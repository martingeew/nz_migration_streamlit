# NZ Migration Claims Dashboard — Build Plan

**Purpose:** Interactive data dashboard stress-testing 12 politically active NZ immigration claims against public datasets, timed for the 2026 election cycle.

**Stack assumption:** Python + Plotly/Dash or Streamlit. Each issue maps to one panel/tab. Data ingested via direct download, requests, or Selenium where needed.

---

## Priority Scoring Framework

Each issue scored across three axes (1–5 each):
- **Data ease** — how accessible, structured, and scriptable the source is
- **Update frequency** — how often new data drops (monthly beats annual)
- **Journalism impact** — how politically live and shareable the finding is

Issues ranked by combined score descending.

---

## Issue 1 — The Brain Drain (Kiwi Exodus)

**Priority score: 15/15**
Data ease: 5 | Update frequency: 5 | Journalism impact: 5

### The Claim
New Zealanders are leaving in historically unprecedented numbers due to domestic economic conditions. Political source: Social Development Minister Louise Upston warned the economy in recession could see the "best and brightest" leave; NZ First's Peters frames it as proof of failed domestic policy.

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| Stats NZ — International Travel and Migration | https://www.stats.govt.nz/topics/migration | CSV via Aotearoa Data Explorer | Monthly (~6 week lag) |
| Stats NZ — Infoshare table ITM | https://infoshare.stats.govt.nz/ > Population > International Travel and Migration | CSV download | Monthly |

### Variables to Extract
- `citizenship = NZ citizen` — filter all other citizenship groups out
- `direction = departures` and `direction = arrivals`
- Calculate: **net NZ citizen migration = arrivals minus departures**, rolling 12-month
- Age band breakdown: isolate 25–49 cohort separately from under-25 (the OE cohort)
- Destination country: isolate Australia vs. rest of world

### Key Visualisations
1. Rolling 12-month net NZ citizen migration — line chart with historical average band shaded
2. Age-band departure heatmap: which age groups are above historical norms
3. Australia vs. rest-of-world split over time

### Stress-Test Logic
- Plot against historical average (pre-2020) as baseline
- Gluckman et al. (2025) argue current rates are not unprecedented when viewed against 1970s–2000s peaks — add this as a reference line
- If the claim is "unprecedented," the data either confirms or refutes it at the specific age-cohort level

### Notes
Stats NZ Infoshare allows direct CSV export with filters applied. No API key needed. This is the single easiest, highest-value dataset in the project.

---

## Issue 2 — Mass Migration vs. Housing Strain

**Priority score: 14/15**
Data ease: 5 | Update frequency: 5 | Journalism impact: 4

### The Claim
High immigration volumes are the primary driver of housing shortages and rental price spikes. Political source: Erica Stanford's April 2024 Beehive press release stated net migration of ~140,000 in 2023 was "putting completely unsustainable pressure on key services and infrastructure." https://www.beehive.govt.nz/release/government-responds-unsustainable-net-migration

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| Stats NZ — International Migration (total net) | https://infoshare.stats.govt.nz/ | CSV | Monthly |
| Stats NZ — Building Consents Issued | https://www.stats.govt.nz/topics/building-consents | CSV | Monthly |
| MBIE — Tenancy Services Rent Data | https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/ | CSV | Quarterly |

### Variables to Extract
- Total net migration (all citizenships) — annual rolling
- New dwelling consents issued (residential) — annual rolling
- Median rent by region — quarterly

### Key Visualisations
1. Dual-axis line chart: net migration (left axis) vs. new dwelling consents (right axis), 10-year window
2. Lagged correlation plot: does consent supply respond to migration with a 12–18 month lag?
3. Regional breakdown: Auckland vs. rest of NZ on both axes

### Stress-Test Logic
- If migration spikes while consents plateau or fall, structural strain claim is supported
- Also pull consent data from pre-2017 (when migration was also high) to check if the relationship held then too
- Confound to flag: consents fell sharply in 2023–24 due to high interest rates — not immigration. The dashboard should isolate this with a recession/OCR overlay

### Notes
Both datasets update monthly on Infoshare. Simple two-series download. Highest confidence, lowest build effort.

