"""
Story 4 — Where They Land.

NZ choropleth showing net international migration by Territorial Authority,
scaled by TA population (net per 1,000 residents).

Charts:
    map          — Choropleth: total net international migration per 1k population by TA
    top_inflow   — Bar chart: 5 TAs with highest per-capita net inflow
    top_outflow  — Bar chart: 5 TAs with lowest per-capita net migration (outflow or near-zero)

Data: data/raw/subnational_pop_2018_2025.csv
    Stats NZ subnational population components (year ended 30 June 2018-2025)
    Net international migration: sum of annual flows for years ended June 2023, 2024, 2025
    Population denominator: Stats NZ 2025 provisional estimate
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go

from src.dashboard.base import BaseStory, FactCheck, PLOTLY_TEMPLATE
from src.dashboard.export import save_all_charts

# ── Constants ──────────────────────────────────────────────────────────────────

_GEOJSON_PATH = Path(__file__).parent.parent.parent.parent / "dashboard" / "assets" / "nz_ta.geojson"
_RAW_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw"

_SUBNATIONAL_CSV = "subnational_pop_2018_2025.csv"
_NET_YEARS = [2023, 2024, 2025]

_DIVERGING_SCALE = [
    [0.0,  "#922B21"],
    [0.35, "#F5B7B1"],
    [0.5,  "#FFFFFF"],
    [0.65, "#7CCBA2"],
    [1.0,  "#045275"],
]

# ── Helpers ────────────────────────────────────────────────────────────────────


def _norm_ta(name: str) -> str:
    """Normalize a TA name to ASCII title-case for cross-source matching."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = s.title()
    # .title() capitalises after apostrophes: "Hawke'S" → "Hawke's"
    s = re.sub(r"'([A-Z])", lambda m: "'" + m.group(1).lower(), s)
    # .title() capitalises prepositions: "Of" → "of"
    s = re.sub(r"\bOf\b", "of", s)
    return s.strip()


# ── Story class ────────────────────────────────────────────────────────────────


