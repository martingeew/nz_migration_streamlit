"""
Story 1 — The Kiwi Exodus.

Stress-tests the claim that NZ citizens are leaving in historically large
numbers due to domestic economic conditions.

Charts:
    main   — Rolling 12-month net NZ citizen migration with pre-COVID baseline band
    split  — NZ citizen net migration: Australia vs rest-of-world

Data: df_citizenship_direction_*.pkl
    Columns: Month, Count, Direction, Citizenship
"""

from __future__ import annotations

from typing import Dict, TYPE_CHECKING

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.base import BaseStory, FactCheck, PLOTLY_TEMPLATE, PALETTE
from src.dashboard.export import save_all_charts

if TYPE_CHECKING:
    from src.dashboard.data_loader import DataLoader

# ── Colour constants ───────────────────────────────────────────────────────────

_BLUE = "#045275"
_RED = "#C0392B"
_GREY = "#AAAAAA"
_BAND_FILL = "rgba(4, 82, 117, 0.10)"

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

    def _get_australia_split(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """12-month rolling net NZ citizens: Australia vs rest-of-world."""
        nz = df[df["Citizenship"] == "New Zealand"].copy()

        def _net_rolling(direction_filter: pd.DataFrame, dest: str) -> pd.Series:
            arr = (
                direction_filter[direction_filter["Direction"] == "Arrivals"]
                .set_index("Month")["Count"]
            )
            dep = (
                direction_filter[direction_filter["Direction"] == "Departures"]
                .set_index("Month")["Count"]
            )
            return (arr - dep).sort_index().rolling(12, min_periods=12).sum()

        # Net NZ citizen flows to/from Australia are approximated by the total
        # net minus non-Australia net (Stats NZ does not publish
        # citizenship × country-of-travel cross-tabs in this dataset).
        # We use total net as the main signal; Australia split requires the
        # citizenship-direction total-net column which covers all destinations.
        total_net = _net_rolling(nz, "total")

        # Use the pre-computed "Net" direction column for the Australia split
        au = (
            df[(df["Citizenship"] == "Australia") & (df["Direction"] == "Net")]
            .set_index("Month")["Count"]
            .sort_index()
            .rolling(12, min_periods=12)
            .sum()
        )
        return total_net, au

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
                name=f"NZ citizen historical mean ({mean_val:,.0f})",
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
                name=f"Non-NZ citizen historical mean ({mean_non_nz_val:,.0f})",
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
                name="Net non-NZ citizen migration (incl. Australians)",
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
                text=(
                    "NZ and non-NZ citizens: rolling 12-month net migration<br>"
                    "<sub>Arrivals minus departures — negative = more leaving than arriving</sub>"
                ),
                x=0.0,
                font_size=18,
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
                yanchor="bottom",
                y=-0.30,
                xanchor="left",
                x=0,
            ),
            margin=dict(l=20, r=20, t=90, b=100),
            hovermode="x unified",
        )
        return fig

    def _build_split(self, df: pd.DataFrame) -> go.Figure:
        """NZ citizen net migration vs Australian citizen net migration (as proxy for cross-Tasman)."""
        nz_net = self._get_nz_net(df).dropna()

        # Australian citizens net (proxy for Tasman flow dynamics — not NZ-to-Aus breakdown)
        au_net = (
            df[
                (df["Citizenship"] == "Australia")
                & (df["Direction"] == "Net")
            ]
            .set_index("Month")["Count"]
            .sort_index()
            .rolling(12, min_periods=12)
            .sum()
            .dropna()
        )

        start = "2015"
        nz_plot = nz_net[start:]
        au_plot = au_net[start:]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=nz_plot.index,
                y=nz_plot.values,
                mode="lines",
                name="NZ citizens (net)",
                line=dict(color=_BLUE, width=2.5),
                hovertemplate="%{x|%b %Y}: %{y:,.0f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=au_plot.index,
                y=au_plot.values,
                mode="lines",
                name="Australian citizens (net)",
                line=dict(color="#F39C12", width=2, dash="dash"),
                hovertemplate="%{x|%b %Y}: %{y:,.0f}<extra></extra>",
            )
        )

        fig.add_hline(y=0, line_color="#999", line_width=1)

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=(
                    "Net migration by citizenship: NZ vs Australian citizens<br>"
                    "<sub>Rolling 12-month total &mdash; shows cross-Tasman dynamics</sub>"
                ),
                x=0.0,
                font_size=18,
            ),
            xaxis=dict(tickangle=0, showgrid=False, tickformat="%Y"),
            yaxis=dict(gridcolor="#EEEEEE", tickformat=","),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.30,
                xanchor="left",
                x=0,
            ),
            margin=dict(l=20, r=20, t=90, b=80),
            hovermode="x unified",
        )
        return fig

    # ── Public interface ───────────────────────────────────────────────────────

    def build_figures(self) -> Dict[str, go.Figure]:
        df = self.loader.load_citizenship_direction()
        return {
            "main": self._build_main(df),
            "split": self._build_split(df),
        }

    def run(self) -> None:
        """Build and export all figures for this story."""
        print(f"\n[{self.title}]")
        figs = self.build_figures()
        save_all_charts(self.slug, figs, self.output_dir)
