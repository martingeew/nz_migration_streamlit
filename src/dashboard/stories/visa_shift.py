"""
Story 3 — The Visa Mix Shift.

Shows how the composition of arrivals by visa type has changed over time,
and provides CLPR breakdowns for India and China.

Charts:
    w1_decisions — Line: monthly approved work visa decisions by substream (MBIE W1)
    overall      — Stacked area: monthly arrivals by visa type (all citizenships)
    india_clpr   — Stacked area: monthly arrivals where CLPR = India, by visa type
    china_clpr   — Stacked area: monthly arrivals where CLPR = China, by visa type

Data:
    mbie_w1_work_decisions_monthly.csv  → Columns: Date, Decision Type, Application Substream, Count
    df_direction_visa_*.pkl             → Columns: Month, Count, Direction, Visa
    df_clpr_india_visa_*.pkl            → Columns: Month, Count, Direction, CLPR, Visa, Citizenship
    df_clpr_china_visa_*.pkl            → Columns: Month, Count, Direction, CLPR, Visa, Citizenship
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

_W1_DATA_PATH = Path(__file__).parents[3] / "data" / "raw" / "mbie_w1_work_decisions_monthly.csv"

# ── W1 substream colour map ───────────────────────────────────────────────────

_W1_SUBSTREAM_COLORS: dict[str, str] = {
    "Skilled Work": "#2980B9",
    "Working Holiday": "#27AE60",
    "Relationship": "#8E44AD",
    "Work -RSE": "#F39C12",
    "Job Search": "#E74C3C",
    "Other": "#95A5A6",
}

_W1_SUBSTREAM_LABELS: dict[str, str] = {
    "Skilled Work": "Skilled / AEWV",
    "Work -RSE": "RSE",
    "Job Search": "Post-study open",
}

# Substreams rolled into "Other" in the W1 chart
_W1_OTHER_SUBSTREAMS = {
    "Work to Residence", "Humanitarian", "Approved In Principle",
    "Section 61", "LTBV/Investor", "Business Investor", "Crew", "IPT Order",
    "Skilled Migrant",
}

# ── Visa colour map ────────────────────────────────────────────────────────────
# Consistent with streamlit_app_plotly.py visa_color_map

_VISA_COLORS: dict[str, str] = {
    "Residence": "#E74C3C",
    "Student": "#F4D03F",
    "Visitor": "#27AE60",
    "Work": "#2980B9",
    "New Zealand and Australian citizens": "#8E44AD",
    "Other": "#E67E22",
    "TOTAL": "#95A5A6",
}

_VISA_ORDER = [
    "New Zealand and Australian citizens",
    "Residence",
    "Work",
    "Student",
    "Visitor",
    "Other",
]

_VISA_SHORT_NAMES: dict[str, str] = {
    "New Zealand and Australian citizens": "NZ & AU citizens",
}

# ── Story class ────────────────────────────────────────────────────────────────


class VisaShiftStory(BaseStory):
    """How the visa mix of NZ arrivals has changed, with India CLPR detail."""

    title = "The Visa Mix Shift"
    slug = "visa-shift"

    def get_fact_check(self) -> FactCheck:
        return FactCheck(
            claim=(
                "Uncapped numbers of students with the right to work "
                "will take Kiwi jobs off Kiwis."
            ),
            source="Winston Peters, NZ First Leader, State of the Nation address, March 2026",
            score="partly_supported",
            evidence=(
                "Student visa arrivals surged sharply after the border reopened "
                "in 2022 and remain elevated. Work visa arrivals also spiked under "
                "the AEWV, though reforms in April 2024 moderated the rate. "
                "Whether student/work visa holders displace domestic workers "
                "requires labour market data not covered here."
            ),
            caveats=[
                "Arrivals ≠ net (many students depart after completing study).",
                (
                    "The India CLPR panel shows visa mix for people whose last "
                    "permanent residence was India — a stronger indicator of "
                    "'from India' than citizenship alone."
                ),
                (
                    "Skill-level data (ANZSCO) from INZ work visa files is needed "
                    "to assess whether arrivals fill genuine shortages."
                ),
            ],
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _stacked_area(
        pivot: pd.DataFrame,
        title: str,
        subtitle: str,
    ) -> go.Figure:
        """Build a stacked area figure from a pivot (Month × Visa)."""
        fig = go.Figure()

        active_visas = [v for v in _VISA_ORDER if v in pivot.columns]
        row_totals = pivot[active_visas].fillna(0).sum(axis=1).replace(0, float("nan"))

        for visa in active_visas:
            series = pivot[visa].fillna(0)
            pct = (series / row_totals * 100).fillna(0).values
            fig.add_trace(
                go.Scatter(
                    x=series.index,
                    y=series.values,
                    customdata=pct,
                    mode="lines",
                    stackgroup="one",
                    name=_VISA_SHORT_NAMES.get(visa, visa),
                    line=dict(width=0, color=_VISA_COLORS.get(visa, "#AAAAAA")),
                    fillcolor=_VISA_COLORS.get(visa, "#AAAAAA"),
                    hovertemplate=f"<b>{visa}</b><br>%{{x|%b %Y}}: %{{y:,.0f}} (%{{customdata:.1f}}%)<extra></extra>",
                )
            )

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=title,
                x=0.0,
                font_size=14,
            ),
            xaxis=dict(
                tickangle=0,
                showgrid=False,
                tickformat="%Y",
                rangeslider_visible=False,
            ),
            yaxis=dict(gridcolor="#EEEEEE", tickformat=","),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.12,
                xanchor="left",
                x=0,
            ),
            shapes=list(BORDER_SHAPES),
            annotations=list(BORDER_ANNOTATIONS),
            margin=dict(l=20, r=20, t=60, b=150),
            hovermode="x unified",
        )
        return fig

    # ── Figure builders ────────────────────────────────────────────────────────

    def _build_w1_decisions(self, df_w1: pd.DataFrame) -> go.Figure:
        """Line chart: 3-month rolling approved work visa decisions by substream."""
        approved = df_w1[df_w1["Decision Type"] == "Approved"].copy()
        approved["Date"] = pd.to_datetime(approved["Date"])
        approved["Category"] = approved["Application Substream"].apply(
            lambda s: "Other" if s in _W1_OTHER_SUBSTREAMS else s
        )

        pivot = (
            approved.groupby(["Date", "Category"])["Count"]
            .sum()
            .unstack("Category")
            .sort_index()
            .rolling(12, min_periods=12)
            .sum()
            .dropna(how="all")
        )

        category_order = ["Skilled Work", "Working Holiday", "Relationship", "Work -RSE", "Job Search", "Other"]
        active = [c for c in category_order if c in pivot.columns]

        fig = go.Figure()
        for cat in active:
            series = pivot[cat].dropna()
            color = _W1_SUBSTREAM_COLORS.get(cat, "#AAAAAA")
            label = _W1_SUBSTREAM_LABELS.get(cat, cat)
            fig.add_trace(go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines",
                name=label,
                line=dict(color=color, width=2),
                hovertemplate=f"<b>{label}</b><br>%{{x|%b %Y}}: %{{y:,.0f}}<extra></extra>",
            ))
            # Direct label pinned to right edge
            fig.add_annotation(
                x=1.0, xref="paper", xanchor="left", xshift=6,
                y=float(series.values[-1]), yref="y",
                text=label, showarrow=False,
                font=dict(size=10, color=color),
            )

        # Policy change markers
        y_max = float(pivot[active].max().max())
        x_end = pivot.index[-1] + pd.DateOffset(months=2)
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(text="Approved work visa decisions", x=0.0, font_size=14),
            xaxis=dict(
                tickangle=0, showgrid=False, tickformat="%Y",
                rangeslider_visible=False,
                range=[pivot.index[0], x_end],
            ),
            yaxis=dict(gridcolor="#EEEEEE", tickformat=",", rangemode="tozero"),
            showlegend=False,
            shapes=[
                dict(
                    type="line", x0="2022-07-01", x1="2022-07-01", y0=0, y1=1,
                    yref="paper", line=dict(color="#999999", width=1.5, dash="dot"),
                ),
                dict(
                    type="line", x0="2024-04-01", x1="2024-04-01", y0=0, y1=1,
                    yref="paper", line=dict(color="#999999", width=1.5, dash="dot"),
                ),
            ],
            annotations=list(fig.layout.annotations) + [
                dict(
                    x="2022-07-01", y=0.97, yref="paper",
                    text="AEWV launch", showarrow=False,
                    xanchor="left", xshift=4, yanchor="top",
                    font=dict(size=9, color="#888888"),
                ),
                dict(
                    x="2024-04-01", y=0.80, yref="paper",
                    text="AEWV reforms", showarrow=False,
                    xanchor="left", xshift=4, yanchor="top",
                    font=dict(size=9, color="#888888"),
                ),
            ],
            margin=dict(l=20, r=100, t=60, b=60),
            hovermode="x unified",
        )
        return fig

    def _build_overall(self, df_visa: pd.DataFrame) -> go.Figure:
        """Stacked area: all arrivals by visa type."""
        arrivals = df_visa[
            (df_visa["Direction"] == "Arrivals")
            & (df_visa["Visa"] != "TOTAL")
        ]
        pivot = (
            arrivals.groupby(["Month", "Visa"])["Count"]
            .sum()
            .unstack("Visa")
            .sort_index()
            .rolling(12, min_periods=12)
            .sum()
            .dropna(how="all")
        )
        return self._stacked_area(
            pivot,
            title="NZ arrivals by visa type",
            subtitle="Rolling 12-month sum — all citizenships",
        )

    def _build_clpr(self, df_clpr: pd.DataFrame, country: str) -> go.Figure:
        """Stacked area: arrivals for a given CLPR country, by visa type."""
        arrivals = df_clpr[
            (df_clpr["Direction"] == "Arrivals")
            & (~df_clpr["Visa"].str.upper().str.contains("TOTAL", na=False))
        ].copy()

        pivot = (
            arrivals.groupby(["Month", "Visa"])["Count"]
            .sum()
            .unstack("Visa")
            .sort_index()
            .rolling(12, min_periods=12)
            .sum()
            .dropna(how="all")
        )
        return self._stacked_area(
            pivot,
            title=f"NZ arrivals by visa type — CLPR: {country}",
            subtitle=f"Rolling 12-month sum — CLPR: {country}",
        )

    def _build_india_clpr(self, df_clpr: pd.DataFrame) -> go.Figure:
        return self._build_clpr(df_clpr, "India")

    def _build_china_clpr(self, df_clpr: pd.DataFrame) -> go.Figure:
        return self._build_clpr(df_clpr, "China")

    # ── Public interface ───────────────────────────────────────────────────────

    def build_figures(self) -> Dict[str, go.Figure]:
        df_visa = self.loader.load_direction_visa()
        figs: Dict[str, go.Figure] = {}
        try:
            df_w1 = pd.read_csv(_W1_DATA_PATH)
            figs["w1_decisions"] = self._build_w1_decisions(df_w1)
        except FileNotFoundError:
            print("  [visa-shift] W1 data not found — skipping w1_decisions chart.")
        figs["overall"] = self._build_overall(df_visa)
        try:
            df_india = self.loader.load_clpr_india_visa()
            figs["india_clpr"] = self._build_india_clpr(df_india)
        except FileNotFoundError:
            print("  [visa-shift] CLPR India data not found — skipping india_clpr chart.")
        try:
            df_china = self.loader.load_clpr_china_visa()
            figs["china_clpr"] = self._build_china_clpr(df_china)
        except FileNotFoundError:
            print("  [visa-shift] CLPR China data not found — skipping china_clpr chart.")
        return figs

    def run(self) -> None:
        print(f"\n[{self.title}]")
        figs = self.build_figures()
        save_all_charts(self.slug, figs, self.output_dir)
        for key, label in [("india_clpr", "India"), ("china_clpr", "China")]:
            path = self.output_dir / f"{self.slug}_{key}.html"
            if not path.exists():
                path.write_text(
                    f"""<div style="background:#FFF3CD; border-left:4px solid #F39C12;
                       padding:14px 18px; border-radius:4px; margin:24px 0;">
                      <strong>Data pending:</strong> Run
                      <code>python src/data/process_clpr_india_visa.py</code>
                      to generate the CLPR {label} breakdown.
                    </div>""",
                    encoding="utf-8",
                )
                print(f"  Saved placeholder: {self.slug}_{key}.html")
