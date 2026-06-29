# MBIE Migration Data Explorer — Reference

URL: https://mbienz.shinyapps.io/migration_data_explorer/
(Shiny app — sessions time out after ~5 min of inactivity; expect disconnects)

## Available datasets

| Code | Name | Notes |
|------|------|-------|
| W1 | Work Decisions | All work visa decisions — the complete picture |
| W3 | Work Occupations | Subset of W1 where occupation was captured (~60% of W1 records) |
| S1 | Student Decisions | Student visa decisions by nationality × institution type |
| S7 | Student First Time | First-time student visa approvals |
| R1 | Residence Decisions | Residence class visa decisions |
| R4 | Residence Occupations | Residence decisions with occupation data |
| R7 | Residence Accepted | Accepted residence applications |
| R8 | Residence On Hand | Residence applications in progress |
| V1 | Visitor Decisions | Visitor visa decisions |
| LP1 | Limited Purpose Decisions | Limited purpose visa decisions |

Datasets downloaded to `data/raw/`:
- `mbie_w3_work_occupations_nationality_skill_level_may_years.csv` — W3, Nationality × Occupation Skill Level × "12-mths to Date (Year Ended May)" — 2017–2026; used in dashboard skill charts
- `mbie_w3_work_occupations_nationality_skill_level.csv` — W3, same dimensions but Financial Year aggregation (superseded by may_years file)
- `mbie_s1_student_decisions_nationality_institution.csv` — S1, Nationality × Institution Type × Financial Year

---

## Dimension hierarchy

### W1 Work Decisions — available variables
Decision Type, Application Substream, Application Criteria, Applicant Type,
Nationality, Age Range, Gender, Branch Location, Agent Type

### W3 Work Occupations — available variables
All W1 variables PLUS: Occupation Standard, Occupation Skill Level, Occupation Code,
Occupation, Occupation Major Group, Occupation Submajor Group,
Labour Market Check, Region, Received Job Offer?

### W1 vs W3
W3 is effectively W1 filtered to records where INZ captured an occupation.
~40% of work visa approvals have no recorded occupation (appear in W1 but not W3, or
appear in W3 as "(not recorded)"). The gap is concentrated in open work right visas
(Working Holiday, Partner of a worker) and some AEWV records post-2022.

---

## Application Substream → Application Criteria hierarchy

Application Substream is the broad policy category; Application Criteria is the
specific visa type/instruction within it.

```
Application Substream    Application Criteria (examples)
─────────────────────────────────────────────────────────────────
Skilled Work             Essential Skills (pre-Jul 2022)
                         Accredited Employer / AEWV (Jul 2022 →)
Working Holiday          Argentina WHS, Austria WHS, Belgium WHS,
                         Brazil WHS, Canada WHS, ... (one per country)
Relationship             Partner of a worker
RSE                      Recognised Seasonal Employer
Other                    Post-study – Open, Job Search, Asylum Seeker,
                         Humanitarian, ASEAN Special Work, ...
```

---

## Where Occupation Skill Level fits

Occupation Skill Level (ANZSCO 1–5) is a separate dimension orthogonal to the
Substream/Criteria hierarchy. It describes the skill level of the JOB, not the visa type.

In practice, W3 data is dominated by the Skilled Work substream (employer-sponsored
visas requiring a specific job offer). Working Holiday and Relationship workers hold
open work rights with no specific occupation captured — they rarely appear in W3.

Skill level is therefore best interpreted as: within employer-sponsored work visas,
what is the skill composition of approved roles.

---

## Key policy context

### Essential Skills (pre-July 2022)
- Application Criteria: "Essential Skills"
- Employer had to pass a Labour Market Test (prove no NZ worker available)
- Time-limited: 1–3 years depending on ANZSCO skill band (A=1-3, B, C)
- Dominated W1 Skilled Work from at least 2015 until mid-2022

### AEWV — Accredited Employer Work Visa (July 2022 →)
- Application Criteria: "Accredited Employer"
- Replaced Essential Skills entirely (blue line drops to ~0, red line surges in W1 chart)
- Employer must be INZ-accredited, but Labour Market Test removed for most roles
- No skill band cap → lower-skill roles became accessible at volume
- April 2024 reforms: reintroduced advertising requirements for lower-skill roles,
  raised wage thresholds
- Explains skill shift in dashboard: India Level 4–5 share rose from ~22% (2015/16)
  to ~56% (2023/24) with structural break at 2022

### RSE — Recognised Seasonal Employment
- Separate substream for seasonal horticultural/agricultural work
- Pacific Island workers predominantly; not employer-accreditation based

### Partner of a worker
- Partners of work visa holders (e.g. AEWV holders) get an open work right
- Application Criteria: "Partner of a worker"
- Volume tracks the stock of primary work visa holders — grew post-2022

### "Partnership" (residence concept)
- Refers to residence class applications for partners of NZ citizens/residents
- Appears in R1 Residence Decisions, NOT in W1 Work Decisions

---

## Application Substream — Application Criteria breakdown (verified)

### Job Search substream (W1)
Contains three Application Criteria:

| Application Criteria | Approved decisions (total series) | Share |
|---|---|---|
| Post-study — Open | 156,519 | 99.3% |
| Silver Fern Job Search | 1,059 | 0.7% |
| Job Search | 3 | ~0% |

The substream is effectively the **Post-study Open work visa** — granted to international students who completed study in NZ and want to stay and look for work. Label as "Post-study open" not "Job Search". Verified by filtering W1 to Application Substream = Job Search and downloading Application Criteria breakdown.

---

## Data quirks

- **"(not recorded)" in Occupation Skill Level**: ~40% of W3 approvals have no
  occupation captured. Exclude when computing skill-level proportions (as done
  in the dashboard) and note in chart subtitle.
- **Financial years**: run Jul–Jun; MBIE labels as "2015/16", "2016/17", etc.
- **Partial years**: labeled e.g. "2024/25 PARTIAL (Jul-May)" or "2025/26 PARTIAL (Jul-May)".
  Filter with `~df["Financial Year"].str.startswith("2025")` to exclude the current
  partial FY (2025/26). The 2024/25 partial year IS included by this filter.
- **Shiny session disconnects**: after ~5 min — download CSV before exploring interactively.
