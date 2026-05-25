"""
Story 4 — Where They Land.

NZ choropleth showing net migration by Territorial Authority, using
GeoJSON boundaries from datafinder.stats.govt.nz.

Charts:
    map    — Choropleth: cumulative net migration by TA (2022–present)
    trend  — Bar chart: top and bottom 10 TAs by net migration (latest 12 months)

Data: df_direction_region_*.pkl
    Columns: Month, Count, Direction, Region
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, TYPE_CHECKING

import json
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.base import BaseStory, FactCheck, PLOTLY_TEMPLATE
from src.dashboard.export import save_all_charts

if TYPE_CHECKING:
    from src.dashboard.data_loader import DataLoader

# ── Constants ──────────────────────────────────────────────────────────────────

# Territorial Authority suffixes to strip for GeoJSON name matching
_TA_KEYWORDS = ["District", "City", "Territory", "Region"]

# GeoJSON path (downloaded from datafinder.stats.govt.nz)
_GEOJSON_PATH = Path(__file__).parent.parent.parent.parent / "dashboard" / "assets" / "nz_ta.geojson"

# TA rows in the data (exclude Regions, Local Boards, and special rows)
_EXCLUDE_REGIONS = {
    "Auckland Region", "Bay of Plenty Region", "Canterbury Region",
    "Gisborne Region", "Hawke's Bay Region", "Manawatu-Wanganui Region",
    "Marlborough Region", "Nelson Region", "Northland Region", "Otago Region",
    "Southland Region", "Taranaki Region", "Tasman Region", "Waikato Region",
    "Wellington Region", "West Coast Region",
    "TOTAL ALL AREAS", "Area Outside Region", "Area Outside Territorial Authority",
    "999 Not applicable/not stated",
}
_LOCAL_BOARD_SUFFIX = "local board area"

# ── Story class ────────────────────────────────────────────────────────────────


class RegionalMapStory(BaseStory):
    """Territorial authority choropleth of net migration."""

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
                "Net migration is highly concentrated — Auckland alone accounts "
                "for the majority of positive net inflows. Several provincial "
                "Territorial Authorities show net outflows. "
                "The map confirms geographic concentration, but 'unsustainable "
                "pressure' requires housing and infrastructure capacity data "
                "not included here."
            ),
            caveats=[
                (
                    "Stats NZ regional migration is based on the 12/16-month rule "
                    "(intended migrants), not short-stay visitors."
                ),
                (
                    "Regional data covers intended last/next usual residence — "
                    "actual settlement patterns may differ from declared destination."
                ),
                (
                    "Building consent and rental data (Issue 2 in the full plan) "
                    "is needed to quantify 'pressure on services'."
                ),
            ],
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _is_ta(region: str) -> bool:
        """Return True if this region row represents a Territorial Authority."""
        if region in _EXCLUDE_REGIONS:
            return False
        if _LOCAL_BOARD_SUFFIX in region.lower():
            return False
        return True

    def _ta_net(self, df: pd.DataFrame, start: str = "2022-01") -> pd.DataFrame:
        """Cumulative net migration by TA since start date."""
        ta_df = df[
            (df["Direction"] == "Net")
            & (df["Month"] >= start)
            & (df["Region"].apply(self._is_ta))
        ]
        cumulative = (
            ta_df.groupby("Region")["Count"]
            .sum()
            .reset_index()
            .rename(columns={"Region": "ta_name", "Count": "net"})
        )
        return cumulative

    @staticmethod
    def _load_geojson() -> dict | None:
        if not _GEOJSON_PATH.exists():
            return None
        with open(_GEOJSON_PATH, encoding="utf-8") as f:
            return json.load(f)

    # ── Figure builders ────────────────────────────────────────────────────────

    def _build_map(self, df: pd.DataFrame) -> go.Figure:
        """Choropleth map: cumulative net migration by TA (2022+)."""
        ta_net = self._ta_net(df)
        geojson = self._load_geojson()

        fig = go.Figure()

        if geojson is None:
            # Fallback: horizontal bar chart when GeoJSON not available
            print("  [regional-map] GeoJSON not found — using bar chart fallback.")
            ta_sorted = ta_net.sort_values("net", ascending=True)
            fig.add_trace(
                go.Bar(
                    x=ta_sorted["net"],
                    y=ta_sorted["ta_name"],
                    orientation="h",
                    marker=dict(
                        color=ta_sorted["net"],
                        colorscale=[[0, "#C0392B"], [0.5, "#FFFFFF"], [1, "#045275"]],
                        cmid=0,
                        showscale=True,
                    ),
                    hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
                )
            )
            fig.update_layout(
                height=900,
                title=dict(
                    text=(
                        "Net migration by Territorial Authority (2022–present)<br>"
                        "<sub>Cumulative net — GeoJSON pending download for map view</sub>"
                    ),
                    x=0.0,
                    font_size=18,
                ),
                xaxis=dict(title=None, showgrid=True, gridcolor="#EEEEEE"),
                yaxis=dict(title=None, tickfont=dict(size=10)),
                margin=dict(l=160, r=20, t=90, b=40),
            )
            return fig

        # Map the GeoJSON feature name field — inspect the first feature
        # to determine the correct property key
        first_props = geojson["features"][0]["properties"]
        name_key = next(
            (k for k in ["TA2023_V1_00_NAME", "TA2022_V1_00_NAME", "TA_NAME", "name", "NAME"]
             if k in first_props),
            list(first_props.keys())[0],
        )

        fig.add_trace(
            go.Choropleth(
                geojson=geojson,
                featureidkey=f"properties.{name_key}",
                locations=ta_net["ta_name"],
                z=ta_net["net"],
                colorscale=[
                    [0.0, "#C0392B"],
                    [0.45, "#FDFEFE"],
                    [0.5, "#FDFEFE"],
                    [0.55, "#FDFEFE"],
                    [1.0, "#045275"],
                ],
                zmid=0,
                colorbar=dict(
                    title="Net migration",
                    tickformat=",",
                    len=0.6,
                ),
                hovertemplate="<b>%{location}</b><br>Net: %{z:,.0f}<extra></extra>",
                marker_line_color="white",
                marker_line_width=0.5,
            )
        )

        fig.update_geos(
            visible=False,
            fitbounds="locations",
        )
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=(
                    "Net migration by Territorial Authority (Jan 2022–present)<br>"
                    "<sub>Cumulative net migration — blue = net inflow, red = net outflow</sub>"
                ),
                x=0.0,
                font_size=18,
            ),
            geo=dict(
                showframe=False,
                showcoastlines=False,
                projection_type="mercator",
            ),
            margin=dict(l=0, r=0, t=90, b=0),
            height=650,
        )
        return fig

    def _build_top_bottom(self, df: pd.DataFrame) -> go.Figure:
        """Bar chart: top 10 and bottom 10 TAs by net migration (last 12 months)."""
        latest_month = df["Month"].max()
        start = latest_month - pd.DateOffset(months=12)

        ta_net = self._ta_net(df, start=str(start.date()))
        ta_sorted = ta_net.sort_values("net", ascending=False)

        top10 = ta_sorted.head(10)
        bottom10 = ta_sorted.tail(10)
        combined = pd.concat([top10, bottom10]).sort_values("net", ascending=True)

        colors = ["#C0392B" if v < 0 else "#045275" for v in combined["net"]]

        fig = go.Figure(
            go.Bar(
                x=combined["net"],
                y=combined["ta_name"],
                orientation="h",
                marker_color=colors,
                hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
            )
        )
        fig.add_vline(x=0, line_color="#999", line_width=1)
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=(
                    "Top and bottom 10 TAs: net migration (last 12 months)<br>"
                    "<sub>Blue = net inflow, red = net outflow</sub>"
                ),
                x=0.0,
                font_size=18,
            ),
            xaxis=dict(showgrid=True, gridcolor="#EEEEEE", tickformat=",", title=None),
            yaxis=dict(title=None, tickfont=dict(size=11)),
            margin=dict(l=160, r=20, t=90, b=40),
            showlegend=False,
            height=500,
        )
        return fig

    # ── Public interface ───────────────────────────────────────────────────────

    def build_figures(self) -> Dict[str, go.Figure]:
        df = self.loader.load_direction_region()
        return {
            "map": self._build_map(df),
            "top_bottom": self._build_top_bottom(df),
        }

    def run(self) -> None:
        print(f"\n[{self.title}]")
        figs = self.build_figures()
        save_all_charts(self.slug, figs, self.output_dir)
