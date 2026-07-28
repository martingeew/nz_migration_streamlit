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
  "generated": "2026-07-26", "generated_label": "26 July 2026",
  "unit": "12-month rolling sum",
  "months": 255, "start": "2005-01", "end": "2026-03"
}
```

**[extended]** `sources` and `notes` are arrays rather than the skill's single `source`
string. `App.svelte` renders both in the footer, so they appear only once the reader has
scrolled past the last step.

**[extended]** `generated` is the build date in ISO form; `generated_label` is the
same date formatted for display (`"26 July 2026"`). `App.svelte` shows
`generated_label` under the heading, in italics — it is when the report was built,
not the latest data month (`meta.end`).

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

- `kind`: `"series"` for a time-series chart, `"map"` for a choropleth. `App.svelte`
  picks the component from this.
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

## Map charts **[extended]**

A `kind: "map"` chart is a choropleth drawn by `MapChart.svelte`. Geometry lives in
`src/data/maps.json`, not here, keyed by the same join name as `values`:

```json
"akl-map": {
  "kind": "map",
  "map": "auckland",
  "title": "...", "subtitle": "...",
  "scale": {"domain": [0, 40.8, 71.5, 102.1], "range": ["#2A3038", "#2C7FA8", "#5CBBAB", "#C8E9A0"]},
  "fitExclude": [],
  "fitBBox": [[174.4, -37.15], [175.05, -36.35]],
  "values": {
    "Otara-Papatoetoe": {"label": "Ōtara-Papatoetoe", "per1k": 102.1, "net": 10100}
  }
}
```

- `map`: which entry of `maps.json` to draw.
- `scale`: `domain`/`range` arrays fed straight to `d3.scaleLinear`. Built in Python so
  the neutral colour lands exactly on zero when the data goes negative.
- `values`: keyed by the geometry's `properties.key`. `label` carries the display name,
  so macrons survive even though the join key is ASCII.
- `fitBBox`: an optional lon/lat window to frame instead of the features. Auckland needs
  it, because Rodney runs far north and Great Barrier sits 60 km offshore; fitting to the
  features leaves the urban boards unreadably small. The geography is clipped to this
  window, so areas running past it end at a deliberate edge.
- `fitExclude`: a lighter alternative — keep a feature drawn but out of the fit.
- A step's `highlight` lists area keys. Those get an outline, keep full opacity while the
  rest drop back, and receive a leader line out to a label showing name, rate per 1,000
  and absolute net.

### The winding trap

`d3-geo` treats a spherical polygon's interior as the side to the **right** of the ring,
the opposite of GeoJSON RFC 7946. Wind a ring the other way and d3 reads it as the whole
globe: `fitExtent` then dutifully scales the planet into the frame and every real area
collapses to a pixel or two. Plotly draws in the plane and never notices, which is why
the Quarto dashboard renders these same files without complaint.

`build.py` pins clockwise winding on every part, and drops islands below a
tolerance-derived area threshold — Whangarei ships 74 parts and simplification collapsed
one of its smallest into a degenerate ring, which was enough to break the whole map. Any
polygon you synthesise in the front end needs the same winding; the `fitBBox` rectangle
is built clockwise for exactly this reason.

To check geometry before blaming the renderer: `d3.geoArea(feature)` returns about 4π
(12.57) for anything being read as the whole sphere, against ~1e-4 for a real TA.

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
