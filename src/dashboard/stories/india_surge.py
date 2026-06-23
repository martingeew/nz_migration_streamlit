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

from pathlib import Path
from typing import Dict, TYPE_CHECKING

import pandas as pd
import plotly.graph_objects as go

from src.dashboard.base import BaseStory, FactCheck, PLOTLY_TEMPLATE, BORDER_SHAPES, BORDER_ANNOTATIONS
from src.dashboard.export import save_all_charts

if TYPE_CHECKING:
    from src.dashboard.data_loader import DataLoader

# ── Skill level colour map ────────────────────────────────────────────────────
# Diverging: teal = high skill (1), red = low skill (5)

_SKILL_COLORS: dict[str, str] = {
    "Skill level 1": "#045275",
    "Skill level 2": "#089099",
    "Skill level 3": "#46AEA0",
    "Skill level 4": "#F4A261",
    "Skill level 5": "#C0392B",
}
_SKILL_ORDER = ["Skill level 5", "Skill level 4", "Skill level 3", "Skill level 2", "Skill level 1"]
_SKILL_DATA_PATH = Path(__file__).parents[3] / "data" / "raw" / "mbie_w3_work_occupations_nationality_skill_level_may_years.csv"

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
                "pre-dates Peters' speech and is strongly supported by monthly data. "
                "India's ANZSCO Level 4–5 (lower-skill) work visa share rose from "
                "~15% in the year ended May 2017 to ~36% in the year ended May 2026, "
                "with a structural break at the 2022 AEWV launch. However, Vietnam "
                "(49%) and Fiji (48%) both have higher lower-skill shares — the pattern "
                "is not India-specific. China (11%) has a strongly high-skill profile."
            ),
            caveats=[
                (
                    "Peters' claim is partly forward-looking; current data confirms "
                    "the historical trend but cannot verify future volumes."
                ),
                (
                    "ANZSCO skill level is not recorded for ~40% of work visa approvals "
                    "in the MBIE dataset — skill-level proportions reflect categorised "
                    "records only and may not represent the full intake."
                ),
                (
                    "Whether Indian arrivals 'take Kiwi jobs' requires labour market "
                    "outcome data by visa type — not available in public datasets."
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
                text="Net migration to NZ by source country",
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
                y=-0.15,
                xanchor="left",
                x=0,
            ),
            showlegend=True,
            shapes=list(BORDER_SHAPES),
            annotations=list(BORDER_ANNOTATIONS),
            margin=dict(l=20, r=20, t=60, b=150),
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

            # Label pinned to right edge of chart in paper coords — doesn't expand x-axis
            fig.add_annotation(
                x=1.0,
                xref="paper",
                xanchor="left",
                xshift=6,
                y=float(series.values[-1]),
                yref="y",
                text=_short_name(country),
                showarrow=False,
                font=dict(size=11, color=color),
            )

        # AEWV reform vertical line
        y_max = float(shares.max().max())
        x_end = shares.index[-1] + pd.DateOffset(months=3)
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
                    xanchor="right",
                    xshift=-6,
                ),
            ),
        )

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text="Non-NZ arrivals by source country — top 5",
                x=0.0,
                font_size=14,
            ),
            xaxis=dict(
                tickangle=0,
                showgrid=False,
                tickformat="%Y",
                range=[shares.index[0], x_end],
            ),
            yaxis=dict(
                gridcolor="#EEEEEE",
                ticksuffix="%",
                rangemode="tozero",
                automargin=True,
            ),
            showlegend=False,
            margin=dict(l=0, r=90, t=60, b=60),
            hovermode="x unified",
        )
        return fig

    def _build_skill_shift(self, df_skills: pd.DataFrame) -> go.Figure:
        """100% horizontal stacked bar: India approved work visa skill mix by year ended May."""
        india = df_skills[
            (df_skills["Nationality"] == "India")
            & (df_skills["Decision Type"] == "Approved")
            & (df_skills["Occupation Skill Level"] != "(not recorded)")
            & (df_skills["Year Ended May"] != "2016 PARTIAL (Jul-May)")
        ]
        pivot = (
            india.groupby(["Year Ended May", "Occupation Skill Level"])["Count"]
            .sum()
            .unstack(fill_value=0)
        )

        fig = go.Figure()
        for skill in _SKILL_ORDER:
            if skill not in pivot.columns:
                continue
            n = skill.split()[-1]
            label = f"Level {n} (highest)" if n == "1" else f"Level {n} (lowest)" if n == "5" else f"Level {n}"
            fig.add_trace(go.Bar(
                name=label,
                y=pivot.index,
                x=pivot[skill],
                orientation="h",
                marker_color=_SKILL_COLORS[skill],
                hovertemplate=f"<b>{skill}</b><br>%{{y}}: %{{x:,}} approved<extra></extra>",
            ))

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            barmode="stack",
            barnorm="fraction",
            title=dict(
                text="India work visas: shifting toward lower-skill roles",
                x=0.0,
                font_size=14,
            ),
            xaxis=dict(tickformat=".0%", showgrid=False),
            yaxis=dict(gridcolor="#EEEEEE"),
            legend=dict(
                orientation="h", yanchor="top", y=-0.10,
                xanchor="left", x=0, traceorder="reversed",
            ),
            height=480,
            margin=dict(l=20, r=20, t=60, b=120),
            hovermode="y unified",
        )
        return fig

    def _build_country_skill(self, df_skills: pd.DataFrame) -> go.Figure:
        """Horizontal 100% stacked bar: work visa skill mix, top 10 countries, year ended May 2026."""
        recent = df_skills[
            (df_skills["Year Ended May"] == "2026")
            & (df_skills["Decision Type"] == "Approved")
            & (df_skills["Occupation Skill Level"] != "(not recorded)")
        ]
        top10 = (
            recent.groupby("Nationality")["Count"].sum().nlargest(10).index.tolist()
        )
        filtered = recent[recent["Nationality"].isin(top10)]
        pivot = (
            filtered.groupby(["Nationality", "Occupation Skill Level"])["Count"]
            .sum()
            .unstack(fill_value=0)
        )
        # Sort ascending so highest lo-skill appears at top of horizontal chart
        lo_cols = [c for c in ["Skill level 4", "Skill level 5"] if c in pivot.columns]
        total = pivot.sum(axis=1)
        lo_share = pivot[lo_cols].sum(axis=1) / total
        pivot = pivot.loc[lo_share.sort_values(ascending=True).index]

        fig = go.Figure()
        for skill in _SKILL_ORDER:
            if skill not in pivot.columns:
                continue
            n = skill.split()[-1]
            label = f"Level {n} (highest)" if n == "1" else f"Level {n} (lowest)" if n == "5" else f"Level {n}"
            fig.add_trace(go.Bar(
                name=label,
                y=pivot.index,
                x=pivot[skill],
                orientation="h",
                marker_color=_SKILL_COLORS[skill],
                hovertemplate=f"<b>{skill}</b><br>%{{y}}: %{{x:,}} approved<extra></extra>",
            ))

        # Annotate lo-skill % on the right for each country
        annotations = []
        for country in pivot.index:
            pct = lo_share[country] * 100
            annotations.append(dict(
                x=1.01, xref="paper",
                y=country, yref="y",
                text=f"{pct:.0f}%",
                showarrow=False,
                font=dict(size=10, color="#C0392B" if country == "India" else "#555"),
                xanchor="left",
                yanchor="middle",
            ))

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            barmode="stack",
            barnorm="fraction",
            title=dict(
                text="Work visa skill mix by nationality (May 2026)",
                x=0.0,
                font_size=14,
            ),
            xaxis=dict(tickformat=".0%", showgrid=False),
            yaxis=dict(gridcolor="#EEEEEE"),
            legend=dict(
                orientation="h", yanchor="top", y=-0.10,
                xanchor="left", x=0, traceorder="reversed",
            ),
            annotations=annotations,
            height=520,
            margin=dict(l=20, r=70, t=60, b=120),
            hovermode="y unified",
        )
        return fig

    # ── Public interface ───────────────────────────────────────────────────────

    def build_figures(self) -> Dict[str, go.Figure]:
        df = self.loader.load_citizenship_direction()
        df_skills = pd.read_csv(_SKILL_DATA_PATH)
        return {
            "net_area": self._build_net_area(df),
            "share": self._build_share(df, n=5),
            "skill_shift": self._build_skill_shift(df_skills),
            "country_skill": self._build_country_skill(df_skills),
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
