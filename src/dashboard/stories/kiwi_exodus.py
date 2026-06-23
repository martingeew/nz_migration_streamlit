"""
Story 1 — The Kiwi Exodus.

Stress-tests the claim that NZ citizens are leaving in historically large
numbers due to domestic economic conditions.

Charts:
    main          — Rolling 12-month net NZ and non-NZ citizen migration
    age_net      — Rolling 12-month net migration by age group (stacked area)

Data:
    df_citizenship_direction_*.pkl  — Columns: Month, Count, Direction, Citizenship
    df_direction_age_sex_*.pkl      — Columns: Month, Count, Direction, Age Group, Sex
"""

from __future__ import annotations

from typing import Dict, TYPE_CHECKING

import pandas as pd
import plotly.graph_objects as go

from src.dashboard.base import BaseStory, FactCheck, PLOTLY_TEMPLATE, PALETTE, BORDER_SHAPES, BORDER_ANNOTATIONS
from src.dashboard.export import save_all_charts

if TYPE_CHECKING:
    from src.dashboard.data_loader import DataLoader

# ── Colour constants ───────────────────────────────────────────────────────────

_BLUE = "#045275"
_RED = "#C0392B"
_GREY = "#AAAAAA"
_BAND_FILL = "rgba(4, 82, 117, 0.10)"

# Age group bins and palette (youngest = lightest, oldest = darkest)
_AGE_BINS: dict[str, list[str]] = {
    "Under 20": ["Under 15 Years", "15-19 Years"],
    "20s": ["20-24 Years", "25-29 Years"],
    "30s": ["30-34 Years", "35-39 Years"],
    "40s": ["40-44 Years", "45-49 Years"],
    "50s–64": ["50-54 Years", "55-59 Years", "60-64 Years"],
    "65+": ["65 Years and Over"],
}
_AGE_COLOURS = ["#B7E6A5", "#7CCBA2", "#46AEA0", "#089099", "#00718B", "#045275"]

# ── Story class ────────────────────────────────────────────────────────────────