---

## Issue 3 — Skill Level of Indian Arrivals

**Priority score: 13/15**
Data ease: 4 | Update frequency: 4 | Journalism impact: 5

### The Claim
The visa system is being flooded with lower-skilled arrivals under the guise of "essential skills," with India singled out as the primary source country. Political source: Peters' State of the Nation, March 2026 — "applications to migrate from India will significantly increase across the board — including uncapped numbers of students with the right to work which will take Kiwi jobs off Kiwis." https://www.nzfirst.nz/power_to_the_people_sotn_2026

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| INZ — Work Visa Approvals Dataset | https://www.immigration.govt.nz/about-us/research-and-statistics/research-reports/work-visa-data | Excel/CSV | Annual (fiscal year) |
| INZ — AEWV Key Statistics | https://www.immigration.govt.nz/about-us/news-centre/accredited-employer-work-visa-aewv-key-information-and-statistics | HTML table + PDF | Monthly |
| INZ — Skilled Migrant Category Fortnightly Selection Stats | https://www.immigration.govt.nz/documents/smc-fortnightly-selection/ | PDF | Fortnightly |

### Variables to Extract
- Filter: `nationality = India`
- Cross-tab: `ANZSCO skill level` (1–5) × `nationality`
- Calculate: Level 1–3 share vs. Level 4–5 share for India vs. all other nationalities combined
- Time series: this ratio over the last 5 fiscal years

### Key Visualisations
1. Stacked bar: India ANZSCO level distribution vs. all-nationalities average, side by side
2. Time series: % of Indian AEWV holders at Level 4–5, with AEWV policy change dates marked
3. Scatter: source country vs. skill level distribution — where does India sit relative to Philippines, South Africa, UK etc.?

### Stress-Test Logic
- The claim implies India skews low-skill vs. other source countries — the ANZSCO cross-tab either confirms or refutes this
- April 2024 AEWV reforms introduced English language and skills requirements specifically targeting Level 4–5 — check if the India Level 4–5 share dropped post-reform
- SMC fortnightly PDFs show India at ~17% of expression of interest pool — within the skilled pathway, this is a very different picture to AEWV

### Notes
INZ work visa Excel files need column-level parsing. ANZSCO level is usually a separate column from occupation title. SMC PDFs need tabula-py for extraction. Budget extra time for PDF parsing step.

---

## Issue 4 — Systemic Migrant Exploitation under the AEWV

**Priority score: 12/15**
Data ease: 4 | Update frequency: 4 | Journalism impact: 4

### The Claim
Tying a worker's visa to a single accredited employer creates structural exploitation. Political source: Andrew Little (Labour) commissioned the independent review; the Bestwick review (February 2024) found INZ staff were instructed to "do no verification work on low-risk and medium-risk applications." MBIE received 2,107 employer complaints; 145 accreditations revoked as of early 2024.

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| INZ — AEWV Key Statistics (accreditations, revocations, MEPV) | https://www.immigration.govt.nz/about-us/news-centre/accredited-employer-work-visa-aewv-key-information-and-statistics | HTML / PDF | Monthly updates |
| MBIE — Labour Inspectorate Annual Report | https://www.mbie.govt.nz/immigration-and-tourism/immigration/labour-inspectorate/ | PDF | Annual |
| MBIE — Migration Exploitation Data Explorer | https://www.mbie.govt.nz/immigration-and-tourism/immigration/migrant-exploitation/ | Web + downloadable | Quarterly |
| INZ — MEPV approvals | Embedded in AEWV stats page above | HTML table | Monthly |

### Variables to Extract
- Total active AEWV holders (denominator)
- Total active MEPVs (Migrant Exploitation Protection Visas) granted
- Accreditation revocations + suspensions (running total)
- Labour Inspectorate: enforcement actions, prosecutions, fines by year
- Calculate: **MEPV rate = active MEPVs / active AEWVs**

### Key Visualisations
1. MEPV rate over time — line chart with policy milestones marked
2. Enforcement funnel: complaints → investigations → revocations → prosecutions (Sankey or waterfall)
3. Revocation rate by employer size/sector where available

