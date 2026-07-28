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
    data/interim/df_clpr_philippines_visa_*.pkl
    data/raw/mbie_w3_work_occupations_nationality_skill_level_may_years.csv

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
from src.dashboard.stories.regional_map import RegionalMapStory  # noqa: E402

# ── Paths and constants ───────────────────────────────────────────────────────

OUT_JSON = SCROLLY_ROOT / "src" / "data" / "story.json"
OUT_MAPS = SCROLLY_ROOT / "src" / "data" / "maps.json"

ROLLING_WINDOW = 12  # months — annual running total, the standard presentation
START = "2005"       # first year shown on the x-axis

# Geometry lives in a second file rather than story.json: it is two orders of
# magnitude larger than the time series and never read by eye.
ASSETS = REPO_ROOT / "dashboard" / "assets"
COORD_DP = 4  # ~11 m, well under a pixel at either map's scale

# simplify tolerance in degrees, chosen per map scale
MAP_SOURCES: Dict[str, Dict[str, Any]] = {
    "nz": {"path": ASSETS / "nz_ta.geojson", "key": "ta_name_ascii", "tolerance": 0.01},
    "auckland": {"path": ASSETS / "auckland_albs.geojson", "key": "alb_name_ascii", "tolerance": 0.001},
}

# MBIE's occupation-level work visa dataset, same file the Quarto dashboard's
# skill-level charts read (src/dashboard/stories/india_surge.py).
MBIE_SKILL_PATH = (
    REPO_ROOT / "data" / "raw" / "mbie_w3_work_occupations_nationality_skill_level_may_years.csv"
)
_SKILL_LO_LEVELS = ["Skill level 4", "Skill level 5"]  # ANZSCO 4-5, the "lower-skill" cut

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
    "MBIE Migration Data Explorer, W3 — approved work visa decisions by nationality "
    "and occupation skill level, year ended May.",
]

NOTES = [
    "Every series is a rolling 12-month sum, so each point counts the previous year.",
    "Stats NZ does not publish the age breakdown split by citizenship, so the age "
    "chart covers all citizenships. Every other chart is non-New Zealand citizens.",
    "Country of last permanent residence (CLPR) is where a person lived before "
    "arriving, which is a closer match for 'from India' than citizenship alone.",
    "Figures use the 12/16-month rule and the latest months are provisional.",
    "Skill-level figures cover approved work visas where MBIE recorded an "
    "occupation, about 60% of decisions; open work-right holders such as "
    "Working Holiday and Relationship visas are largely excluded. They run on "
    "a year-ended-May calendar, a different measure to the arrivals figures "
    "elsewhere on this page.",
    "'Lower-skill' follows MBIE's ANZSCO skill-level scale: Level 1 is the "
    "highest, typically a bachelor's degree or higher, and Level 5 the "
    "lowest, typically no formal qualification beyond secondary school. This "
    "story counts Levels 4 and 5 combined as lower-skill.",
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
    "age_50_64": "#4FB8C4",
    "age_65p": "#4AA0C2",
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
    # Chart 6 — Philippines CLPR by visa
    "ph_work": _BLUE,
    "ph_student": _YELLOW,
    "ph_visitor": _GREEN,
    "ph_residence": _RED,
    "ph_other": _GREY,
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
    "ph_work": "Work",
    "ph_student": "Student",
    "ph_visitor": "Visitor",
    "ph_residence": "Residence",
    "ph_other": "Other",
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
        "subtitle": "Rolling 12-month sum",
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
    "philippines": {
        "keys": ["ph_work", "ph_student", "ph_visitor", "ph_residence", "ph_other"],
        "mode": "stack",
        "y": [0, 40000],
        "title": "Arrivals by visa type: last permanent residence Philippines",
        "subtitle": "Rolling 12-month sum",
    },
}

# Every chart carries a `kind` so the front end knows which component draws it.
for _chart in CHARTS.values():
    _chart["kind"] = "series"

# ── Map colours ───────────────────────────────────────────────────────────────
# Same family as the age bands, so a bright cell means a lot of people wherever
# it appears. The neutral end sits close to the page background, so a region near
# zero recedes rather than reading as a colour.

