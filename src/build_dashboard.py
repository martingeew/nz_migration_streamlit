"""
Dashboard build script — pre-generates all Plotly chart HTML for the Quarto site.

Run from the repository root before `quarto render dashboard/`:
    python src/build_dashboard.py

Output: dashboard/data/*.html (one file per chart)

Inputs:
    data/interim/df_*.pkl  — processed migration data files
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

# Add repo root to path so src.dashboard imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dashboard.data_loader import DataLoader
from src.dashboard.fact_checker import EvidenceScorer
from src.dashboard.stories.kiwi_exodus import KiwiExodusStory
from src.dashboard.stories.india_surge import IndiaSurgeStory
from src.dashboard.stories.visa_shift import VisaShiftStory
from src.dashboard.stories.regional_map import RegionalMapStory


def _write_fact_check_report(stories: list, output_dir: Path) -> None:
    """Write an internal markdown fact-check report for all stories.

    Args:
        stories: List of BaseStory instances — each must implement get_fact_check().
        output_dir: Directory to write fact_check_report.md into.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    scorer = EvidenceScorer()
    lines: list[str] = [
        "# NZ Migration — Fact-Check Report\n\n",
        f"_Generated {datetime.date.today()}_\n\n---\n\n",
    ]
    for story in stories:
        fact = story.get_fact_check()
        lines.append(f"## {story.title}\n\n")
        lines.append(scorer.render_markdown(fact))
        lines.append("\n\n---\n\n")
    path = output_dir / "fact_check_report.md"
    path.write_text("".join(lines), encoding="utf-8")
    print(f"  Fact-check report saved: {path}")


def main() -> None:
    """Run all stories and export chart HTML files to dashboard/data/.

    Quarto .qmd files embed these via {{< include >}} shortcodes —
    no Python execution needed during quarto render.

    Also writes output/fact_check_report.md for internal review.
    """
    print("NZ Migration Dashboard — build script")
    print("=" * 50)

    loader = DataLoader()

    stories = [
        KiwiExodusStory(loader),
        IndiaSurgeStory(loader),
        VisaShiftStory(loader),
        RegionalMapStory(loader),
    ]

    for story in stories:
        story.run()

    print("\n--- Fact-check report ---")
    repo_root = Path(__file__).parent.parent
    _write_fact_check_report(stories, repo_root / "output")

    print("\n" + "=" * 50)
    print("Build complete. Run 'quarto render dashboard/' to generate the site.")


if __name__ == "__main__":
    main()