### Stress-Test Logic
- MEPV is a floor estimate (only confirmed exploitation), not a ceiling — frame accordingly
- The revocation rate as % of total accredited employers is the cleanest signal of systemic vs. edge-case exploitation
- Prosecution rate vs. complaint rate is the accountability gap metric

### Notes
MEPV numbers are published in the AEWV stats page but not always in a clean downloadable format — use `requests` + `BeautifulSoup` to scrape the HTML table monthly. The MBIE migration exploitation explorer has a CSV export option.

---

## Issue 5 — The 501 Deportee Pipeline

**Priority score: 12/15**
Data ease: 4 | Update frequency: 3 | Journalism impact: 5

### The Claim
Australia is deporting NZ citizens with criminal records under s501 of the Migration Act, contributing to gang growth and organised crime in NZ. Political source: PM Christopher Luxon, May 2024 — "deportees have been linked to a rise in gang activity in New Zealand and an increase in crime. We regret the decision that Australia has made." https://www.nzherald.co.nz/nz/politics/pm-unsure-if-501-numbers-will-increase-after-australias-rewrite-of-deportation-policy/

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| Australian Dept. of Home Affairs — Character Cancellations | https://www.homeaffairs.gov.au/research-and-statistics/statistics/visa-statistics/live/character-and-general-return | Excel | Annual |
| NZ Police — 501 Deportee Offending Statistics | OIA request or Parliamentary questions (check Hansard) | PDF/OIA | Annual |
| NZ Corrections — Returning Offender data | https://www.corrections.govt.nz/resources/research_and_statistics | PDF | Annual |
| RNZ — Rate of 501 deportations dropping (Oct 2023) | https://www.rnz.co.nz/news/national/501293/ | Article | Reference only |

### Variables to Extract
- Annual 501 deportations to NZ, by year (2015–present)
- Crime type breakdown of deported individuals (Home Affairs publishes this)
- NZ reoffending rate: % of 501s who reoffend in NZ (NZ Police figure: ~50%)
- Monthly rate: pre- vs. post-Direction 110 (2024) comparison

### Key Visualisations
1. Annual 501 deportations to NZ — bar chart with policy change dates annotated
2. Crime type breakdown of the deported cohort (drug, assault, sexual offences etc.)
3. Monthly rate: pre-2023 average vs. post "common sense approach" vs. post-Direction 110

### Stress-Test Logic
- The political claim blurs two issues: (a) the reoffending rate of deportees, and (b) the appropriateness of deporting people with no NZ connection — visualise these separately
- Reoffending rate is ~50% but covers a wide severity range — show the crime-type breakdown to contextualise
- NZ Police gang membership figure: only ~5% of 501s are known gang members — that's the counter-statistic to foreground

### Notes
Australian Home Affairs Excel files are the cleanest data here. NZ Police 501 statistics require OIA or checking recent Parliamentary written questions (search ParlInfo). The Centrist.nz summary cites 21,404 total offences — verify this against primary NZ Police source before publishing.

---

## Issue 6 — Wage Suppression in High-Migration Sectors

**Priority score: 11/15**
Data ease: 4 | Update frequency: 4 | Journalism impact: 3

### The Claim
High immigration in specific sectors is holding down wages for NZ workers. Political source: Labour's explicit 2017 and 2026 election framing — "stop wages being kept low"; also the removal of median wage thresholds from the AEWV in March 2025 prompted concern from Vialto Partners that this "could raise concerns about wage suppression." https://vialtopartners.com/regional-alerts/new-zealand-immigration-potential-immigration-policy-changes

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| Stats NZ — Quarterly Employment Survey (QES) | https://www.stats.govt.nz/topics/employment | CSV via Infoshare | Quarterly |
| MBIE — Work Visa Approvals by Industry (ANZSIC) | https://www.mbie.govt.nz/immigration-and-tourism/immigration/migration-research-and-evaluation/migration-data-explorer/ | Interactive + CSV | Annual |
| MBIE — Labour Market Indicators | https://www.mbie.govt.nz/business-and-employment/employment-and-skills/labour-market-reports-data-and-analysis/ | Excel | Quarterly |
| CPI — RBNZ Inflation data | https://www.rbnz.govt.nz/statistics | CSV | Quarterly |