class RegionalMapStory(BaseStory):
    """TA choropleth: net international migration per 1,000 population."""

    title = "Where They Land"
    slug = "where-they-land"

    def get_fact_check(self) -> FactCheck:
        return FactCheck(
            claim=(
                "Net migration of around 140,000 is putting completely "
                "unsustainable pressure on key services and infrastructure."
            ),
            source=(
                "Erica Stanford, Minister of Immigration, "
                "Beehive press release, April 2024"
            ),
            score="partly_supported",
            evidence=(
                "Net international migration is highly concentrated geographically — "
                "Auckland and Hamilton dominate inflows in absolute terms, but per-capita "
                "rates reveal significant variation. Queenstown-Lakes shows the highest "
                "per-capita inflow (~71 per 1,000), while a small number of TAs recorded "
                "net outflows over the three years ended June 2025. 'Unsustainable pressure' "
                "requires housing and infrastructure capacity data not included here."
            ),
            caveats=[
                (
                    "Migration figures are Stats NZ official subnational population estimates "
                    "(components-of-change method), not the monthly 12/16-month migration rule counts."
                ),
                (
                    "Regional data covers intended usual residence — actual settlement "
                    "patterns may differ from initial destination."
                ),
                (
                    "Population denominator is the 2025 provisional estimate, applied uniformly "
                    "across the full three-year window."
                ),
            ],
        )

    # ── Data loading ───────────────────────────────────────────────────────────

    @staticmethod
    def _load_subnational() -> Tuple[Dict[str, float], Dict[str, float]]:
        """Load net international migration (sum 2023-2025) and 2025 population by TA.

        Returns (net_by_ta, pop_by_ta) — both keyed by _norm_ta(area_name).
        """
        csv_path = _RAW_DIR / _SUBNATIONAL_CSV
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Expected {csv_path} — download from "
                "stats.govt.nz/information-releases/subnational-population-estimates-at-30-june-2025/"
            )

        df = pd.read_csv(csv_path)

        _exclude_areas = {
            "Total New Zealand by territorial authority",
            "Area outside territorial authority",
        }
        df_ta = df[
            ~df["Area"].str.contains("local board", case=False, na=False)
            & ~df["Area"].isin(_exclude_areas)
        ]

        net_series = (
            df_ta[
                (df_ta["Measure"] == "Net international migration")
                & (df_ta["Year"].isin(_NET_YEARS))
            ]
            .groupby("Area")["OBS_VALUE"]
            .sum()
        )

        pop_series = (
            df_ta[
                (df_ta["Measure"] == "Population")
                & (df_ta["Year"] == 2025)
            ]
            .set_index("Area")["OBS_VALUE"]
        )

        net_by_ta = {_norm_ta(k): float(v) for k, v in net_series.items()}
        pop_by_ta = {_norm_ta(k): float(v) for k, v in pop_series.items()}

        return net_by_ta, pop_by_ta

    @staticmethod
    def _build_ta_df(
        net_by_ta: Dict[str, float], pop_by_ta: Dict[str, float]
    ) -> pd.DataFrame:
        """Merge net migration and population into a per-TA DataFrame with per-1k rate."""
        records = []
        for norm_name, net in net_by_ta.items():
            pop = pop_by_ta.get(norm_name)
            if pop is None or pop == 0:
                print(f"  [regional-map] No population for {norm_name!r} — skipped")
                continue
            records.append({"ta_name": norm_name, "net": net, "population": pop})
        df = pd.DataFrame(records)
        df["value_per1k"] = df["net"] / df["population"] * 1000
        return df

    @staticmethod
    def _load_geojson() -> Optional[dict]:
        if not _GEOJSON_PATH.exists():
            return None
        with open(_GEOJSON_PATH, encoding="utf-8") as f:
            return json.load(f)

    # ── Figure builders ────────────────────────────────────────────────────────

    def _build_map(self, ta_df: pd.DataFrame) -> go.Figure:
        """Choropleth: net international migration per 1k population by TA."""
        geojson = self._load_geojson()
        fig = go.Figure()

        if geojson is None:
            print("  [regional-map] GeoJSON not found — using bar chart fallback.")
            ta_sorted = ta_df.sort_values("value_per1k", ascending=True)
            fig.add_trace(
                go.Bar(
                    x=ta_sorted["value_per1k"],
                    y=ta_sorted["ta_name"],
                    orientation="h",
                    marker_color="#046C9A",
                    hovertemplate="%{y}: %{x:.1f} per 1k pop<extra></extra>",
                )
            )
            fig.update_layout(
                height=900,
                title=dict(
                    text=(
                        "Net international migration per 1k population by TA<br>"
                        "<sub>Cumulative change June 2022–June 2025 — GeoJSON pending for map view</sub>"
                    ),
                    x=0.0,
                    font_size=18,
                ),
                xaxis=dict(title=None, showgrid=True, gridcolor="#EEEEEE", tickformat=".1f"),
                yaxis=dict(title=None, tickfont=dict(size=10)),
                margin=dict(l=160, r=20, t=90, b=40),
            )
            return fig

        fig.add_trace(
            go.Choropleth(
                geojson=geojson,
                featureidkey="properties.ta_name_ascii",
                locations=ta_df["ta_name"],
                z=ta_df["value_per1k"],
                customdata=ta_df["net"],
                colorscale=_DIVERGING_SCALE,
                zmid=0,
                colorbar=dict(
                    title="Net<br>per 1k<br>pop",
                    tickformat=".1f",
                    nticks=8,
                    len=0.6,
                ),
                hovertemplate=(
                    "<b>%{location}</b><br>"
                    "Net / 1k pop: %{z:.1f}<br>"
                    "Net absolute: %{customdata:,.0f}"
                    "<extra></extra>"
                ),
                marker_line_color="#BBBBBB",
                marker_line_width=0.5,
            )
        )

        fig.update_geos(visible=False, fitbounds="locations")
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=(
                    "Net international migration per 1,000 population by TA<br>"
                    "<sub>Cumulative change June 2022–June 2025  |  Teal = net inflow  |  Red = net outflow</sub>"
                ),
                x=0.0,
                font_size=18,
            ),
            geo=dict(showframe=False, showcoastlines=False, projection_type="mercator"),
            margin=dict(l=0, r=0, t=90, b=20),
            height=650,
        )
        return fig

    @staticmethod
    def _load_albs() -> pd.DataFrame:
        """Load Auckland local board area net migration and population from subnational CSV."""
        csv_path = _RAW_DIR / _SUBNATIONAL_CSV
        df = pd.read_csv(csv_path)
        alb_df = df[df["Area"].str.contains("local board area", case=False, na=False)]

        net = (
            alb_df[
                (alb_df["Measure"] == "Net international migration")
                & (alb_df["Year"].isin(_NET_YEARS))
            ]
            .groupby("Area")["OBS_VALUE"]
            .sum()
            .rename("net")
        )
        pop = (
            alb_df[
                (alb_df["Measure"] == "Population")
                & (alb_df["Year"] == 2025)
            ]
            .set_index("Area")["OBS_VALUE"]
            .rename("population")
        )
        merged = pd.concat([net, pop], axis=1).dropna().reset_index()
        merged.rename(columns={"Area": "area_name"}, inplace=True)
        merged["value_per1k"] = merged["net"] / merged["population"] * 1000
        merged["display_name"] = merged["area_name"].str.replace(
            r"\s+local board area$", "", regex=True, case=False
        )
        return merged[["display_name", "net", "population", "value_per1k"]]

    def _build_top_inflow(self, ta_df: pd.DataFrame) -> go.Figure:
        """Bar chart: 5 TAs with highest per-capita net international migration inflow."""
        top5 = (
            ta_df.sort_values("value_per1k", ascending=False)
            .head(5)
            .sort_values("value_per1k", ascending=True)
        )
        abs_labels = [f"+{v:,.0f}" if v >= 0 else f"{v:,.0f}" for v in top5["net"]]
        max_val = top5["value_per1k"].max()

        fig = go.Figure(
            go.Bar(
                x=top5["value_per1k"],
                y=top5["ta_name"],
                orientation="h",
                marker_color="#045275",
                text=abs_labels,
                textposition="outside",
                textfont=dict(size=10, color="#555555"),
                hovertemplate="%{y}: %{x:.1f} per 1k pop<extra></extra>",
            )
        )
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=(
                    "Highest net international migration per 1,000 population — top 5 TAs<br>"
                    "<sub>Cumulative change June 2022–June 2025  |  Numbers show absolute net count</sub>"
                ),
                x=0.0,
                font_size=18,
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor="#EEEEEE",
                tickformat=".1f",
                title=None,
                range=[0, max_val * 1.4],
            ),
            yaxis=dict(title=None, tickfont=dict(size=11)),
            margin=dict(l=180, r=20, t=90, b=40),
            showlegend=False,
            height=350,
        )
        return fig

    def _build_auckland_albs(self, alb_df: pd.DataFrame) -> go.Figure:
        """Bar chart: top 5 Auckland local board areas by per-capita net international migration."""
        top5 = (
            alb_df.sort_values("value_per1k", ascending=False)
            .head(5)
            .sort_values("value_per1k", ascending=True)
        )
        abs_labels = [f"+{v:,.0f}" for v in top5["net"]]
        max_val = top5["value_per1k"].max()

        fig = go.Figure(
            go.Bar(
                x=top5["value_per1k"],
                y=top5["display_name"],
                orientation="h",
                marker_color="#045275",
                text=abs_labels,
                textposition="outside",
                textfont=dict(size=10, color="#555555"),
                hovertemplate="%{y}: %{x:.1f} per 1k pop<extra></extra>",
            )
        )
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=(
                    "Auckland local board areas — net international migration per 1,000 population<br>"
                    "<sub>Cumulative change June 2022–June 2025  |  Numbers show absolute net count</sub>"
                ),
                x=0.0,
                font_size=18,
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor="#EEEEEE",
                tickformat=".1f",
                title=None,
                range=[0, max_val * 1.4],
            ),
            yaxis=dict(title=None, tickfont=dict(size=11)),
            margin=dict(l=200, r=20, t=90, b=40),
            showlegend=False,
            height=350,
        )
        return fig

    # ── Public interface ───────────────────────────────────────────────────────

    def build_figures(self) -> Dict[str, go.Figure]:
        net_by_ta, pop_by_ta = self._load_subnational()
        ta_df = self._build_ta_df(net_by_ta, pop_by_ta)
        alb_df = self._load_albs()
        return {
            "map": self._build_map(ta_df),
            "top_inflow": self._build_top_inflow(ta_df),
            "auckland_albs": self._build_auckland_albs(alb_df),
        }

    def run(self) -> None:
        print(f"\n[{self.title}]")
        figs = self.build_figures()
        save_all_charts(self.slug, figs, self.output_dir)
