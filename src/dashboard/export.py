"""
Export utilities — saves Plotly figures as self-contained HTML fragments.

Each chart is saved with full_html=False so it can be embedded inside a
Quarto page that already has Plotly.js loaded via the site header.

Usage:
    from src.dashboard.export import save_chart_html
    save_chart_html(fig, output_dir / "kiwi_exodus_main.html")
"""

from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio


def save_fact_check_html(html: str, path: Path) -> None:
    """Save a fact-check HTML callout to a file for Quarto include.

    Args:
        html: HTML string from EvidenceScorer.render_html().
        path: Destination file path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    print(f"  Saved fact-check: {path.name}")


def save_chart_html(
    fig: go.Figure,
    path: Path,
    include_plotlyjs: str | bool = False,
) -> None:
    """Save a Plotly figure as an HTML fragment (no <html>/<body> wrapper).

    Args:
        fig: Plotly Figure object.
        path: Destination file path (should end in .html).
        include_plotlyjs: Passed to plotly write_html. False = assume Plotly.js
            is already loaded on the page (set in _quarto.yml header).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        str(path),
        full_html=False,
        include_plotlyjs=include_plotlyjs,
        config={"displayModeBar": True, "responsive": True},
    )
    print(f"  Saved chart: {path.name}")


def save_all_charts(story_slug: str, figures: dict[str, go.Figure], output_dir: Path) -> None:
    """Save all figures for a story to output_dir.

    Filenames follow the pattern: {story_slug}_{key}.html
    e.g. kiwi-exodus_main.html, kiwi-exodus_split.html

    Args:
        story_slug: Story identifier string (e.g. 'kiwi-exodus').
        figures: Dict mapping figure key to Figure object.
        output_dir: Directory to save into.
    """
    for key, fig in figures.items():
        filename = f"{story_slug}_{key}.html"
        save_chart_html(fig, output_dir / filename)