### Variables to Extract
- Average hourly earnings by industry (ANZSIC division) — QES
- Number of AEWV/work visa approvals by industry — MBIE
- Real wage growth = nominal wage growth minus CPI, by industry
- Identify top 5 industries by migrant intake volume

### Key Visualisations
1. Scatter: migrant intake volume (x) vs. real wage growth (y) by industry — one dot per industry
2. Time series: real wages in top-5 migrant-heavy industries vs. low-migration industries as control
3. Pre/post AEWV median wage removal (March 2025): did wage growth in affected sectors change?

### Stress-Test Logic
- The Productivity Commission 2021 inquiry found "on average, immigration is not driving down wages" — use this as null hypothesis
- Test sector-by-sector: if the aggregate finding holds but specific sectors (aged care, hospitality) diverge, that's the story
- Confound to flag: real wages fell across the economy in 2022–23 due to inflation, not immigration — the dashboard needs CPI deflation applied

### Notes
QES industry breakdown in Infoshare is straightforward. Matching QES ANZSIC codes to MBIE ANZSIC codes requires a lookup table — build this as a reference CSV in the project. Annual cadence on MBIE data means this panel will lag the monthly panels.

---

## Issue 8 — Sector Dependency / Migration as Substitute for Training

**Priority score: 10/15**
Data ease: 3 | Update frequency: 3 | Journalism impact: 4

### The Claim
Employers in aged care, construction, and food processing have become structurally dependent on migrant labour instead of investing in domestic training. Political source: Winston Peters, September 2025 — "We take them in, train them, up-skill them, look after their families, and then they emigrate. How is this an effective immigration policy?" https://www.nzherald.co.nz/nz/politics/immigration-minister-erica-stanford-unveils-two-new-pathways-to-residency-for-skilled-migrants-including-tradies/RNSEREEXPZAANIKRQKYG7QCGME/

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| MBIE — Work Visa Approvals by Industry and Occupation | https://www.mbie.govt.nz/immigration-and-tourism/immigration/migration-data-explorer/ | CSV via explorer | Annual |
| Tertiary Education Commission — Industry Training Activity | https://www.tec.govt.nz/teo/working-with-teos/it/industry-training-data/ | Excel | Annual |
| MBIE — Employer accreditation by sector | Embedded in AEWV stats page | HTML/PDF | Monthly |

### Variables to Extract
- Annual AEWV approvals by ANZSIC industry — focus on: aged care, construction, food processing, hospitality
- Annual vocational/apprenticeship enrolments by field of study from TEC
- Calculate: visa approvals vs. training enrolments ratio, by sector, by year

### Key Visualisations
1. Dual-axis: migrant work visas into sector X (left) vs. apprenticeship enrolments in sector X (right) — 5-year window per sector
2. Small multiples: repeat for aged care, construction, hospitality, food processing
3. Index chart: if 2019 = 100, how has each series moved relative to base?

### Stress-Test Logic
- If visas rise while training enrolments fall in the same sector, substitution is occurring
- The counter-argument is that training pipelines take 3–5 years, so short-term visa dependence is rational — add a lag indicator
- Aged care is the politically most potent case: the Aged Care Association CEO explicitly said the sector relies on migrants

### Notes
TEC data is annual and published in Excel workbooks. The ANZSIC/field-of-study crosswalk to MBIE occupation data requires manual mapping — document this mapping in the project. This is the most labour-intensive panel to build.

---

## Issue 9 — Pacific/RSE Circular vs. Permanent Migration

**Priority score: 9/15**
Data ease: 3 | Update frequency: 3 | Journalism impact: 3

