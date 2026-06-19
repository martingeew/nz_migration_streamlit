# Quarto Dashboard Rules

## Build workflow

```bash
python src/build_dashboard.py   # 1. Generate chart HTML → dashboard/data/*.html
quarto render dashboard/        # 2. Render site → docs/
# 3. Verify desktop + mobile layout before pushing:
/preview-dashboard --section "#section-id"
git add docs/ && git commit && git push   # 4. Deploy to GitHub Pages
```

Never skip step 1 before step 2 — the chart HTML files are gitignored and must be regenerated each time.

## GitHub Pages

- `_quarto.yml` sets `output-dir: ../docs` — render output lands in `docs/` at repo root
- `docs/` is **committed** to the repo (not gitignored)
- GitHub Pages: Settings → Pages → Deploy from branch → `main` / `/docs`
- Live URL: `https://martingeew.github.io/nz_migration_streamlit/`

## `{{< include >}}` — MUST use raw HTML blocks

Quarto's `{{< include data/*.html >}}` embeds the file content into the markdown stream. Without a raw block, Pandoc escapes `<script>` tags as `<pre><code>` and charts do not render.

**Always wrap every chart include in a `{=html}` raw block:**

```markdown
```{=html}
{{< include data/chart-name.html >}}
```
```

Shortcodes are processed by Quarto before Pandoc sees the document, so they work correctly inside raw blocks.

## Chart HTML generation

`src/dashboard/export.py` `save_chart_html()`:
- `full_html=False` — fragment only (no `<html>` wrapper)
- `include_plotlyjs=False` — Plotly.js loaded once via CDN in `_quarto.yml` `include-in-header`
- Output: `dashboard/data/{story-slug}_{chart-key}.html`

## Story architecture

```
src/dashboard/
├── base.py          # BaseStory ABC + FactCheck dataclass
├── data_loader.py   # DataLoader singleton — caches pkl files by pattern
├── fact_checker.py  # EvidenceScorer — render_html(), render_markdown()
├── export.py        # save_chart_html(), save_all_charts()
└── stories/
    ├── kiwi_exodus.py   # slug: kiwi-exodus   charts: main, split
    ├── india_surge.py   # slug: india-surge   charts: bump, share
    ├── visa_shift.py    # slug: visa-shift    charts: overall, india_clpr
    └── regional_map.py  # slug: where-they-land  charts: map, top_bottom
```

Each story implements `get_fact_check() -> FactCheck` and `build_figures() -> Dict[str, go.Figure]`. `build_dashboard.py` calls `story.run()` on each.

## Fact-check report

`build_dashboard.py` writes `output/fact_check_report.md` after chart generation — internal use only, not embedded in the public site. Call `_write_fact_check_report(stories, repo_root / "output")` at end of `main()`.

## index.qmd section pattern

```markdown
## Section Title

1–2 sentences of commentary.

```{=html}
{{< include data/story-slug_chart-key.html >}}
```

<p class="data-source">Source: Statistics NZ ITMxxxxxx — description.</p>
```

## Styles

`dashboard/styles.css` must start with `/*-- scss:rules --*/` (Quarto SCSS layer marker — without it, render fails with "doesn't contain at least one layer boundary").
