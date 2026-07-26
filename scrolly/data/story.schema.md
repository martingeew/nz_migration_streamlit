# The `story.json` data contract

Every chart in this story reads one file: `src/data/story.json`, emitted by
`data/build.py`. The front end never touches the raw pkl files.

This is the scrollytelling-starter skill's contract with four additions, marked
**[extended]** below. The additions are what this story needed: stacked areas instead
of lines, several charts in one page instead of one, and band highlighting instead of
point annotations.

## Top-level keys

| Key | Type | What it is |
|---|---|---|
| `meta` | object | Header and provenance. `title`, `standfirst`, `byline`, `sources`, `notes`. |
| `colors` | object | `{ series_key: hex }`. **The keys here define the series keys** used everywhere else. |
| `labels` | object | `{ series_key: string }`. Drawn beside each band at the right edge. |
| `annotations` | object | Empty here. The skill's point-annotation feature is unused; highlighting replaced it. |
| `charts` | object | **[extended]** One entry per chart. Stack order, y-domain, title, subtitle. |
| `steps` | array | The narrative. One object per scroll block, in order. |
| `series` | array | The data. One object per month. |

## `meta` — header and provenance

```json
{
  "title": "Who is actually arriving in New Zealand",
  "standfirst": "Non-New Zealand citizen arrivals reached 211,842 ...",
  "byline": "Built by Autonomous Econ",
  "sources": ["Statistics NZ ITM552301 - ..."],
  "notes": ["Every series is a rolling 12-month sum, ..."],
  "generated": "2026-07-26", "unit": "12-month rolling sum",
  "months": 255, "start": "2005-01", "end": "2026-03"
}
```

**[extended]** `sources` and `notes` are arrays rather than the skill's single `source`
string. `App.svelte` renders both in the footer, so they appear only once the reader has
scrolled past the last step.

## `series` — the data

An array of records, oldest first. Each record has a `month` string (`YYYY-MM`) and one
integer field per series key. Every key appears on every record:

```json
{ "month": "2026-03", "flow_arrivals": 109208, "flow_departures": -48421, "...": 0 }
```

`flow_departures` is stored negative so the mirrored chart fills downward without the
component knowing anything about the data.

## `charts` — one entry per chart **[extended]**

```json
"india": {
  "keys": ["in_work", "in_student", "in_visitor", "in_residence", "in_other"],
  "mode": "stack",
  "y": [0, 40000],
  "title": "Arrivals by visa type: last permanent residence India",
  "subtitle": "Rolling 12-month sum"
}
```

- `keys`: the stack order, **bottom band first**.
- `mode`: `"stack"` stacks the keys with `d3.stack`; `"mirror"` areas each key from zero
  instead, which is how the arrivals-above / departures-below chart is drawn.
- `line`: optional series key drawn as a line on top (only the mirrored chart uses it).
- `y`: the fixed y-domain. Charts that share a domain are directly comparable — here
  `age` and `nationality` share `[0, 245000]`, `india` and `china` share `[0, 40000]`.
  `data/build.py` prints each chart's drawn range on every run and flags any that no
  longer fit.
- `title` / `subtitle`: drawn above the chart, matching the Quarto dashboard's
  `title<br><sub>subtitle</sub>` convention.

## `steps` — the narrative

```json
{
  "chart": "india",
  "highlight": ["in_work"],
  "title": "Work visas, not students, powered the surge",
  "body": "Work visa arrivals peaked at 16,404 ..."
}
```

- `chart` **[extended]**: which entry of `charts` to draw. Replaces the skill's
  `visible` array, because a stack needs an order, not a set.
- `highlight` **[extended]**: series keys the commentary is about. They stay solid while
  every other band in the chart drops to 22% opacity. An empty array means all bands
  solid. Replaces the skill's `focus` annotation.
- `title` / `body`: the text shown in the step block below the chart.

## Rules that keep it working

1. The keys of `colors` are the source of truth. `labels`, every `series` record, and
   every `charts[*].keys` entry must use the same keys.
2. Colours are keyed to the **group**, not the chart. Work visas are the same blue in the
   India chart and the China chart; Student the same yellow. Two charts never reuse one
   colour for different things at the same time.
3. Series colours live here, not in the theme files, so switching
   `minimalist-dark.css` for `minimalist-white.css` never touches the data.
4. `month` strings are `YYYY-MM`, oldest first, with no gaps.
5. Numbers in `steps[*].body` are computed in `build.py` from the same frame that
   produces `series`, never typed by hand.
