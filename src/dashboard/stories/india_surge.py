"""
Story 2 — India's Rising Share.

Stress-tests the claim that India has become the dominant source of migrants
to New Zealand, and that this will increase further.

Charts:
    bump   — Bump chart: top source country rankings by year (2010–present)
    share  — India's % share of total non-NZ arrivals (12-month rolling)

Data: df_citizenship_direction_*.pkl
    Columns: Month, Count, Direction, Citizenship
"""

from __future__ import annotations

from typing import Dict, TYPE_CHECKING

import pandas as pd
import plotly.graph_objects as go

from src.dashboard.base import BaseStory, FactCheck, PLOTLY_TEMPLATE
from src.dashboard.export import save_all_charts

if TYPE_CHECKING:
    from src.dashboard.data_loader import DataLoader

# ── Country colour map ─────────────────────────────────────────────────────────
# Consistent with streamlit_app_plotly.py colour conventions

_COUNTRY_COLORS: dict[str, str] = {
    "India": "#E74C3C",
    "China, People's Republic of": "#C0392B",
    "United Kingdom": "#2980B9",
    "Philippines": "#8E44AD",
    "South Africa": "#27AE60",
    "Australia": "#F39C12",
    "Fiji": "#16A085",
    "Korea, Republic of": "#2C3E50",
    "Nepal": "#D35400",
    "United States of America": "#1ABC9C",
    "Germany": "#7F8C8D",
    "France": "#2ECC71",
    "Japan": "#9B59B6",
    "Sri Lanka": "#E67E22",
    "Malaysia": "#34495E",
    "Ireland": "#27AE60",
    "Other": "#95A5A6",
}

_EXCLUDE = {
    "New Zealand",
    "TOTAL ALL CITIZENSHIPS",
    "Non-New Zealand",
    "Not elsewhere specified/other",
}

# ── Story class ────────────────────────────────────────────────────────────────


