"""Build the scrollytelling data contract (story.json) for the NZ migration story.

Purpose:
    Turn the repo's processed Stats NZ pkl files into the single JSON file the
    Svelte front end reads. Every transform stays in Python; the front end only
    ever sees story.json.

Inputs:
    data/interim/df_citizenship_direction_*.pkl  (via src.dashboard.DataLoader)
    data/interim/df_direction_age_sex_*.pkl
    data/interim/df_clpr_india_visa_*.pkl
    data/interim/df_clpr_china_visa_*.pkl

Outputs:
    scrolly/src/data/story.json — meta + colors + labels + charts + steps + series.
    See scrolly/data/story.schema.md for the shape.

Run from the repo root:
    .venv/Scripts/python scrolly/data/build.py
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

SCROLLY_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SCROLLY_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))

from src.dashboard.data_loader import DataLoader  # noqa: E402

# ── Paths and constants ───────────────────────────────────────────────────────

OUT_JSON = SCROLLY_ROOT / "src" / "data" / "story.json"

ROLLING_WINDOW = 12  # months — annual running total, the standard presentation
START = "2005"       # first year shown on the x-axis

# ── Header text ───────────────────────────────────────────────────────────────

TITLE = "Who is actually arriving in New Zealand"
STANDFIRST = (
    "Non-New Zealand citizen arrivals reached 211,842 in the year to October 2023, "
    "close to three times the pre-COVID norm. Scroll to see how old those arrivals "
    "were, where they came from, and what visas they held."
)
BYLINE = "Built by Autonomous Econ"

SOURCES = [
    "Statistics NZ ITM552301 — migrant arrivals and departures by citizenship.",
    "Statistics NZ ITM552101 — migrant arrivals and departures by age group and sex.",
    "Statistics NZ ITM553001 — migrant arrivals by citizenship, visa type and country "
    "of last permanent residence, 12/16-month rule.",
]

NOTES = [
    "Every series is a rolling 12-month sum, so each point counts the previous year.",
    "Stats NZ does not publish the age breakdown split by citizenship, so the age "
    "chart covers all citizenships. Every other chart is non-New Zealand citizens.",
    "Country of last permanent residence (CLPR) is where a person lived before "
    "arriving, which is a closer match for 'from India' than citizenship alone.",
    "Figures use the 12/16-month rule and the latest months are provisional.",
]

# ── Colours ───────────────────────────────────────────────────────────────────
# The repo's teal palette bottoms out at #045275, which disappears on the
# #111418 dark background, so this story uses the light half of the same family.
# Colours are keyed to the group, not the chart: Work visas are the same blue in
# the India chart and the China chart, Student the same yellow.

_BLUE = "#5BA8DE"
_RED = "#E8705F"
_YELLOW = "#F2C14E"
_GREEN = "#7FD1B9"
_PURPLE = "#A98CD6"
_GREY = "#6B7580"
_WHITE = "#F5F7FA"

COLORS: Dict[str, str] = {
    # Chart 1 — non-NZ flows
    "flow_arrivals": _BLUE,
    "flow_departures": _RED,
    "flow_net": _WHITE,
    # Chart 2 — arrivals by age group (young to old)
    "age_u20": "#F7FEAE",
    "age_20s": "#C8E9A0",
    "age_30s": "#8ED4A8",
    "age_40s": "#5CBBAB",
    "age_50_64": "#37A0AE",
    "age_65p": "#2C7FA8",
    # Chart 3 — arrivals by nationality
    "cit_india": _RED,
    "cit_china": _YELLOW,
    "cit_philippines": _PURPLE,
    "cit_uk": _BLUE,
    "cit_australia": _GREEN,
    "cit_other": _GREY,
    # Chart 4 — India CLPR by visa
    "in_work": _BLUE,
    "in_student": _YELLOW,
    "in_visitor": _GREEN,
    "in_residence": _RED,
    "in_other": _GREY,
    # Chart 5 — China CLPR by visa
    "cn_work": _BLUE,
    "cn_student": _YELLOW,
    "cn_visitor": _GREEN,
    "cn_residence": _RED,
    "cn_other": _GREY,
}

LABELS: Dict[str, str] = {
    "flow_arrivals": "Arrivals",
    "flow_departures": "Departures",
    "flow_net": "Net",
    "age_u20": "Under 20",
    "age_20s": "20s",
    "age_30s": "30s",
    "age_40s": "40s",
    "age_50_64": "50s-64",
    "age_65p": "65+",
    "cit_india": "India",
    "cit_china": "China",
    "cit_philippines": "Philippines",
    "cit_uk": "UK",
    "cit_australia": "Australia",
    "cit_other": "Other",
    "in_work": "Work",
    "in_student": "Student",
    "in_visitor": "Visitor",
    "in_residence": "Residence",
    "in_other": "Other",
    "cn_work": "Work",
    "cn_student": "Student",
    "cn_visitor": "Visitor",
    "cn_residence": "Residence",
    "cn_other": "Other",
}

# ── Chart definitions ─────────────────────────────────────────────────────────
# `keys` is the stack order, bottom to top. `y` is fixed so charts sharing a
# scale can be compared: charts 2 and 3 share one, charts 4 and 5 share another.

CHARTS: Dict[str, Dict[str, Any]] = {
    "flows": {
        "keys": ["flow_arrivals", "flow_departures"],
        "line": "flow_net",
        "mode": "mirror",
        "y": [-60000, 220000],
        "title": "Non-NZ citizen arrivals, departures and net migration",
        "subtitle": "Rolling 12-month sum, arrivals above the line and departures below",
    },
    "age": {
        "keys": ["age_u20", "age_20s", "age_30s", "age_40s", "age_50_64", "age_65p"],
        "mode": "stack",
        "y": [0, 245000],
        "title": "Migrant arrivals by age group",
        "subtitle": "Rolling 12-month sum, all citizenships",
    },
    "nationality": {
        "keys": [
            "cit_india", "cit_china", "cit_philippines",
            "cit_uk", "cit_australia", "cit_other",
        ],
        "mode": "stack",
        "y": [0, 245000],
        "title": "Non-NZ citizen arrivals by nationality",
        "subtitle": "Rolling 12-month sum, top five source countries",
    },
    "india": {
        "keys": ["in_work", "in_student", "in_visitor", "in_residence", "in_other"],
        "mode": "stack",
        "y": [0, 40000],
        "title": "Arrivals by visa type: last permanent residence India",
        "subtitle": "Rolling 12-month sum",
    },
    "china": {
        "keys": ["cn_work", "cn_student", "cn_visitor", "cn_residence", "cn_other"],
        "mode": "stack",
        "y": [0, 40000],
        "title": "Arrivals by visa type: last permanent residence China",
        "subtitle": "Rolling 12-month sum",
    },
}

# ── Source data mappings ──────────────────────────────────────────────────────

# Same six bins as src/dashboard/stories/kiwi_exodus.py, keyed to series names.
_AGE_BINS: Dict[str, List[str]] = {
    "age_u20": ["Under 15 Years", "15-19 Years"],
    "age_20s": ["20-24 Years", "25-29 Years"],
    "age_30s": ["30-34 Years", "35-39 Years"],
    "age_40s": ["40-44 Years", "45-49 Years"],
    "age_50_64": ["50-54 Years", "55-59 Years", "60-64 Years"],
    "age_65p": ["65 Years and Over"],
}

_COUNTRIES: Dict[str, str] = {
    "cit_india": "India",
    "cit_china": "China, People's Republic of",
    "cit_philippines": "Philippines",
    "cit_uk": "United Kingdom",
    "cit_australia": "Australia",
}

# "New Zealand and Australian citizens" peaks at 30 over the whole CLPR series,
# so it is folded into Other rather than drawn as its own band.
_VISA_BANDS: Dict[str, List[str]] = {
    "work": ["Work"],
    "student": ["Student"],
    "visitor": ["Visitor"],
    "residence": ["Residence"],
    "other": ["Other", "New Zealand and Australian citizens"],
}

CIT_NON_NZ = "Non-New Zealand"


# ── Transforms ────────────────────────────────────────────────────────────────


def _rolling(frame: pd.DataFrame) -> pd.DataFrame:
    """Rolling 12-month sum, sorted by month and trimmed to the display window."""
    return (
        frame.sort_index()
        .rolling(ROLLING_WINDOW, min_periods=ROLLING_WINDOW)
        .sum()
        .dropna(how="all")
        .loc[START:]
    )


def _flows(df: pd.DataFrame) -> pd.DataFrame:
    """Chart 1 — non-NZ arrivals, departures (negative) and net migration."""
    wide = (
        df[(df["Citizenship"] == CIT_NON_NZ) & (df["Direction"].isin(["Arrivals", "Departures"]))]
        .pivot_table(index="Month", columns="Direction", values="Count")
    )
    out = _rolling(wide)
    return pd.DataFrame(
        {
            "flow_arrivals": out["Arrivals"],
            "flow_departures": -out["Departures"],
            "flow_net": out["Arrivals"] - out["Departures"],
        }
    )


def _age_arrivals(df_age: pd.DataFrame) -> pd.DataFrame:
    """Chart 2 — arrivals by binned age group, all citizenships."""
    age_map = {age: key for key, ages in _AGE_BINS.items() for age in ages}
    d = df_age[
        (df_age["Sex"].str.lower() == "total")
        & (df_age["Direction"] == "Arrivals")
        & (df_age["Age Group"] != "Total All Ages")
    ].copy()
    d["Bin"] = d["Age Group"].map(age_map)
    if d["Bin"].isna().any():
        missing = sorted(d.loc[d["Bin"].isna(), "Age Group"].unique())
        raise ValueError("Unmapped age groups: " + ", ".join(missing))

    wide = d.pivot_table(index="Month", columns="Bin", values="Count", aggfunc="sum")
    return _rolling(wide)[list(_AGE_BINS)]


def _nationality(df: pd.DataFrame) -> pd.DataFrame:
    """Chart 3 — non-NZ arrivals for the top five source countries, plus Other.

    `cit_other` is the non-NZ total minus the five named countries, so the stack
    sums to total non-NZ arrivals. Taking the residual this way sidesteps the
    region aggregates (Asia, Europe, ...) that sit alongside countries in the
    raw Stats NZ table.
    """
    arrivals = df[df["Direction"] == "Arrivals"]
    wide = arrivals.pivot_table(index="Month", columns="Citizenship", values="Count")

    missing = [c for c in list(_COUNTRIES.values()) + [CIT_NON_NZ] if c not in wide.columns]
    if missing:
        raise ValueError("Missing citizenships in source data: " + ", ".join(missing))

    named = pd.DataFrame({key: wide[name] for key, name in _COUNTRIES.items()})
    named["cit_other"] = wide[CIT_NON_NZ] - named.sum(axis=1)
    return _rolling(named)


def _clpr_visa(df_clpr: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Charts 4 and 5 — CLPR arrivals split into five visa bands."""
    d = df_clpr[(df_clpr["Direction"] == "Arrivals") & (df_clpr["Visa"] != "TOTAL")].copy()
    visa_map = {visa: band for band, visas in _VISA_BANDS.items() for visa in visas}
    d["Band"] = d["Visa"].map(visa_map)
    if d["Band"].isna().any():
        missing = sorted(d.loc[d["Band"].isna(), "Visa"].unique())
        raise ValueError("Unmapped visa types: " + ", ".join(missing))

    wide = d.pivot_table(index="Month", columns="Band", values="Count", aggfunc="sum")
    out = _rolling(wide)[list(_VISA_BANDS)]
    return out.rename(columns={band: prefix + band for band in _VISA_BANDS})