class KiwiExodusStory(BaseStory):
    """Rolling net NZ citizen migration with historical context."""

    title = "The Kiwi Exodus"
    slug = "kiwi-exodus"

    def get_fact_check(self) -> FactCheck:
        return FactCheck(
            claim=(
                "The economy in recession could see the best and brightest "
                "leave New Zealand."
            ),
            source="Louise Upston, Minister for Social Development, 2024",
            score="mostly_supported",
            evidence=(
                "Net NZ citizen migration turned sharply negative after 2022 "
                "and reached multi-decade highs in 2023–24. The 12-month "
                "departure surplus consistently exceeds the pre-COVID average. "
                "Australia absorbs the majority of departing NZ citizens."
            ),
            caveats=[
                (
                    "Whether this is 'unprecedented' depends on the time frame. "
                    "Similar peaks occurred in the late 1970s and early 2000s "
                    "(Gluckman et al., 2025) — compare with the baseline "
                    "band on the chart."
                ),
                (
                    "Data shows total NZ citizen flows, not skill-level breakdown. "
                    "A separate Stats NZ cross-tabulation (not yet downloaded) "
                    "is required to isolate the working-age cohort specifically."
                ),
            ],
        )

    # ── Private transforms ─────────────────────────────────────────────────────

    def _get_nz_net(self, df: pd.DataFrame) -> pd.Series:
        """Rolling 12-month net NZ citizen migration."""
        arr = (
            df[(df["Citizenship"] == "New Zealand") & (df["Direction"] == "Arrivals")]
            .set_index("Month")["Count"]
        )
        dep = (
            df[(df["Citizenship"] == "New Zealand") & (df["Direction"] == "Departures")]
            .set_index("Month")["Count"]
        )
        net = (arr - dep).sort_index()
        return net.rolling(12, min_periods=12).sum()

    def _get_non_nz_net(self, df: pd.DataFrame) -> pd.Series:
        """Rolling 12-month net non-NZ citizen migration (includes Australians)."""
        arr = (
            df[(df["Citizenship"] == "Non-New Zealand") & (df["Direction"] == "Arrivals")]
            .set_index("Month")["Count"]
        )
        dep = (
            df[(df["Citizenship"] == "Non-New Zealand") & (df["Direction"] == "Departures")]
            .set_index("Month")["Count"]
        )
        net = (arr - dep).sort_index()
        return net.rolling(12, min_periods=12).sum()

    def _monthly_age_net(self, df_age: pd.DataFrame) -> pd.DataFrame:
        """Monthly net migration (arrivals minus departures) by binned age group."""
        age_map: dict[str, str] = {
            age: bin_name
            for bin_name, raw_ages in _AGE_BINS.items()
            for age in raw_ages
        }
        sex_total = df_age["Sex"].str.lower().str.contains("total")
        d = df_age[sex_total & (df_age["Age Group"] != "Total All Ages")].copy()
        d["Age Bin"] = d["Age Group"].map(age_map)
        d = d.dropna(subset=["Age Bin"])

        arr = d[d["Direction"] == "Arrivals"].groupby(["Month", "Age Bin"])["Count"].sum()
        dep = d[d["Direction"] == "Departures"].groupby(["Month", "Age Bin"])["Count"].sum()
        return (arr - dep).rename("Net").reset_index()

    # ── Figure builders ────────────────────────────────────────────────────────

    def _build_main(self, df: pd.DataFrame) -> go.Figure:
        """Rolling 12-month net NZ and non-NZ citizen migration."""
        net_nz = self._get_nz_net(df).dropna()
        net_non_nz = self._get_non_nz_net(df).dropna()

        # Historical means (2001–2019)
        mean_val = net_nz["2001":"2019"].mean()
        mean_non_nz_val = net_non_nz["2001":"2019"].mean()

        # Show data from 2005 onwards
        net_nz_plot = net_nz["2005":]
        net_non_nz_plot = net_non_nz["2005":]

        fig = go.Figure()

        # Border closure shaded area (Mar 2020 – Aug 2022)
        fig.add_vrect(
            x0="2020-03-01",
            x1="2022-08-01",
            fillcolor="rgba(200, 200, 200, 0.25)",
            line_width=0,
            annotation_text="Border closed",
            annotation_position="top left",
            annotation=dict(font_size=10, font_color=_GREY, showarrow=False),
        )

        # Historical mean line (NZ citizens)
        fig.add_trace(
            go.Scatter(
                x=net_nz_plot.index,
                y=[mean_val] * len(net_nz_plot),
                mode="lines",
                line=dict(color=_GREY, dash="dot", width=1.5),
                name=f"NZ mean: {mean_val:,.0f}",
                hoverinfo="skip",
            )
        )

        # Historical mean line (non-NZ citizens)
        fig.add_trace(
            go.Scatter(
                x=net_non_nz_plot.index,
                y=[mean_non_nz_val] * len(net_non_nz_plot),
                mode="lines",
                line=dict(color=_RED, dash="dot", width=1.5),
                name=f"Non-NZ mean: {mean_non_nz_val:,.0f}",
                hoverinfo="skip",
            )
        )

        # Non-NZ citizen net line (includes Australians)
        fig.add_trace(
            go.Scatter(
                x=net_non_nz_plot.index,
                y=net_non_nz_plot.values,
                mode="lines",
                line=dict(color=_RED, width=2.5),
                name="Non-NZ migration (incl. AU)",
                hovertemplate="%{x|%b %Y}: %{y:,.0f}<extra></extra>",
            )
        )

        # NZ citizen net line
        fig.add_trace(
            go.Scatter(
                x=net_nz_plot.index,
                y=net_nz_plot.values,
                mode="lines",
                line=dict(color=_BLUE, width=2.5),
                name="Net NZ citizen migration",
                hovertemplate="%{x|%b %Y}: %{y:,.0f}<extra></extra>",
            )
        )

        y_max = int(max(net_non_nz_plot.max(), mean_non_nz_val) * 1.08)

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text="Net NZ and non-NZ citizen migration",
                x=0.0,
                font_size=14,
            ),
            xaxis=dict(tickangle=0, showgrid=False, tickformat="%Y"),
            yaxis=dict(
                gridcolor="#EEEEEE",
                tickformat=",",
                zeroline=True,
                zerolinecolor="#999",
                zerolinewidth=1,
                range=[-100000, y_max],
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="left",
                x=0,
            ),
            margin=dict(l=20, r=20, t=60, b=160),
            hovermode="x unified",
        )
        return fig

    def _build_age_net(self, df_age: pd.DataFrame) -> go.Figure:
        """Stacked area of rolling 12-month net migration by age group."""
        monthly = self._monthly_age_net(df_age)

        # Pre-compute all rolling series so we can derive row totals for % share
        rolling: dict[str, pd.Series] = {}
        for bin_name in _AGE_BINS:
            rolling[bin_name] = (
                monthly[monthly["Age Bin"] == bin_name]
                .set_index("Month")["Net"]
                .sort_index()
                .rolling(12, min_periods=12)
                .sum()
                .dropna()
                .loc["2005":]
            )

        row_totals = (
            pd.DataFrame(rolling).fillna(0).sum(axis=1).replace(0, float("nan"))
        )

        fig = go.Figure()
        for bin_name, colour in zip(_AGE_BINS, _AGE_COLOURS):
            s = rolling[bin_name]
            pct = (s / row_totals.reindex(s.index) * 100).fillna(0).values
            fig.add_trace(
                go.Scatter(
                    x=s.index,
                    y=s.values,
                    customdata=pct,
                    mode="lines",
                    name=bin_name,
                    stackgroup="one",
                    line=dict(width=0.5, color=colour),
                    fillcolor=colour,
                    hovertemplate=f"{bin_name}: %{{y:,.0f}} (%{{customdata:.1f}}%)<extra></extra>",
                )
            )

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text="Net migration by age group",
                x=0.0,
                font_size=14,
            ),
            xaxis=dict(tickangle=0, showgrid=False, tickformat="%Y"),
            yaxis=dict(gridcolor="#EEEEEE", tickformat=","),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.12,
                xanchor="left",
                x=0,
                traceorder="normal",
            ),
            shapes=list(BORDER_SHAPES),
            annotations=list(BORDER_ANNOTATIONS),
            margin=dict(l=20, r=20, t=60, b=140),
            hovermode="x unified",
        )
        return fig

    # ── Public interface ───────────────────────────────────────────────────────

    def build_figures(self) -> Dict[str, go.Figure]:
        df = self.loader.load_citizenship_direction()
        df_age = self.loader.load_direction_age_sex()
        return {
            "main": self._build_main(df),
            "age_net": self._build_age_net(df_age),
        }

    def run(self) -> None:
        """Build and export all figures for this story."""
        print(f"\n[{self.title}]")
        figs = self.build_figures()
        save_all_charts(self.slug, figs, self.output_dir)
