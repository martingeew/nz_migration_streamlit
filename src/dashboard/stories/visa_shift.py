"""
Story 3 — The Visa Mix Shift.

Shows how the composition of arrivals by visa type has changed over time,
and provides an India-specific breakdown using CLPR data.

Charts:
    overall   — Stacked area: monthly arrivals by visa type (all citizenships)
    india_clpr — Stacked area: monthly arrivals where CLPR = India, by visa type

Data:
    df_direction_visa_*.pkl         → Columns: Month, Count, Direction, Visa
    df_clpr_india_visa_*.pkl        → Columns: Month, Count, Direction, CLPR, Visa, Citizenship
"""

from __future__ import annotations

from typing import Dict, TYPE_CHECKING

import pandas as pd
import plotly.graph_objects as go

from src.dashboard.base import BaseStory, FactCheck, PLOTLY_TEMPLATE
from src.dashboard.export import save_all_charts

if TYPE_CHECKING:
    from src.dashboard.data_loader import DataLoader

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

# Policy event annotations
_EVENTS = [
    dict(x="2020-03-01", label="Border<br>closed", ay=50),
    dict(x="2022-05-01", label="AEWV<br>launched", ay=-50),
    dict(x="2022-08-01", label="Borders<br>reopen", ay=50),
    dict(x="2024-04-01", label="AEWV<br>reforms", ay=-50),
]

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

        for visa in _VISA_ORDER:
            if visa not in pivot.columns:
                continue
            series = pivot[visa].fillna(0)
            fig.add_trace(
                go.Scatter(
                    x=series.index,
                    y=series.values,
                    mode="lines",
                    stackgroup="one",
                    name=visa,
                    line=dict(width=0, color=_VISA_COLORS.get(visa, "#AAAAAA")),
                    fillcolor=_VISA_COLORS.get(visa, "#AAAAAA"),
                    hovertemplate=f"<b>{visa}</b><br>%{{x|%b %Y}}: %{{y:,.0f}}<extra></extra>",
                )
            )

        # Policy annotations
        annotations = []
        for ev in _EVENTS:
            try:
                y_max = pivot.sum(axis=1).max()
                annotations.append(
                    dict(
                        x=ev["x"],
                        y=y_max * 0.95,
                        text=ev["label"],
                        showarrow=True,
                        arrowhead=2,
                        arrowcolor="#888",
                        font=dict(size=10, color="#555"),
                        ax=0,
                        ay=ev["ay"],
                        bgcolor="rgba(255,255,255,0.7)",
                    )
                )
            except Exception:
                pass

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(
                text=f"{title}<br><sub>{subtitle}</sub>",
                x=0.0,
                font_size=18,
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
                yanchor="bottom",
                y=-0.35,
                xanchor="left",
                x=0,
            ),
            annotations=annotations,
            margin=dict(l=20, r=20, t=90, b=100),
            hovermode="x unified",
        )
        return fig

    # ── Figure builders ────────────────────────────────────────────────────────

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
        )
        return self._stacked_area(
            pivot,
            title="NZ arrivals by visa type",
            subtitle="Monthly arrivals — all citizenships",
        )

    def _build_india_clpr(self, df_clpr: pd.DataFrame) -> go.Figure:
        """Stacked area: arrivals where CLPR = India, by visa type."""
        arrivals = df_clpr[
            (df_clpr["Direction"] == "Arrivals")
            & (~df_clpr["Visa"].str.upper().str.contains("TOTAL", na=False))
        ].copy()

        pivot = (
            arrivals.groupby(["Month", "Visa"])["Count"]
            .sum()
            .unstack("Visa")
            .sort_index()
        )
        return self._stacked_area(
            pivot,
            title="NZ arrivals by visa type — CLPR: India",
            subtitle=(
                "Monthly arrivals whose Country of Last Permanent Residence is India"
            ),
        )

    # ── Public interface ───────────────────────────────────────────────────────

    def build_figures(self) -> Dict[str, go.Figure]:
        df_visa = self.loader.load_direction_visa()
        figs: Dict[str, go.Figure] = {
            "overall": self._build_overall(df_visa),
        }
        try:
            df_clpr = self.loader.load_clpr_india_visa()
            figs["india_clpr"] = self._build_india_clpr(df_clpr)
        except FileNotFoundError:
            print("  [visa-shift] CLPR India data not yet downloaded — skipping india_clpr chart.")
        return figs

    def run(self) -> None:
        print(f"\n[{self.title}]")
        figs = self.build_figures()
        save_all_charts(self.slug, figs, self.output_dir)
        # If CLPR chart wasn't built, save a styled placeholder so the
        # {{< include >}} in the .qmd doesn't fail.
        clpr_path = self.output_dir / f"{self.slug}_india_clpr.html"
        if not clpr_path.exists():
            clpr_path.write_text(
                """<div style="background:#FFF3CD; border-left:4px solid #F39C12;
                   padding:14px 18px; border-radius:4px; margin:24px 0;">
                  <strong>Data pending:</strong> The India CLPR breakdown requires a separate
                  Stats NZ table (Estimated migrant arrivals by citizenship, visa type and CLPR).
                  Run <code>python src/data/download_stats_nz.py --dataset itm_citizenship_visa</code>
                  then <code>python src/data/process_clpr_india_visa.py</code> to enable this chart.
                </div>""",
                encoding="utf-8",
            )
            print(f"  Saved placeholder: {self.slug}_india_clpr.html")
