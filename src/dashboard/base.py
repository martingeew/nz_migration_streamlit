"""
Base classes for dashboard stories.

Each story encapsulates:
- A political claim being stress-tested
- Data transforms and Plotly figure construction
- A FactCheck record with evidence score and caveats

Usage:
    class MyStory(BaseStory):
        title = "My Story"
        slug  = "my-story"
        def get_fact_check(self) -> FactCheck: ...
        def build_figures(self) -> dict[str, go.Figure]: ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List

import plotly.graph_objects as go

if TYPE_CHECKING:
    from src.dashboard.data_loader import DataLoader

# ── Constants ──────────────────────────────────────────────────────────────────

PLOTLY_TEMPLATE = "plotly_white"

# Teal-green sequential palette (global convention)
PALETTE = [
    "#F7FEAE", "#B7E6A5", "#7CCBA2", "#46AEA0",
    "#089099", "#00718B", "#045275",
]

# Border closure vertical lines — add to any stacked area chart
BORDER_SHAPES = [
    dict(
        type="line", x0="2020-03-01", x1="2020-03-01", y0=0, y1=1, yref="paper",
        line=dict(color="#999999", width=1.5, dash="dot"),
    ),
    dict(
        type="line", x0="2022-08-01", x1="2022-08-01", y0=0, y1=1, yref="paper",
        line=dict(color="#999999", width=1.5, dash="dot"),
    ),
]

BORDER_ANNOTATIONS = [
    dict(
        x="2020-03-01", y=0.97, yref="paper",
        text="Border closed", showarrow=False,
        xanchor="left", xshift=4, yanchor="top",
        font=dict(size=9, color="#888888"),
    ),
]

SCORE_LEVELS = [
    "strongly_supported",
    "mostly_supported",
    "partly_supported",
    "unsupported",
    "contradicted",
]


# ── FactCheck dataclass ────────────────────────────────────────────────────────

@dataclass
class FactCheck:
    """Structured record of evidence quality for a political claim."""

    claim: str
    """Exact or near-exact quote from a politician or official source."""

    source: str
    """Attribution: name, title, and date of the claim."""

    score: str
    """One of: strongly_supported | mostly_supported | partly_supported |
    unsupported | contradicted."""

    evidence: str
    """1–2 sentences summarising what the data actually shows."""

    caveats: List[str] = field(default_factory=list)
    """Data gaps, confounds, or limits on the conclusion."""

    def __post_init__(self) -> None:
        if self.score not in SCORE_LEVELS:
            raise ValueError(
                f"score must be one of {SCORE_LEVELS}, got {self.score!r}"
            )


# ── BaseStory abstract class ───────────────────────────────────────────────────

class BaseStory(ABC):
    """Abstract base class for all dashboard stories.

    Inputs:
        loader: DataLoader instance providing access to processed pkl files.

    Outputs:
        - Plotly figures (via build_figures)
        - FactCheck record (via get_fact_check)
    """

    title: str = ""
    slug: str = ""

    def __init__(self, loader: "DataLoader") -> None:
        self.loader = loader
        self.output_dir = Path(__file__).parent.parent.parent / "dashboard" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_fact_check(self) -> FactCheck:
        """Return the FactCheck record for this story."""
        ...

    @abstractmethod
    def build_figures(self) -> Dict[str, go.Figure]:
        """Build and return all Plotly figures for this story.

        Returns a dict mapping figure keys (e.g. 'main', 'split') to figures.
        """
        ...

    def _apply_base_layout(self, fig: go.Figure, title: str, subtitle: str = "") -> None:
        """Apply shared layout conventions to a figure."""
        title_text = title
        if subtitle:
            title_text = f"{title}<br><sub>{subtitle}</sub>"
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title=dict(text=title_text, x=0.0, font_size=20),
            margin=dict(l=20, r=20, t=80, b=60),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="left",
                x=0,
            ),
            xaxis=dict(tickangle=0, showgrid=False),
            yaxis=dict(gridcolor="#EEEEEE"),
        )