class IndiaSurgeStory(BaseStory):
    """India's rise to the top of NZ's source country rankings."""

    title = "India's Rising Share"
    slug = "india-surge"

    def get_fact_check(self) -> FactCheck:
        return FactCheck(
            claim=(
                "Applications to migrate from India will significantly increase "
                "across the board — including uncapped numbers of students with "
                "the right to work, which will take Kiwi jobs off Kiwis."
            ),
            source="Winston Peters, NZ First Leader, State of the Nation address, March 2026",
            score="mostly_supported",
            evidence=(
                "India has been the #1 source country for NZ arrivals since 2022, "
                "rising from around 5th place a decade ago. India's share of "
                "non-NZ-citizen arrivals has roughly tripled since 2015. The trend "
                "pre-dates Peters' speech and is strongly supported by monthly data."
            ),
            caveats=[
                (
                    "Peters' claim is partly forward-looking; current data confirms "
                    "the historical trend but cannot verify future volumes."
                ),
                (
                    "Whether Indian arrivals 'take Kiwi jobs' requires labour market "
                    "and ANZSCO skill-level data (INZ work visa files) — not yet "
                    "included in this dashboard."
                ),
            ],
        )

    # ── Private transforms ─────────────────────────────────────────────────────

    def _annual_rankings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Annual arrivals by citizenship, ranked within each year."""
        arrivals = df[
            (df["Direction"] == "Arrivals")
            & (~df["Citizenship"].isin(_EXCLUDE))
        ].copy()

        arrivals["Year"] = arrivals["Month"].dt.year
        annual = (
            arrivals.groupby(["Year", "Citizenship"])["Count"]
            .sum()
            .reset_index()
        )

        # Rank: 1 = most arrivals
        annual["Rank"] = annual.groupby("Year")["Count"].rank(
            ascending=False, method="min"
        ).astype(int)
        return annual

    def _india_share(self, df: pd.DataFrame) -> pd.Series:
        """India's rolling 12-month share of non-NZ arrivals."""
        non_nz = df[
            (df["Direction"] == "Arrivals")
            & (~df["Citizenship"].isin(_EXCLUDE))
        ]
        india = (
            non_nz[non_nz["Citizenship"] == "India"]
            .set_index("Month")["Count"]
            .sort_index()
        )
        total = (
            non_nz.groupby("Month")["Count"]
            .sum()
            .sort_index()
        )
        share = (india / total * 100).rolling(12, min_periods=12).mean()
        return share.dropna()

    # ── Figure builders ────────────────────────────────────────────────────────

    def _build_bump(self, df: pd.DataFrame) -> go.Figure:
        """Bump chart: top 10 source country rankings 2010–present."""
        annual = self._annual_rankings(df)

        # Top 10 countries by total arrivals across all years
        top_countries = (
            annual.groupby("Citizenship")["Count"]
            .sum()
            .nlargest(10)
            .index.tolist()
        )

        # Filter to 2010+ for readability
        plot_data = annual[
            (annual["Citizenship"].isin(top_countries))
            & (annual["Year"] >= 2010)
        ]

        # Exclude the current (partial) year
        max_full_year = plot_data["Year"].max()
        plot_data = plot_data[plot_data["Year"] < max_full_year]

        fig = go.Figure()

        for country in top_countries:
            cdata = plot_data[plot_data["Citizenship"] == country].sort_values("Year")
            if cdata.empty:
                continue

            color = _COUNTRY_COLORS.get(country, "#AAAAAA")
            is_india = country == "India"

            # Label only at the last year
            labels = [""] * len(cdata)
            labels[-1] = _short_name(country)

            fig.add_trace(
                go.Scatter(
                    x=cdata["Year"],
                    y=cdata["Rank"],
                    mode="lines+markers+text",
                    name=_short_name(country),
                    text=labels,
                    textposition="middle right",
                    textfont=dict(size=11, color=color),
                    line=dict(
                        color=color,
                        width=3.5 if is_india else 1.5,
                    ),
                    marker=dict(
                        size=8 if is_india else 5,
                        color=color,
                    ),
                    hovertemplate=(
                        f"<b>{_short_name(country)}</b><br>"
                        "%{x}: Rank %{y}<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=(
                    "Source country rankings: arrivals to NZ (non-NZ citizens)<br>"
                    "<sub>Annual total arrivals &mdash; rank 1 = largest source country</sub>"
                ),
                x=0.0,
                font_size=18,
            ),
            yaxis=dict(
                autorange="reversed",
                tickvals=list(range(1, 11)),
                ticktext=[f"#{i}" for i in range(1, 11)],
                gridcolor="#EEEEEE",
                title=None,
            ),
            xaxis=dict(
                showgrid=False,
                tickangle=0,
                dtick=1,
                title=None,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.30,
                xanchor="left",
                x=0,
            ),
            margin=dict(l=20, r=120, t=90, b=80),
            hovermode="closest",
        )
        return fig

    def _build_share(self, df: pd.DataFrame) -> go.Figure:
        """India's % share of non-NZ arrivals (12-month rolling average)."""
        share = self._india_share(df)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=share.index,
                y=share.values,
                mode="lines",
                line=dict(color=_COUNTRY_COLORS["India"], width=2.5),
                hovertemplate="%{x|%b %Y}: %{y:.1f}%<extra></extra>",
                name="India share",
            )
        )

        # AEWV reform vertical line + annotation (using shapes avoids Plotly 5.18 bug)
        y_max = float(share.max())
        fig.update_layout(
            shapes=[
                dict(
                    type="line",
                    x0="2024-04-01", x1="2024-04-01",
                    y0=0, y1=y_max,
                    line=dict(color="#888", width=1.5, dash="dot"),
                )
            ],
            annotations=[
                dict(
                    x="2024-04-01",
                    y=y_max * 0.95,
                    text="AEWV reforms",
                    showarrow=False,
                    font=dict(size=11, color="#555"),
                    xanchor="left",
                    xshift=6,
                )
            ],
        )

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=(
                    "India's share of non-NZ-citizen arrivals to NZ<br>"
                    "<sub>Rolling 12-month average &mdash; % of total non-NZ arrivals</sub>"
                ),
                x=0.0,
                font_size=18,
            ),
            xaxis=dict(tickangle=0, showgrid=False, tickformat="%Y"),
            yaxis=dict(
                gridcolor="#EEEEEE",
                ticksuffix="%",
                rangemode="tozero",
            ),
            showlegend=False,
            margin=dict(l=20, r=20, t=90, b=60),
            hovermode="x unified",
        )
        return fig

    # ── Public interface ───────────────────────────────────────────────────────

    def build_figures(self) -> Dict[str, go.Figure]:
        df = self.loader.load_citizenship_direction()
        return {
            "bump": self._build_bump(df),
            "share": self._build_share(df),
        }

    def run(self) -> None:
        print(f"\n[{self.title}]")
        figs = self.build_figures()
        save_all_charts(self.slug, figs, self.output_dir)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _short_name(country: str) -> str:
    """Shorten verbose country names for chart labels."""
    mapping = {
        "China, People's Republic of": "China",
        "United Kingdom": "UK",
        "United States of America": "USA",
        "Korea, Republic of": "Korea",
        "Hong Kong (Special Administrative Region)": "Hong Kong",
    }
    return mapping.get(country, country)
