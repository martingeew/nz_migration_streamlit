"""
EvidenceScorer — renders FactCheck records as styled HTML callout blocks.

Each story embeds one callout block showing the political claim, its source,
an evidence quality score badge, what the data shows, and any caveats.

Usage:
    scorer = EvidenceScorer()
    html = scorer.render_html(story.get_fact_check())
"""

from __future__ import annotations

from src.dashboard.base import FactCheck

# ── Score visual config ────────────────────────────────────────────────────────

_SCORE_CONFIG: dict[str, dict] = {
    "strongly_supported": {
        "label": "Strongly Supported",
        "icon": "✓✓",
        "color": "#FFFFFF",
        "bg": "#1A7A4A",
        "badge_bg": "#1A7A4A",
        "border": "#1A7A4A",
        "strip": "#1A7A4A",
    },
    "mostly_supported": {
        "label": "Mostly Supported",
        "icon": "✓",
        "color": "#FFFFFF",
        "bg": "#2E9E5A",
        "badge_bg": "#2E9E5A",
        "border": "#2E9E5A",
        "strip": "#2E9E5A",
    },
    "partly_supported": {
        "label": "Partly Supported",
        "icon": "~",
        "color": "#FFFFFF",
        "bg": "#D68910",
        "badge_bg": "#D68910",
        "border": "#D68910",
        "strip": "#D68910",
    },
    "unsupported": {
        "label": "Not Supported",
        "icon": "✗",
        "color": "#FFFFFF",
        "bg": "#C0392B",
        "badge_bg": "#C0392B",
        "border": "#C0392B",
        "strip": "#C0392B",
    },
    "contradicted": {
        "label": "Contradicted by Data",
        "icon": "✗✗",
        "color": "#FFFFFF",
        "bg": "#7D3C98",
        "badge_bg": "#7D3C98",
        "border": "#7D3C98",
        "strip": "#7D3C98",
    },
}


# ── EvidenceScorer class ───────────────────────────────────────────────────────

class EvidenceScorer:
    """Renders FactCheck objects as self-contained HTML callout blocks."""

    @staticmethod
    def render_html(fact: FactCheck) -> str:
        """Return a styled HTML string for embedding in Quarto .qmd files.

        Args:
            fact: FactCheck dataclass instance.

        Returns:
            HTML string — safe to emit with #| output: asis in a Quarto cell.
        """
        cfg = _SCORE_CONFIG[fact.score]

        caveats_html = ""
        if fact.caveats:
            items = "".join(f"<li style='margin:3px 0'>{c}</li>" for c in fact.caveats)
            caveats_html = f"""
            <p style="margin:10px 0 2px; font-size:13px; color:#555;">
              <strong>Caveats and data limits:</strong>
            </p>
            <ul style="margin:0; padding-left:20px; font-size:13px; color:#555;">
              {items}
            </ul>"""

        return f"""
<div style="
  border-left: 5px solid {cfg['strip']};
  background: #FAFAFA;
  padding: 16px 20px;
  margin: 24px 0;
  border-radius: 0 6px 6px 0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
">
  <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
    <span style="
      background:{cfg['badge_bg']};
      color:{cfg['color']};
      padding:3px 12px;
      border-radius:20px;
      font-size:12px;
      font-weight:700;
      letter-spacing:0.5px;
      text-transform:uppercase;
    ">{cfg['icon']}&nbsp;&nbsp;{cfg['label']}</span>
    <span style="font-size:12px; color:#888;">Evidence quality score</span>
  </div>
  <p style="margin:6px 0; font-size:14px; line-height:1.5;">
    <strong>Claim:</strong> &ldquo;{fact.claim}&rdquo;
  </p>
  <p style="margin:4px 0; font-size:13px; color:#666;">
    <strong>Source:</strong> {fact.source}
  </p>
  <p style="margin:10px 0 4px; font-size:14px; line-height:1.5;">
    <strong>What the data shows:</strong> {fact.evidence}
  </p>
  {caveats_html}
</div>
"""

    @staticmethod
    def render_markdown(fact: FactCheck) -> str:
        """Render a FactCheck as a markdown section for internal reports.

        Args:
            fact: FactCheck dataclass instance.

        Returns:
            Markdown string with verdict, claim, source, evidence, and caveats.
        """
        cfg = _SCORE_CONFIG[fact.score]
        caveats_md = ""
        if fact.caveats:
            caveats_md = "\n**Caveats:**\n" + "".join(f"- {c}\n" for c in fact.caveats)
        return (
            f"**Verdict:** {cfg['icon']} {cfg['label']}\n\n"
            f'**Claim:** "{fact.claim}"\n\n'
            f"**Source:** {fact.source}\n\n"
            f"**Evidence:** {fact.evidence}\n"
            f"{caveats_md}"
        )

    @staticmethod
    def render_compact_html(fact: FactCheck) -> str:
        """Return a compact one-line badge + evidence note for single-page use.

        Format:
            [SCORE BADGE]  Evidence sentence. Caveats: ...

        Args:
            fact: FactCheck dataclass instance.

        Returns:
            HTML string for embedding above a chart in index.qmd.
        """
        cfg = _SCORE_CONFIG[fact.score]

        caveats_note = ""
        if fact.caveats:
            caveats_note = f" <em style='color:#888'>Caveat: {fact.caveats[0]}</em>"

        return (
            f'<p style="margin:4px 0 12px; font-size:13px; line-height:1.6;">'
            f'<span style="background:{cfg["badge_bg"]}; color:{cfg["color"]}; '
            f'padding:2px 9px; border-radius:20px; font-size:11px; font-weight:700; '
            f'text-transform:uppercase; letter-spacing:0.4px; vertical-align:middle;">'
            f'{cfg["icon"]}&nbsp;{cfg["label"]}</span>'
            f'&nbsp;&nbsp;{fact.evidence}{caveats_note}'
            f'</p>'
        )