def _records(wide: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert the wide frame to compact JSON records, oldest first."""
    return [
        {"month": month.strftime("%Y-%m"),
         **{key: int(round(float(value))) for key, value in row.items()}}
        for month, row in wide.iterrows()
    ]


# ── Narrative ─────────────────────────────────────────────────────────────────


def _month_label(month: pd.Timestamp) -> str:
    """'2023-10' -> 'October 2023'."""
    return month.strftime("%B %Y")


def _steps(wide: pd.DataFrame) -> List[Dict[str, Any]]:
    """The nine scroll steps, with every figure read from the data.

    `chart` names the entry in CHARTS to draw; `highlight` lists the bands the
    commentary is about, which stay solid while the rest fade back.
    """
    latest = wide.index[-1]
    latest_label = _month_label(latest)
    last = wide.loc[latest]

    # Chart 1 — how far arrivals moved against how little departures did.
    arr = wide["flow_arrivals"]
    dep = -wide["flow_departures"]
    arr_peak_month = arr.idxmax()

    # Chart 2 — age shares now, and where the 30s-40s share peaked.
    age_keys = CHARTS["age"]["keys"]
    age_total = wide[age_keys].sum(axis=1)
    age_share = wide[age_keys].div(age_total, axis=0) * 100
    young = last["age_u20"] + last["age_20s"]
    young_share = age_share["age_u20"] + age_share["age_20s"]
    mid_share = age_share["age_30s"] + age_share["age_40s"]
    mid_peak_month = mid_share.idxmax()
    baseline = pd.Timestamp("2019-03-01")

    # Chart 3 — the India plus China share of non-NZ arrivals, now against 2005.
    cit_keys = CHARTS["nationality"]["keys"]
    cit_total = wide[cit_keys].sum(axis=1)
    cit_share = wide[cit_keys].div(cit_total, axis=0) * 100
    two_share = cit_share["cit_india"] + cit_share["cit_china"]
    first = wide.index[0]

    # Charts 4 and 5 — visa mix for India and China arrivals.
    india_total = wide[CHARTS["india"]["keys"]].sum(axis=1)
    china_total = wide[CHARTS["china"]["keys"]].sum(axis=1)
    india_share = wide[CHARTS["india"]["keys"]].div(india_total, axis=0) * 100
    china_share = wide[CHARTS["china"]["keys"]].div(china_total, axis=0) * 100
    work_peak_month = wide["in_work"].idxmax()
    cn_work_peak_month = wide["cn_work"].idxmax()

    return [
        {
            "chart": "flows",
            "highlight": [],
            "title": "Two decades of migrant flows",
            "body": (
                "Every point counts the previous 12 months. Arrivals of non-New Zealand "
                "citizens sit above the line, their departures below it, and the white "
                "line is the net difference between the two."
            ),
        },
        {
            "chart": "flows",
            "highlight": ["flow_arrivals"],
            "title": "Arrivals did all the moving",
            "body": (
                f"Arrivals ran from a low of {arr.min():,.0f} to a peak of {arr.max():,.0f} "
                f"in the year to {_month_label(arr_peak_month)}. Departures stayed inside a "
                f"band of {dep.min():,.0f} to {dep.max():,.0f} across the same two decades."
            ),
        },
        {
            "chart": "age",
            "highlight": [],
            "title": "The same arrivals, split by age",
            "body": (
                "Stats NZ publishes the age breakdown for all citizenships together, "
                "so this chart includes returning New Zealanders. The six bands stack "
                "to total arrivals."
            ),
        },
        {
            "chart": "age",
            "highlight": ["age_u20", "age_20s"],
            "title": "People 30 and under carry the intake",
            "body": (
                f"The under-20 and 20s bands together account for "
                f"{young_share.loc[latest]:.0f}% of arrivals in the year to "
                f"{latest_label}, {young:,.0f} people out of {age_total.loc[latest]:,.0f}. "
                f"That share has not fallen below {young_share.min():.0f}% at any point "
                "in two decades."
            ),
        },
        {
            "chart": "age",
            "highlight": ["age_30s", "age_40s"],
            "title": "The 30s and 40s peaked with the surge",
            "body": (
                f"Prime-working-age arrivals reached {mid_share.max():.0f}% of the total "
                f"in the year to {_month_label(mid_peak_month)}, up from "
                f"{mid_share.loc[baseline]:.0f}% in the year to "
                f"{_month_label(baseline)}. They have since settled back to "
                f"{mid_share.loc[latest]:.0f}%."
            ),
        },
        {
            "chart": "nationality",
            "highlight": ["cit_india", "cit_china"],
            "title": "India and China now dominate inflows",
            "body": (
                f"The two countries supplied {last['cit_india'] + last['cit_china']:,.0f} "
                f"of {cit_total.loc[latest]:,.0f} non-NZ arrivals in the year to "
                f"{latest_label}, a combined {two_share.loc[latest]:.0f}%. In "
                f"{_month_label(first)} they accounted for {two_share.loc[first]:.0f}%."
            ),
        },
        {
            "chart": "india",
            "highlight": [],
            "title": "Zoom in on India",
            "body": (
                "These are arrivals whose last permanent residence was India, split by the "
                "visa they held. Watch the axis: the whole chart peaks at "
                f"{india_total.max():,.0f}, against {cit_total.max():,.0f} on the last one."
            ),
        },
        {
            "chart": "india",
            "highlight": ["in_work"],
            "title": "Work visas, not students, powered the surge",
            "body": (
                f"Work visa arrivals peaked at {wide['in_work'].max():,.0f} in the year to "
                f"{_month_label(work_peak_month)}, {india_share['in_work'].max():.0f}% of "
                "all India arrivals, as the Accredited Employer Work Visa replaced "
                f"Essential Skills. The April 2024 reforms cut that band to "
                f"{last['in_work']:,.0f} by {latest_label}."
            ),
        },
        {
            "chart": "china",
            "highlight": ["cn_student"],
            "title": "China is the mirror image",
            "body": (
                f"Student visas make up {china_share['cn_student'].loc[latest]:.0f}% of "
                f"arrivals from China in the year to {latest_label}, "
                f"{last['cn_student']:,.0f} people, and they held their level while work "
                f"visas fell from a peak of {wide['cn_work'].max():,.0f} in the year to "
                f"{_month_label(cn_work_peak_month)} to {last['cn_work']:,.0f}. For India "
                f"the student band covers {india_share['in_student'].loc[latest]:.0f}%."
            ),
        },
    ]


# ── Assemble and write ────────────────────────────────────────────────────────


def build_wide(quiet: bool = False) -> pd.DataFrame:
    """Join all five charts into one month-indexed frame of 24 series."""
    loader = DataLoader(base_path=REPO_ROOT)

    def _load() -> tuple[pd.DataFrame, ...]:
        return (
            loader.load_citizenship_direction(),
            loader.load_direction_age_sex(),
            loader.load_clpr_india_visa(),
            loader.load_clpr_china_visa(),
        )

    if quiet:
        with redirect_stdout(io.StringIO()):
            df_cit, df_age, df_india, df_china = _load()
    else:
        df_cit, df_age, df_india, df_china = _load()

    parts = [
        _flows(df_cit),
        _age_arrivals(df_age),
        _nationality(df_cit),
        _clpr_visa(df_india, "in_"),
        _clpr_visa(df_china, "cn_"),
    ]
    wide = pd.concat(parts, axis=1).dropna()

    expected = list(COLORS)
    missing = [key for key in expected if key not in wide.columns]
    if missing:
        raise ValueError("Series missing from the joined frame: " + ", ".join(missing))
    return wide[expected]


def build_story(quiet: bool = False) -> Dict[str, Any]:
    """Assemble the full story.json contract as a dict."""
    wide = build_wide(quiet=quiet)
    return {
        "meta": {
            "title": TITLE,
            "standfirst": STANDFIRST,
            "byline": BYLINE,
            "sources": SOURCES,
            "notes": NOTES,
            "generated": date.today().isoformat(),
            "unit": f"{ROLLING_WINDOW}-month rolling sum",
            "months": len(wide),
            "start": wide.index[0].strftime("%Y-%m"),
            "end": wide.index[-1].strftime("%Y-%m"),
        },
        "colors": COLORS,
        "labels": LABELS,
        "annotations": {},
        "charts": CHARTS,
        "steps": _steps(wide),
        "series": _records(wide),
    }


def _print_summary(story: Dict[str, Any]) -> None:
    """Per-chart drawn range, so the fixed y-domains can be checked each run.

    Stacked charts are measured on the stack total; the mirrored chart is
    measured on its widest single band in each direction, plus the net line.
    """
    frame = pd.DataFrame(story["series"]).set_index("month")
    print("Chart               drawn min   drawn max   y-domain")
    print("-" * 62)
    for name, chart in CHARTS.items():
        columns = list(chart["keys"]) + ([chart["line"]] if chart.get("line") else [])
        if chart["mode"] == "stack":
            drawn = frame[columns].sum(axis=1)
            low, high = drawn.min(), drawn.max()
        else:
            low, high = frame[columns].min().min(), frame[columns].max().max()
        lo, hi = chart["y"]
        flag = "" if low >= lo and high <= hi else "   <-- OUT OF RANGE"
        print(f"{name:<18}{low:>10,.0f}{high:>12,.0f}   [{lo:,} to {hi:,}]{flag}")


def main() -> None:
    print("Building the NZ migration scrollytelling contract")
    print("-" * 60)

    story = build_story()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(story, indent=1), encoding="utf-8")

    print()
    _print_summary(story)
    print()
    meta = story["meta"]
    print(f"Months: {meta['months']:,} ({meta['start']} to {meta['end']})")
    print(f"Series: {len(story['colors'])}   Steps: {len(story['steps'])}")
    print(f"Wrote {OUT_JSON.relative_to(REPO_ROOT)} "
          f"({OUT_JSON.stat().st_size / 1024:,.0f} KB)")


if __name__ == "__main__":
    main()