_MAP_NEUTRAL = "#2A3038"
_MAP_RED = "#E8705F"
_MAP_STOPS = ["#2C7FA8", "#5CBBAB", "#C8E9A0"]


def _map_scale(lo: float, hi: float) -> Dict[str, List[Any]]:
    """Colour stops for a choropleth, as domain/range arrays for d3.scaleLinear.

    Negative values get their own red arm with the neutral pinned at zero, so the
    colour break always falls on zero rather than mid-range.
    """
    if lo < 0:
        return {
            "domain": [lo, 0, hi * 0.4, hi * 0.7, hi],
            "range": [_MAP_RED, _MAP_NEUTRAL] + _MAP_STOPS,
        }
    return {
        "domain": [0, hi * 0.4, hi * 0.7, hi],
        "range": [_MAP_NEUTRAL] + _MAP_STOPS,
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


# ── Map geometry ──────────────────────────────────────────────────────────────


def _round_ring(ring: List[Any], dp: int) -> List[List[float]] | None:
    """Round a ring's coordinates, dropping points that collapse onto each other."""
    out: List[List[float]] = []
    for x, y in ring:
        point = [round(float(x), dp), round(float(y), dp)]
        if not out or point != out[-1]:
            out.append(point)
    # A ring needs three distinct corners plus the closing point to enclose area.
    return out if len(out) >= 4 else None


def _round_geometry(geom: Dict[str, Any], dp: int) -> Dict[str, Any] | None:
    """Round every ring of a Polygon or MultiPolygon, dropping any that collapse."""
    if geom["type"] == "Polygon":
        rings = [r for r in (_round_ring(r, dp) for r in geom["coordinates"]) if r]
        return {"type": "Polygon", "coordinates": rings} if rings else None

    polygons = []
    for polygon in geom["coordinates"]:
        rings = [r for r in (_round_ring(r, dp) for r in polygon) if r]
        if rings:
            polygons.append(rings)
    return {"type": "MultiPolygon", "coordinates": polygons} if polygons else None


def _clean_geometry(geometry: Any, tolerance: float) -> Any:
    """Drop sub-pixel islands and force clockwise winding on every polygon part.

    Two traps, both of which make d3-geo read a shape as the whole globe rather
    than as a region, at which point fitExtent scales the planet into the frame
    and every real area collapses to a pixel or two:

    1. Winding. d3-geo treats a spherical polygon's interior as the side to the
       right of the ring, which is the opposite of GeoJSON RFC 7946. Stats NZ
       shapefiles happen to use the convention d3 wants, but simplification can
       flip an individual part, so it is worth pinning rather than assuming.
       Plotly draws in the plane and never cares, which is why the Quarto
       dashboard renders these same files without complaint.
    2. Slivers. Whangarei ships 74 parts, most of them tiny offshore islands.
       Simplifying at this tolerance collapses the smallest into degenerate rings
       whose winding is meaningless, and one of those was enough to break the
       whole map.
    """
    from shapely.geometry import MultiPolygon
    from shapely.geometry.polygon import orient

    # An island smaller than a quarter of the simplify tolerance squared cannot
    # register at the scale this map is drawn at.
    min_area = (tolerance ** 2) / 4

    if geometry.geom_type == "Polygon":
        return orient(geometry, sign=-1.0)
    if geometry.geom_type == "MultiPolygon":
        parts = [orient(p, sign=-1.0) for p in geometry.geoms if p.area >= min_area]
        # Never return an empty geometry: keep the largest part if all look small.
        if not parts:
            largest = max(geometry.geoms, key=lambda p: p.area)
            parts = [orient(largest, sign=-1.0)]
        return MultiPolygon(parts)
    return geometry


def _load_map(name: str) -> Dict[str, Any]:
    """Read one GeoJSON asset, simplify it and strip it to a single join key.

    The dashboard's assets carry 17 decimal places and properties the map does not
    need. Simplifying and rounding takes the pair from 1.1 MB to under 300 KB with
    no visible change at these scales.
    """
    import geopandas as gpd  # imported here: only the map step needs it

    source = MAP_SOURCES[name]
    frame = gpd.read_file(source["path"])
    tolerance = source["tolerance"]
    frame["geometry"] = frame.geometry.simplify(tolerance).apply(
        lambda g: _clean_geometry(g, tolerance)
    )

    features = []
    dropped = []
    for _, row in frame.iterrows():
        geometry = _round_geometry(row.geometry.__geo_interface__, COORD_DP)
        if geometry is None:
            dropped.append(row[source["key"]])
            continue
        features.append({
            "type": "Feature",
            "properties": {"key": row[source["key"]]},
            "geometry": geometry,
        })
    if dropped:
        print("  [maps] " + name + ": dropped after simplify: " + ", ".join(dropped))
    return {"type": "FeatureCollection", "features": features}


# ── Map data ──────────────────────────────────────────────────────────────────


def _shorten(name: str) -> str:
    """Trim TA suffixes so annotation labels stay narrow."""
    for suffix in (" District", " City", " Region"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _nz_map_values() -> pd.DataFrame:
    """Net international migration per 1,000 residents by territorial authority."""
    net_by_ta, pop_by_ta = RegionalMapStory._load_subnational()
    frame = RegionalMapStory._build_ta_df(net_by_ta, pop_by_ta)
    frame["key"] = frame["ta_name"]
    frame["label"] = frame["ta_name"].apply(_shorten)
    return frame[["key", "label", "net", "value_per1k"]]


def _auckland_map_values() -> pd.DataFrame:
    """The same measure for Auckland local board areas."""
    frame = RegionalMapStory._load_albs()
    return frame.rename(columns={"alb_name_ascii": "key", "display_name": "label"})[
        ["key", "label", "net", "value_per1k"]
    ]


def _drop_unvalued(map_name: str, geometry: Dict[str, Any], values: pd.DataFrame) -> None:
    """Remove features with no value, in place.

    Not just tidiness. The TA file carries an "Area Outside Territorial Authority"
    polygon covering the whole EEZ whose rings wind the wrong way, so d3-geo reads
    it as the entire sphere minus New Zealand. Left in, it fills the frame and
    fitExtent scales the world into the box, leaving the real authorities a couple
    of pixels wide.
    """
    keys = set(values["key"])
    keep = [f for f in geometry["features"] if f["properties"]["key"] in keys]
    dropped = sorted(
        f["properties"]["key"] for f in geometry["features"] if f["properties"]["key"] not in keys
    )
    if dropped:
        print("  [maps] " + map_name + ": dropped, no value: " + ", ".join(dropped))
    geometry["features"] = keep


def _map_chart(
    map_name: str,
    values: pd.DataFrame,
    geometry: Dict[str, Any],
    title: str,
    subtitle: str,
    fit_exclude: List[str] | None = None,
    fit_bbox: List[List[float]] | None = None,
    align: str = "center",
) -> Dict[str, Any]:
    """Assemble a map chart definition, warning about any join misses."""
    _drop_unvalued(map_name, geometry, values)

    keys_in_geometry = {f["properties"]["key"] for f in geometry["features"]}
    unmatched = sorted(set(values["key"]) - keys_in_geometry)
    if unmatched:
        print("  [maps] " + map_name + ": no geometry for " + ", ".join(unmatched))

    lo = float(values["value_per1k"].min())
    hi = float(values["value_per1k"].max())
    return {
        "kind": "map",
        "map": map_name,
        "title": title,
        "subtitle": subtitle,
        "scale": _map_scale(lo, hi),
        "fitExclude": fit_exclude or [],
        "fitBBox": fit_bbox,
        "align": align,
        "values": {
            row["key"]: {
                "label": row["label"],
                "per1k": round(float(row["value_per1k"]), 1),
                "net": int(round(float(row["net"]))),
            }
            for _, row in values.iterrows()
        },
    }


def _top_keys(values: pd.DataFrame, count: int) -> List[str]:
    """The `count` areas with the highest per-1,000 rate, highest first."""
    return (
        values.sort_values("value_per1k", ascending=False)
        .head(count)["key"]
        .tolist()
    )


def _ordinal(n: int) -> str:
    """1 -> '1st', 7 -> '7th'."""
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}" + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


# ── Narrative ─────────────────────────────────────────────────────────────────


def _month_label(month: pd.Timestamp) -> str:
    """'2023-10' -> 'October 2023'."""
    return month.strftime("%B %Y")


def _work_visa_lo_skill_share(mbie: pd.DataFrame, nationality: str) -> pd.Series:
    """Lower-skill (ANZSCO 4-5) share of approved work visas, by year ended May.

    Indexed by 'Year Ended May' (e.g. '2026'). Records with no occupation
    captured - about 40% of approvals, mostly open work-right holders such as
    Working Holiday and Relationship visas - are excluded from the total,
    matching the Quarto dashboard's skill-level charts.
    """
    d = mbie[
        (mbie["Nationality"] == nationality)
        & (mbie["Decision Type"] == "Approved")
        & (mbie["Occupation Skill Level"] != "(not recorded)")
        & (mbie["Year Ended May"] != "2016 PARTIAL (Jul-May)")
    ]
    pivot = d.groupby(["Year Ended May", "Occupation Skill Level"])["Count"].sum().unstack(fill_value=0)
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    lo_cols = [c for c in _SKILL_LO_LEVELS if c in pct.columns]
    return pct[lo_cols].sum(axis=1)


def _map_steps(nz: pd.DataFrame, akl: pd.DataFrame) -> List[Dict[str, Any]]:
    """The four map steps. `highlight` names the areas to colour and annotate."""
    nz_sorted = nz.sort_values("value_per1k", ascending=False)
    akl_sorted = akl.sort_values("value_per1k", ascending=False)
    nz_top = nz_sorted.head(5)
    akl_top = akl_sorted.head(3)
    akl_low = akl_sorted.iloc[-1]
    nz_negative = int((nz["value_per1k"] < 0).sum())

    # The top five by rate are all small places, so the biggest destination in the
    # country never appears among them. Naming it alongside is the whole point of
    # this step: it is where the rate and the volume stories part company.
    biggest = nz.loc[nz["net"].idxmax()]
    biggest_rank = int(nz_sorted["key"].tolist().index(biggest["key"])) + 1
    biggest_share = biggest["net"] / nz["net"].sum() * 100
    nz_highlight = _top_keys(nz, 5)
    if biggest["key"] not in nz_highlight:
        nz_highlight.append(biggest["key"])

    return [
        {
            "chart": "nz-map",
            "highlight": [],
            "title": "Where they actually land",
            "body": (
                "Net international migration per 1,000 residents by territorial "
                f"authority, over the three years ended June 2025. Rates run from "
                f"{nz['value_per1k'].min():.1f} to {nz['value_per1k'].max():.1f}, and "
                f"{nz_negative} of {len(nz)} authorities recorded a net outflow."
            ),
        },
        {
            "chart": "nz-map",
            "highlight": nz_highlight,
            "title": "The highest rates are not the biggest places",
            "body": (
                f"{nz_top.iloc[0]['label']} leads at "
                f"{nz_top.iloc[0]['value_per1k']:.1f} per 1,000, but that is only "
                f"{nz_top.iloc[0]['net']:,.0f} people. {biggest['label']} sits "
                f"{_ordinal(biggest_rank)} on the rate at "
                f"{biggest['value_per1k']:.1f} and takes {biggest['net']:,.0f}, "
                f"{biggest_share:.0f}% of the national total."
            ),
        },
        {
            "chart": "akl-map",
            "highlight": [],
            "title": "Auckland is not one place either",
            "body": (
                "The same measure across Auckland's local board areas. The spread "
                f"inside the city, {akl_low['value_per1k']:.1f} to "
                f"{akl_sorted.iloc[0]['value_per1k']:.1f} per 1,000, is wider than "
                "the spread across the country as a whole."
            ),
        },
        {
            "chart": "akl-map",
            "highlight": _top_keys(akl, 3),
            "title": "South and central Auckland absorb the most",
            "body": (
                f"{akl_top.iloc[0]['label']} took {akl_top.iloc[0]['net']:,.0f} people, "
                f"{akl_top.iloc[0]['value_per1k']:.0f} per 1,000 residents, against "
                f"{akl_low['value_per1k']:.1f} in {akl_low['label']} at the other end "
                "of the city."
            ),
        },
    ]


def _steps(wide: pd.DataFrame) -> List[Dict[str, Any]]:
    """The eleven time-series scroll steps, with every figure read from the data.

    `chart` names the entry in CHARTS to draw; `highlight` lists the bands the
    commentary is about, which stay solid while the rest fade back.
    """
    latest = wide.index[-1]
    latest_label = _month_label(latest)
    last = wide.loc[latest]

    # Chart 1 — how far arrivals moved against how little departures did.
    arr = wide["flow_arrivals"]
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

    # Chart 3 — the India, China and Philippines share of non-NZ arrivals, now
    # against 2005.
    cit_keys = CHARTS["nationality"]["keys"]
    cit_total = wide[cit_keys].sum(axis=1)
    cit_share = wide[cit_keys].div(cit_total, axis=0) * 100
    three_share = cit_share["cit_india"] + cit_share["cit_china"] + cit_share["cit_philippines"]
    first = wide.index[0]

    # Charts 4-6 — visa mix for India, China and Philippines arrivals.
    india_total = wide[CHARTS["india"]["keys"]].sum(axis=1)
    china_total = wide[CHARTS["china"]["keys"]].sum(axis=1)
    philippines_total = wide[CHARTS["philippines"]["keys"]].sum(axis=1)
    india_share = wide[CHARTS["india"]["keys"]].div(india_total, axis=0) * 100
    china_share = wide[CHARTS["china"]["keys"]].div(china_total, axis=0) * 100
    philippines_share = wide[CHARTS["philippines"]["keys"]].div(philippines_total, axis=0) * 100
    work_peak_month = wide["in_work"].idxmax()
    # The Philippines chart's own peak, not a fixed date: work and residence
    # visas grew in lockstep from the border's August 2022 reopening to here.
    ph_peak_month = philippines_total.idxmax()
    ph_reopen = pd.Timestamp("2022-08-01")

    # Skill level of approved work visas, MBIE's occupation dataset rather than
    # Stats NZ arrivals - a different measure (decisions, not people arriving)
    # on a different calendar (year ended May), so its own local variable names.
    mbie = pd.read_csv(MBIE_SKILL_PATH)
    in_lo_skill = _work_visa_lo_skill_share(mbie, "India")
    cn_lo_skill = _work_visa_lo_skill_share(mbie, "China")
    ph_lo_skill = _work_visa_lo_skill_share(mbie, "Philippines")
    skill_latest = in_lo_skill.index[-1]  # '2026' - same for every country

    return [
        {
            "chart": "flows",
            "highlight": [],
            "title": "Two decades of migrant flows",
            "body": (
                "Arrivals of non-New Zealand citizens sit above the line, their "
                "departures below it, and the white line is the net difference "
                "between the two."
            ),
        },
        {
            "chart": "flows",
            "highlight": ["flow_arrivals"],
            "title": "Arrivals did all the moving",
            "body": (
                f"Arrivals drive the cycles, hitting a low of {arr.min():,.0f} as "
                f"borders closed to a peak of {arr.max():,.0f} in the year to "
                f"{_month_label(arr_peak_month)}."
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
            "title": "The 30s and 40s peaked with the post-Covid surge",
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
            "highlight": [],
            "title": "Three names beyond India and China",
            "body": (
                f"The UK and Australia are named because they were the two largest "
                f"non-NZ sources in {_month_label(first)}, at "
                f"{cit_share['cit_uk'].loc[first]:.0f}% and "
                f"{cit_share['cit_australia'].loc[first]:.0f}% of arrivals. The "
                f"Philippines is named too: from {cit_share['cit_philippines'].loc[first]:.1f}% "
                f"back then it has grown to {cit_share['cit_philippines'].loc[latest]:.0f}%, "
                "now bigger than the UK or Australia on their own."
            ),
        },
        {
            "chart": "nationality",
            "highlight": ["cit_india", "cit_china", "cit_philippines"],
            "title": "India, China and the Philippines now dominate inflows",
            "body": (
                f"The three countries supplied "
                f"{last['cit_india'] + last['cit_china'] + last['cit_philippines']:,.0f} "
                f"of {cit_total.loc[latest]:,.0f} non-NZ arrivals in the year to "
                f"{latest_label}, a combined {three_share.loc[latest]:.0f}%. In "
                f"{_month_label(first)} they accounted for {three_share.loc[first]:.0f}%."
            ),
        },
        {
            "chart": "india",
            "highlight": [],
            "title": "Zooming in on India",
            "body": (
                "These are arrivals whose last permanent residence was India, split by the "
                "visa they held. Arrivals from India peaked at "
                f"{india_total.max():,.0f}, against {cit_total.max():,.0f} from other "
                "countries."
            ),
        },
        {
            "chart": "india",
            "highlight": ["in_work"],
            "title": "Work visas powered the surge",
            "body": (
                f"Work visa arrivals peaked at {wide['in_work'].max():,.0f} in the year to "
                f"{_month_label(work_peak_month)}, {india_share['in_work'].max():.0f}% of "
                "all India arrivals, as the Accredited Employer Work Visa replaced "
                f"Essential Skills. The April 2024 reforms cut that band to "
                f"{last['in_work']:,.0f} by {latest_label}, and shifted its skill mix too: "
                f"the lower-skill share peaked at {in_lo_skill.max():.0f}% in "
                f"{in_lo_skill.idxmax()} before falling back to "
                f"{in_lo_skill.loc[skill_latest]:.0f}% in {skill_latest}, according to MBIE "
                "data."
            ),
        },
        {
            "chart": "philippines",
            "highlight": ["ph_work", "ph_residence"],
            "title": "Work and residence visas powered the surge",
            "body": (
                f"Once the border reopened in {_month_label(ph_reopen)}, work and residence "
                f"visas grew almost in lockstep, reaching "
                f"{philippines_share['ph_work'].loc[ph_peak_month]:.0f}% and "
                f"{philippines_share['ph_residence'].loc[ph_peak_month]:.0f}% of "
                f"{philippines_total.max():,.0f} arrivals by {_month_label(ph_peak_month)}. "
                f"Visitor visas are now the largest band, at "
                f"{philippines_share['ph_visitor'].loc[latest]:.0f}%. Work visa holders have "
                f"a similar share of low-skilled visas as India: "
                f"{ph_lo_skill.loc[skill_latest]:.0f}% in {skill_latest}."
            ),
        },
        {
            "chart": "china",
            "highlight": ["cn_student"],
            "title": "China is the mirror image",
            "body": (
                f"Student visas make up {china_share['cn_student'].loc[latest]:.0f}% of "
                f"China's arrivals ({last['cn_student']:,.0f} people) while work visas fell "
                f"from a peak of {wide['cn_work'].max():,.0f} to {last['cn_work']:,.0f}. For "
                f"India the student share is {india_share['in_student'].loc[latest]:.0f}%. "
                f"China's work visas stay the most skilled: its lower-skill share was just "
                f"{cn_lo_skill.loc[skill_latest]:.0f}% in {skill_latest}, against "
                f"{in_lo_skill.loc[skill_latest]:.0f}% for India and "
                f"{ph_lo_skill.loc[skill_latest]:.0f}% for the Philippines."
            ),
        },
    ]


# ── Assemble and write ────────────────────────────────────────────────────────


def build_wide(quiet: bool = False) -> pd.DataFrame:
    """Join all six charts into one month-indexed frame of 30 series."""
    loader = DataLoader(base_path=REPO_ROOT)

    def _load() -> tuple[pd.DataFrame, ...]:
        return (
            loader.load_citizenship_direction(),
            loader.load_direction_age_sex(),
            loader.load_clpr_india_visa(),
            loader.load_clpr_china_visa(),
            loader.load_clpr_philippines_visa(),
        )

    if quiet:
        with redirect_stdout(io.StringIO()):
            df_cit, df_age, df_india, df_china, df_philippines = _load()
    else:
        df_cit, df_age, df_india, df_china, df_philippines = _load()

    parts = [
        _flows(df_cit),
        _age_arrivals(df_age),
        _nationality(df_cit),
        _clpr_visa(df_india, "in_"),
        _clpr_visa(df_china, "cn_"),
        _clpr_visa(df_philippines, "ph_"),
    ]
    wide = pd.concat(parts, axis=1).dropna()

    expected = list(COLORS)
    missing = [key for key in expected if key not in wide.columns]
    if missing:
        raise ValueError("Series missing from the joined frame: " + ", ".join(missing))
    return wide[expected]


def build_maps() -> tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """Build the two map charts, their geometry, and the four map steps.

    Returns (geometries, chart definitions, steps). Geometry is written to its own
    file; the chart definitions carry only the values and colour scale.
    """
    geometries = {name: _load_map(name) for name in MAP_SOURCES}
    nz_values = _nz_map_values()
    akl_values = _auckland_map_values()

    charts = {
        "nz-map": _map_chart(
            "nz", nz_values, geometries["nz"],
            title="Net migration per 1,000 residents by territorial authority",
            subtitle="Three years ended June 2025",
        ),
        "akl-map": _map_chart(
            "auckland", akl_values, geometries["auckland"],
            title="Net migration per 1,000 residents: Auckland local boards",
            subtitle="Three years ended June 2025",
            # Great Barrier sits 60 km offshore and Rodney runs far north, so
            # fitting to the features leaves the urban boards too small to read.
            # Frame the city instead, cropping the top 25% off the Quarto
            # dashboard's window (little more than open water and rural Rodney),
            # and let the rest fall outside the clip.
            fit_bbox=[[174.4, -37.15], [175.05, -36.55]],
            # Every board worth naming sits in the eastern half, so all three
            # labels go right. Centring the frame would leave a hole on the left
            # and crowd the labels against the right edge.
            align="left",
        ),
    }
    return geometries, charts, _map_steps(nz_values, akl_values)


def build_story(quiet: bool = False) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Assemble the story.json contract and the map geometry alongside it."""
    wide = build_wide(quiet=quiet)
    geometries, map_charts, map_steps = build_maps()

    charts = {**CHARTS, **map_charts}
    story = {
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
            "last_update": _month_label(wide.index[-1]),
        },
        "colors": COLORS,
        "labels": LABELS,
        "annotations": {},
        "charts": charts,
        "steps": _steps(wide) + map_steps,
        "series": _records(wide),
    }
    return story, geometries


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


def _print_map_summary(story: Dict[str, Any], geometries: Dict[str, Any]) -> None:
    """Per-map feature count, value coverage and rate range."""
    print()
    print("Map            features  valued   per-1k range")
    print("-" * 62)
    for name, chart in story["charts"].items():
        if chart.get("kind") != "map":
            continue
        rates = [v["per1k"] for v in chart["values"].values()]
        features = len(geometries[chart["map"]]["features"])
        print(f"{name:<15}{features:>8}{len(rates):>9}   "
              f"{min(rates):>6.1f} to {max(rates):<6.1f}")


def main() -> None:
    print("Building the NZ migration scrollytelling contract")
    print("-" * 60)

    story, geometries = build_story()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(story, indent=1), encoding="utf-8")
    OUT_MAPS.write_text(json.dumps(geometries, separators=(",", ":")), encoding="utf-8")

    print()
    _print_summary(story)
    _print_map_summary(story, geometries)
    print()
    meta = story["meta"]
    print(f"Months: {meta['months']:,} ({meta['start']} to {meta['end']})")
    print(f"Series: {len(story['colors'])}   Charts: {len(story['charts'])}   "
          f"Steps: {len(story['steps'])}")
    print(f"Wrote {OUT_JSON.relative_to(REPO_ROOT)} "
          f"({OUT_JSON.stat().st_size / 1024:,.0f} KB)")
    print(f"Wrote {OUT_MAPS.relative_to(REPO_ROOT)} "
          f"({OUT_MAPS.stat().st_size / 1024:,.0f} KB)")


if __name__ == "__main__":
    main()