### The Claim
Two competing claims: (a) the RSE scheme is a model of circular migration with near-zero overstay rates, or (b) Pacific workers are being exploited/disadvantaged by high visa fees replacing the old Pacific Programmes. Political source: RNZ January 2026 — NZ quietly axed Pacific Programmes in favour of new Peak Seasonal Visa with $1,540 fee vs. $350 RSE fee. https://www.rnz.co.nz/international/pacific-news/585217/documents-reveal-nz-quietly-axed-pacific-migrant-worker-programme-in-favour-of-high-cost-seasonal-visas

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| INZ — RSE Scheme Statistics | https://www.immigration.govt.nz/about-us/research-and-statistics/statistics/work-statistics/ | Excel | Annual |
| Stats NZ — Overstayer data by nationality and visa type | https://www.immigration.govt.nz/about-us/research-and-statistics/statistics/ | Excel | Annual |
| MFAT — Pacific Labour Mobility Programme | https://www.mfat.govt.nz/en/aid-and-development/labour-mobility | PDF reports | Annual |
| INZ — Pacific Access Category draw results | https://www.immigration.govt.nz/pacific/ | HTML | Per draw |

### Variables to Extract
- Annual RSE worker arrivals by source country, by year
- RSE overstay rate as % of annual arrivals (early data shows <1% — verify current)
- PSV vs. RSE fee comparison (direct from INZ/MFAT Cabinet papers)
- PAC quota utilisation: applications vs. cap by year

### Key Visualisations
1. RSE arrivals by Pacific nation — stacked bar over time, showing expansion to 20,000+
2. RSE overstay rate trend — is the model holding as scale increases?
3. Fee comparison table: PSV vs. RSE vs. Pacific Programmes (static infographic)

### Stress-Test Logic
- If the RSE overstay rate remains below 1%, the circular migration claim is robustly supported
- The policy substitution story (Pacific Programmes → PSV) is a data journalism angle, not a data visualisation — pair the chart with the MFAT Cabinet paper quote
- PAC quota utilisation tells you whether supply matches demand

### Notes
RSE overstay data historically comes from NZ DoL/INZ annual reports — confirm whether the current INZ stats page has a downloadable version. Historical data (pre-2020) may only exist in archived PDF reports.

---

## Issue 10 — Parent Category: Welfare and Pension Drain

**Priority score: 9/15**
Data ease: 3 | Update frequency: 2 | Journalism impact: 4

### The Claim
Allowing migrants to sponsor elderly parents creates an immediate financial burden on the public purse. Political source: Winston Peters has made this claim since at least 2012, when he estimated 22,000 elderly immigrants from non-reciprocal pension agreement countries who "could arrive at 55, not work for a decade, and receive full super and healthcare at 65." The government itself responded with the July 2024 change extending NZ Super residency requirement from 10 to 20 years. https://workandincome.govt.nz/eligibility/seniors/nz-super-and-veterans-pension-residency-changes-2024.html

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| INZ — Parent Resident Visa approvals (annual cap = 2,500) | https://www.immigration.govt.nz/about-us/news-centre/update-to-the-parent-resident-visa-category | HTML | Per draw / Annual |
| MSD — Benefit Fact Sheets | https://www.msd.govt.nz/about-msd-and-our-work/publications-resources/statistics/benefit/ | Excel | Quarterly |
| MSD — Sponsorship Debt Recoveries | OIA request required | OIA | Annual |
| Work and Income — NZ Super residency criteria | https://workandincome.govt.nz/eligibility/seniors/nz-super-and-veterans-pension-residency-changes-2024.html | HTML | Reference |

### Variables to Extract
- Annual Parent Resident Visa approvals vs. 2,500 cap — is the cap always hit?
- MSD benefit uptake by visa type (where available in fact sheets)
- Sponsorship debt recovery data — how much is clawed back from sponsors annually? (OIA required)
- NZ Super: number of recipients who arrived in NZ after age 55 (OIA from MSD)

### Key Visualisations
1. Parent visa approvals vs. annual cap — bar chart showing demand always exceeds supply (waitlist pressure)
2. NZ Super eligibility timeline: before vs. after July 2024 change — infographic showing the window that closed
3. If MSD data available: benefit uptake rate for recently arrived migrants vs. NZ-born population

### Stress-Test Logic
- The 2024 Super residency change from 10 to 20 years is the government's own implicit acknowledgement of the risk — but it also closes the window Peters identified
- The sponsorship debt recovery OIA is the key test: if recoveries are near-zero, the legal guarantee is nominal; if substantial, the system is self-funding
- Without the OIA data, this panel is partially incomplete — flag this honestly on the dashboard

