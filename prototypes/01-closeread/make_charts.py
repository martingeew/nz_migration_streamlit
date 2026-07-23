"""
Chart generation for the Closeread scrollytelling prototype.

Builds one Plotly HTML fragment per scroll step. Closeread swaps between
stickies rather than mutating a single chart, so each step needs its own
fully-rendered figure.

Inputs:
    prototypes/data/net_migration_citizenship.json

Outputs:
    prototypes/01-closeread/charts/step-{id}.html  (5 fragments)

Fragments follow the repo convention from src/dashboard/export.py:
full_html=False, include_plotlyjs=False (Plotly loaded once via CDN in
_quarto.yml).

Run from the repo root:
    .venv/Scripts/python prototypes/01-closeread/make_charts.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import plotly.graph_objects as go

PROTOTYPE_DIR = Path(__file__).parent
DATA_PATH = PROTOTYPE_DIR.parent / "data" / "net_migration_citizenship.json"
CHART_DIR = PROTOTYPE_DIR / "charts"

CHART_HEIGHT = 520
AXIS_GREY = "#CCCCCC"
MUTED = "#999999"


# ── Figure construction ────────────────────────────────────────────────────────

def _add_series(
    fig: go.Figure,
    payload: Dict[str, Any],
    key: str,
    dimmed: bool = False,
) -> None:
    """Add one net-migration line to the figure."""
    months = [r["month"] for r in payload["series"]]
    values = [r[key] for r in payload["series"]]
    color = MUTED if dimmed else payload["colors"][key]

    fig.add_trace(
        go.Scatter(
            x=months,
            y=values,
            mode="lines",
            name=payload["labels"][key],
            line=dict(color=color, width=3 if not dimmed else 1.5),
            hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>",
        )
    )


def _add_focus(fig: go.Figure, payload: Dict[str, Any], focus_key: str) -> None:
    """Mark a single annotation point with a dot and label."""
    point = payload["annotations"][focus_key]
    color = payload["colors"][point["series"]]

    fig.add_trace(
        go.Scatter(
            x=[point["month"]],
            y=[point["value"]],
            mode="markers",
            marker=dict(color=color, size=12, line=dict(color="white", width=2)),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_annotation(
        x=point["month"],
        y=point["value"],
        text=f"<b>{point['value']:,}</b><br>{point['label']}",
        showarrow=True,
        arrowhead=0,
        arrowcolor=color,
        arrowwidth=1.5,
        ax=0,
        ay=-50 if point["value"] > 0 else 50,
        font=dict(size=13, color=color),
        align="center",
    )


def _build_figure(payload: Dict[str, Any], step: Dict[str, Any]) -> go.Figure:
    """Build the figure for one scroll step."""
    fig = go.Figure()

    for key in step["visible"]:
        _add_series(fig, payload, key)

    if step["focus"]:
        _add_focus(fig, payload, step["focus"])

    fig.add_hline(y=0, line=dict(color=AXIS_GREY, width=1))

    fig.update_layout(
        template="plotly_white",
        height=CHART_HEIGHT,
        margin=dict(l=20, r=20, t=20, b=40),
        showlegend=len(step["visible"]) > 1,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0
        ),
        xaxis=dict(tickangle=0, showgrid=False, tickformat="%Y"),
        yaxis=dict(gridcolor="#EEEEEE", tickformat=",.0f", range=_y_range(payload)),
        hovermode="x unified",
    )
    return fig


def _y_range(payload: Dict[str, Any]) -> List[float]:
    """Shared y-axis range so stickies do not jump between steps."""
    values = [
        v
        for r in payload["series"]
        for v in (r["total"], r["nz"], r["non_nz"])
    ]
    lo, hi = min(values), max(values)
    pad = (hi - lo) * 0.12
    return [lo - pad, hi + pad]


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Building Closeread prototype charts")
    print("-" * 60)

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    for step in payload["steps"]:
        fig = _build_figure(payload, step)
        out = CHART_DIR / f"step-{step['id']}.html"
        fig.write_html(
            out,
            full_html=False,
            include_plotlyjs=False,
            config={"displayModeBar": False, "responsive": True},
        )
        print(f"  step-{step['id']:<8} {out.stat().st_size / 1024:6.1f} KB")

    print("-" * 60)
    print(f"Wrote {len(payload['steps'])} fragments to charts/")


if __name__ == "__main__":
    main()
