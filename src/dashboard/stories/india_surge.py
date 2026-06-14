"""
Story 2 — India's Rising Share.

Stress-tests the claim that India has become the dominant source of migrants
to New Zealand, and that this will increase further.

Charts:
    share  — Rolling 12-month share of non-NZ arrivals for top 5 source countries

Data: df_citizenship_direction_*.pkl
    Columns: Month, Count, Direction, Citizenship
"""

from __future__ import annotations

from typing import Dict, TYPE_CHECKING

import pandas as pd
import plotly.graph_objects as go

from src.dashboard.base import BaseStory, FactCheck, PLOTLY_TEMPLATE, BORDER_SHAPES, BORDER_ANNOTATIONS
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

_EXCLUDE_REGIONS = {
    "Asia",
    "Europe",
    "Oceania and Antarctica",
    "North-East Asia",
    "South-East Asia",
    "Southern and Central Asia",
    "North-West Europe",
    "Southern and Eastern Europe",
    "The Americas",
    "Africa and the Middle East",
    "North Africa and the Middle East",
    "Sub-Saharan Africa",
}

# Countries shown in the stacked net-migration area chart
_NET_AREA_COUNTRIES = [
    "China, People's Republic of",
    "India",
    "Philippines",
    "Sri Lanka",
    "United Kingdom",
    "Fiji",
]

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

    def _top_countries_share(self, df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
        """Rolling 12-month share of non-NZ arrivals for the top N countries."""
        non_nz = df[
            (df["Direction"] == "Arrivals")
            & (~df["Citizenship"].isin(_EXCLUDE | _EXCLUDE_REGIONS))
        ]
        total = non_nz.groupby("Month")["Count"].sum().sort_index()

        # Identify top N by arrivals in the most recent 12 months of data
        max_month = non_nz["Month"].max()
        cutoff = max_month - pd.DateOffset(months=11)
        top_n = (
            non_nz[non_nz["Month"] >= cutoff]
            .groupby("Citizenship")["Count"]
            .sum()
            .nlargest(n)
            .index.tolist()
        )

        shares: dict = {}
        for country in top_n:
            monthly = (
                non_nz[non_nz["Citizenship"] == country]
                .set_index("Month")["Count"]
                .sort_index()
                .reindex(total.index, fill_value=0)
            )
            shares[country] = (monthly / total * 100).rolling(12, min_periods=12).mean()

        return pd.DataFrame(shares).dropna(how="all")

    def _net_by_country(self, df: pd.DataFrame, countries: list) -> tuple:
        """Rolling 12-month net migration for named countries + Other.

        Returns (net_rolling DataFrame, countries list) where net_rolling has
        one column per country plus 'Other'.
        """
        filtered = df[~df["Citizenship"].isin(_EXCLUDE | _EXCLUDE_REGIONS)]

        arr = (
            filtered[filtered["Direction"] == "Arrivals"]
            .groupby(["Month", "Citizenship"])["Count"].sum()
            .unstack(fill_value=0)
        )
        dep = (
            filtered[filtered["Direction"] == "Departures"]
            .groupby(["Month", "Citizenship"])["Count"].sum()
            .unstack(fill_value=0)
        )
        all_cols = arr.columns.union(dep.columns)
        net = arr.reindex(columns=all_cols, fill_value=0) - dep.reindex(columns=all_cols, fill_value=0)
        net_rolling = net.rolling(12, min_periods=12).sum().dropna(how="all")

        out = net_rolling[countries].copy()
        out["Other"] = net_rolling.drop(columns=countries).sum(axis=1)
        return out, countries

    # ── Figure builders ────────────────────────────────────────────────────────

    def _build_net_area(self, df: pd.DataFrame) -> go.Figure:
        """Stacked area: rolling 12-month net migration by country (excl NZ)."""
        net, top_n = self._net_by_country(df, _NET_AREA_COUNTRIES)

        _GREY = "rgba(180,180,180,0.5)"
        _GREY_LINE = "#BBBBBB"

        fig = go.Figure()

        row_totals = net.sum(axis=1).replace(0, float("nan"))

        # Stack Other at the bottom (grey), then top-N countries above
        other = net["Other"].dropna()
        pct_other = (net["Other"] / row_totals * 100).reindex(other.index).fillna(0).values
        fig.add_trace(go.Scatter(
            x=other.index, y=other.values,
            customdata=pct_other,
            name="Other",
            stackgroup="one",
            mode="lines",
            line=dict(color=_GREY_LINE, width=0.5),
            fillcolor=_GREY,
            hovertemplate="<b>Other</b><br>%{x|%b %Y}: %{y:,.0f} (%{customdata:.1f}% of non-NZ net)<extra></extra>",
        ))

        for country in reversed(top_n):
            color = _COUNTRY_COLORS.get(country, "#AAAAAA")
            series = net[country].dropna()
            pct = (net[country] / row_totals * 100).reindex(series.index).fillna(0).values
            fig.add_trace(go.Scatter(
                x=series.index, y=series.values,
                customdata=pct,
                name=_short_name(country),
                stackgroup="one",
                mode="lines",
                line=dict(color=color, width=0.5),
                fillcolor=color,
                hovertemplate=(
                    f"<b>{_short_name(country)}</b><br>"
                    "%{x|%b %Y}: %{y:,.0f} (%{customdata:.1f}% of non-NZ net)<extra></extra>"
                ),
            ))

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=(
                    "Net migration to NZ by source country<br>"
                    "<sub>Rolling 12-month sum — non-NZ citizens</sub>"
                ),
                x=0.0,
                font_size=14,
            ),
            xaxis=dict(tickangle=0, showgrid=False, tickformat="%Y"),
            yaxis=dict(
                gridcolor="#EEEEEE",
                tickformat=",.0f",
                rangemode="tozero",
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.12,
                xanchor="left",
                x=0,
            ),
            showlegend=True,
            shapes=list(BORDER_SHAPES),
            annotations=list(BORDER_ANNOTATIONS),
            margin=dict(l=20, r=20, t=90, b=80),
            hovermode="x unified",
        )
        return fig

    def _build_share(self, df: pd.DataFrame, n: int = 5) -> go.Figure:
        """Rolling 12-month share of non-NZ arrivals — top N source countries."""
        shares = self._top_countries_share(df, n=n)

        fig = go.Figure()

        for country in shares.columns:
            series = shares[country].dropna()
            color = _COUNTRY_COLORS.get(country, "#AAAAAA")
            is_india = country == "India"

            fig.add_trace(
                go.Scatter(
                    x=series.index,
                    y=series.values,
                    mode="lines",
                    name=_short_name(country),
                    line=dict(color=color, width=2.5 if is_india else 1.5),
                    hovertemplate=(
                        f"<b>{_short_name(country)}</b><br>"
                        "%{x|%b %Y}: %{y:.1f}%<extra></extra>"
                    ),
                )
            )

            # Direct label at end of line
            fig.add_annotation(
                x=series.index[-1],
                y=float(series.values[-1]),
                text=_short_name(country),
                showarrow=False,
                xanchor="left",
                xshift=8,
                font=dict(size=11, color=color),
            )

        # AEWV reform vertical line
        y_max = float(shares.max().max())
        fig.update_layout(
            shapes=[
                dict(
                    type="line",
                    x0="2024-04-01", x1="2024-04-01",
                    y0=0, y1=y_max,
                    line=dict(color="#888", width=1.5, dash="dot"),
                )
            ],
            annotations=fig.layout.annotations + (
                dict(
                    x="2024-04-01",
                    y=y_max * 0.95,
                    text="AEWV reforms",
                    showarrow=False,
                    font=dict(size=11, color="#555"),
                    xanchor="left",
                    xshift=6,
                ),
            ),
        )

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=(
                    "Non-NZ arrivals by source country — top 5<br>"
                    "<sub>Rolling 12-month average — % of total non-NZ arrivals</sub>"
                ),
                x=0.0,
                font_size=14,
            ),
            xaxis=dict(tickangle=0, showgrid=False, tickformat="%Y"),
            yaxis=dict(
                gridcolor="#EEEEEE",
                ticksuffix="%",
                rangemode="tozero",
            ),
            showlegend=False,
            margin=dict(l=20, r=70, t=90, b=60),
            hovermode="x unified",
        )
        return fig

    # ── Public interface ───────────────────────────────────────────────────────

    def build_figures(self) -> Dict[str, go.Figure]:
        df = self.loader.load_citizenship_direction()
        return {
            "net_area": self._build_net_area(df),
            "share": self._build_share(df, n=5),
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