### Notes
File an OIA with MSD for sponsorship debt recoveries before building this panel. Allow 20 working days. In the meantime, build the visa cap utilisation chart as the minimum viable version.

---

## Issue 11 — Employer Accreditation Fraud and AEWV Integrity

**Priority score: 8/15**
Data ease: 2 | Update frequency: 3 | Journalism impact: 3

### The Claim
The AEWV accreditation system is being gamed — fake employers, bought job offers, and unverified checks are compromising border integrity. Political source: the independent Bestwick Review (February 2024) found INZ staff were told to do "no verification work on low-risk and medium-risk applications" and only "quick" checks on high-risk ones; 27,894 applicants processed but only 2 declined accreditation. MBIE received 2,107 complaints. https://www.mbie.govt.nz/about/open-government-and-official-information/release-of-information/independent-review-into-the-accredited-employer-work-visa-aewv/

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| INZ — AEWV stats (accreditations granted, revoked, suspended) | https://www.immigration.govt.nz/about-us/news-centre/accredited-employer-work-visa-aewv-key-information-and-statistics | HTML table | Monthly |
| MBIE — Labour Inspectorate Annual Report | https://www.mbie.govt.nz/immigration-and-tourism/immigration/labour-inspectorate/ | PDF | Annual |
| Te Kawa Mataaho — Bestwick Review (Feb 2024) | https://www.publicservice.govt.nz/system/public-service-commission/publications/independent-review-aewv.pdf | PDF | One-time reference |
| INZ — Post-accreditation check statistics | Embedded in AEWV stats page | HTML | Monthly |

### Variables to Extract
- Total accreditations granted (cumulative)
- Revocations + suspensions (cumulative and annual flow)
- Calculate: **revocation rate = revocations / total accreditations**
- Post-accreditation checks completed vs. employers checked (INZ reports 5,613 checks on 4,246 employers as at late 2024)
- Labour Inspectorate: enforcement actions involving accredited employers

### Key Visualisations
1. Waterfall: accreditations granted → active → suspended → revoked → prosecuted (the accountability funnel)
2. Monthly trend: revocation rate as % of active pool — is it rising or falling post-reform?
3. Post-accreditation check coverage: % of active employers checked annually

### Stress-Test Logic
- If revocation rate is <1% and post-accreditation check coverage is <20% of employers per year, the integrity gap is structural, not anecdotal
- Compare check volume pre-reform (before April 2024) vs. post-reform
- The "only 2 declines from 27,894 applications" statistic from the Bestwick Review is the forensic anchor — this is pre-reform and should be shown as a baseline

### Notes
HTML table scraping of the INZ AEWV stats page is required monthly. The MBIE Labour Inspectorate PDF requires tabula-py or pdfplumber. This panel is primarily retrospective (documenting the known failure) rather than forward-looking.

---

## Issue 12 — Net Fiscal Contribution (The Full Balance Sheet)

**Priority score: 7/15**
Data ease: 2 | Update frequency: 1 | Journalism impact: 4

### The Claim
Migrants are either a net fiscal gain (taxes, labour force participation, consumption) or a net fiscal drain (services consumed, welfare, remittances). This is the macro framing underlying all other claims. Political source: NZ Herald, May 2026 — "immigration ranks as the 12th most pressing issue [in polling], but we saw what happens when you turn off the migration tap — labour shortages, unemployment plunged, and wages soared." https://www.nzherald.co.nz/business/immigration-politics-why-national-and-acts-populist-turn-misreads-data-liam-dann/

### Data Sources

| Source | URL | Format | Cadence |
|--------|-----|--------|---------|
| NZ Productivity Commission — Immigration Inquiry 2021 | https://www.productivitycommission.govt.nz/inquiry/immigration/ | PDF + data appendices | One-time reference |
| MBIE — Migration Trends and Outlook (annual) | https://www.mbie.govt.nz/immigration-and-tourism/immigration/migration-research-and-evaluation/migration-trends/ | PDF + Excel | Annual |
| Stats NZ — National Accounts (GDP contributions) | https://www.stats.govt.nz/topics/national-accounts | CSV | Quarterly |
| RBNZ — Inflation and OCR data (for real wage context) | https://www.rbnz.govt.nz/statistics | CSV | Quarterly |

### Variables to Extract
- Productivity Commission 2021 fiscal impact estimates — use as static benchmark
- MBIE Migration Trends annual report: total migrant population, labour force participation rate, benefit uptake rate
- GDP per capita trend: does it rise or fall with net migration changes?
- Employment rate by visa status (where available in MBIE data)

### Key Visualisations
1. GDP per capita vs. net migration — scatter, annual data points, 15-year window
2. Unemployment rate vs. net migration — same treatment (test whether the 2020–21 "closed border" experiment supports the claims)
3. Static infographic: Productivity Commission's fiscal impact model — income taxes paid vs. services consumed by migrant cohort

### Stress-Test Logic
- The clearest natural experiment is 2020–21 border closure: net migration went negative, unemployment fell to 3.2%, wages surged — but inflation followed and the RBNZ hiked aggressively. The dashboard should show this full sequence
- The fiscal balance is structurally positive for working-age migrants and negative for elderly migrants — this is the finding that splits Parent Category from skilled migrant categories
- Frame as a "the evidence is X, the political claim is Y" comparison rather than a verdict

### Notes
This is the hardest panel to build with live data. The Productivity Commission report is a static PDF — extract the key tables using pdfplumber and hardcode as reference data. The live component is GDP per capita and unemployment rate vs. net migration, which can be automated via Stats NZ Infoshare.

---

## Build Sequence

```
Phase 1 (Weeks 1–2): Core Stats NZ panels
  → Issues 1, 2 (Infoshare CSV automation)
  → Build reusable Stats NZ Infoshare downloader module

Phase 2 (Weeks 3–4): INZ data panels
  → Issue 3 (work visa Excel parsing)
  → Build reusable INZ Excel parser with ANZSCO lookup table

Phase 3 (Weeks 5–6): MBIE/enforcement panels
  → Issues 4, 11 (AEWV stats scraper + Labour Inspectorate PDF)
  → Build reusable HTML table scraper for INZ stats pages

Phase 4 (Weeks 7–8): External source panels
  → Issue 9 (Australian Home Affairs Excel)
  → Issue 6 (QES wage data + MBIE industry crosswalk)

Phase 5 (Weeks 9–10): Annual/static panels
  → Issues 8, 10, 12 (TEC, MSD, Productivity Commission)
  → File OIAs for: MSD sponsorship debt recoveries, NZ Police 501 reoffending breakdown

Phase 6 (Weeks 11–12): Dashboard integration + automation
  → Scheduled refresh jobs for monthly panels (Issues 1, 2, 4, 11)
  → Quarterly refresh for Issues 6, 10, 12
  → Annual refresh for Issues 3, 7, 8, 9
```

---

## Shared Infrastructure Needed

```python
# Modules to build once and reuse across panels
- stats_nz_infoshare.py      # parameterised CSV downloader for Infoshare
- inz_excel_parser.py        # Excel workbook handler with ANZSCO lookup
- inz_html_scraper.py        # BeautifulSoup scraper for INZ stats pages
- mbie_pdf_extractor.py      # pdfplumber wrapper for MBIE annual reports
- aus_home_affairs.py        # Excel downloader for AHA deportation stats
- oia_tracker.md             # log of outstanding OIA requests and expected dates
```

---

## OIA Requests to File Now

| Target agency | Information requested | Priority |
|--------------|----------------------|---------|
| MSD | Sponsorship debt recovery amounts, Parent Category, annual 2018–2025 | High (Issue 10) |
| NZ Police | 501 deportee reoffending breakdown: charge type, year, gang affiliation flag | High (Issue 9) |
| MSD | NZ Super recipients who arrived in NZ after age 55, by year, 2015–2025 | Medium (Issue 10) |

---

## Data Licensing Note

All Stats NZ, INZ, and MBIE data is licensed under the Creative Commons Attribution 4.0 International licence. Australian Home Affairs data is Crown Copyright (Commonwealth of Australia) — attribution required. MSD benefit fact sheets are similarly open for journalistic use with attribution.
