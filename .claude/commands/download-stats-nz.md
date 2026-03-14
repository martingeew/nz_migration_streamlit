# /download-stats-nz

Download the latest NZ migration CSV from Stats NZ Infoshare using the Playwright MCP browser tools, and save it to `data/raw/`.

**Argument:** Pass one of the following (default: `direction-citizenship`):
- `direction-citizenship` — ITM552301: Estimated migration by direction and country of citizenship (Monthly)
- `direction-age-sex` — ITM552101: Estimated migration by direction, age group and sex (Monthly)
- `arrivals-visatype` — ITM552201: Estimated migrant arrivals by visa type (Monthly)

---

## Steps

**1. Open the Infoshare homepage**

Use `browser_navigate` to go to `https://infoshare.stats.govt.nz/`. This establishes the ASP.NET session — do not skip this step. Navigating directly to a dataset URL will fail with a session error.

Wait for the browse tree to be visible before proceeding.

**2. Expand Tourism**

Use `browser_click` on the "Tourism" link in the browse tree. The response snapshot will contain the expanded subtree — use the ref from that snapshot for the next step.

**3. Expand International Travel and Migration - ITM**

Use `browser_click` on the "International Travel and Migration - ITM" link.

> The ITM subtree is large — the snapshot will exceed the inline limit and be saved to a file. Immediately follow up with `browser_snapshot` (using `filename: "itm-snapshot.md"`) to get a searchable markdown file, then use Grep to find the dataset ref:
> ```
> Grep pattern="<PATTERN>" path="itm-snapshot.md" output_mode="content" -C=2
> ```
> Use the pattern for your argument (see table in step 4).
> Look for the `link [ref=eXXXX]` on the matching line — that's the ref for step 4.

**4. Navigate to the dataset**

Grep `itm-snapshot.md` for the pattern matching your argument, then use `browser_click` on the found ref:

| Argument               | Grep pattern | Dataset ID |
|------------------------|--------------|------------|
| `direction-citizenship` | `ITM552301` | ITM552301  |
| `direction-age-sex`    | `ITM552101`  | ITM552101  |
| `arrivals-visatype`    | `ITM552201`  | ITM552201  |

The page will navigate to SelectVariables.aspx.

> Each `browser_click` on a tree node waits for navigation to settle before returning, so no extra `browser_wait_for` calls are needed between steps.

**5. Select all variables and set CSV format (single call)**

Use one `browser_evaluate` call. The JS varies by dataset:

**`direction-citizenship` and `arrivals-visatype`** — generic block (select all listboxes, narrow Estimate type):
```javascript
const allListboxes = Array.from(document.querySelectorAll('[id$="_lbVariableOptions"]'));
allListboxes.forEach(lb => {
  for (let i = 0; i < lb.options.length; i++) lb.options[i].selected = true;
  lb.dispatchEvent(new Event('change', {bubbles: true}));
});
allListboxes.forEach(lb => {
  const opts = Array.from(lb.options);
  if (opts.length > 1 && opts.some(o => o.text === 'Estimate')) {
    opts.forEach(o => { o.selected = (o.text === 'Estimate'); });
    lb.dispatchEvent(new Event('change', {bubbles: true}));
  }
});
const dd = document.getElementById('ctl00_MainContent_dlOutputOptions');
for (let i = 0; i < dd.options.length; i++)
  if (dd.options[i].text.includes('Comma delimited')) dd.options[i].selected = true;
dd.dispatchEvent(new Event('change', {bubbles: true}));
```

**`direction-age-sex`** — must use explicit age selection: the age listbox contains individual years (0–89) plus grouped bands; selecting all would exceed the 100,000 cell limit (~354k cells). Select only the 13 grouped bands that match the existing raw file:
```javascript
const ageTarget = new Set([
  'Under 15 Years','15-19 Years','20-24 Years','25-29 Years','30-34 Years',
  '35-39 Years','40-44 Years','45-49 Years','50-54 Years','55-59 Years',
  '60-64 Years','65 Years and Over','Total All Ages'
]);
const dir = document.getElementById('ctl00_MainContent_ctl02_lbVariableOptions');
for (let i = 0; i < dir.options.length; i++) dir.options[i].selected = true;
dir.dispatchEvent(new Event('change', {bubbles: true}));
const age = document.getElementById('ctl00_MainContent_ctl04_lbVariableOptions');
for (let i = 0; i < age.options.length; i++)
  age.options[i].selected = ageTarget.has(age.options[i].text);
age.dispatchEvent(new Event('change', {bubbles: true}));
const sex = document.getElementById('ctl00_MainContent_ctl07_lbVariableOptions');
for (let i = 0; i < sex.options.length; i++) sex.options[i].selected = true;
sex.dispatchEvent(new Event('change', {bubbles: true}));
const est = document.getElementById('ctl00_MainContent_ctl09_lbVariableOptions');
for (let i = 0; i < est.options.length; i++)
  est.options[i].selected = (est.options[i].text === 'Estimate');
est.dispatchEvent(new Event('change', {bubbles: true}));
const time = document.getElementById('ctl00_MainContent_ctl12_lbVariableOptions');
for (let i = 0; i < time.options.length; i++) time.options[i].selected = true;
time.dispatchEvent(new Event('change', {bubbles: true}));
const dd = document.getElementById('ctl00_MainContent_dlOutputOptions');
for (let i = 0; i < dd.options.length; i++)
  if (dd.options[i].text.includes('Comma delimited')) dd.options[i].selected = true;
dd.dispatchEvent(new Event('change', {bubbles: true}));
```

> Selecting "Estimate" only avoids exceeding the 100,000 cell limit.

**6. Submit and capture download**

Use `browser_evaluate` to click btnGo by its stable element ID — no snapshot needed:
```javascript
() => { document.getElementById('ctl00_MainContent_btnGo').click(); return 'clicked'; }
```
The file will download automatically to the `.playwright-mcp/` folder. Look for `Downloading file <DATASETID>_...csv` in the events.

**7. Copy to data/raw/**

Use Bash to copy the downloaded file to `data/raw/`:
```bash
# Windows PowerShell
$file = Get-ChildItem ".playwright-mcp/*.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $file.FullName "data/raw/$($file.Name -replace '-','_')"
```
Or on Unix (Playwright MCP saves with hyphens; rename to underscores to match existing files):
```bash
src=$(ls -t .playwright-mcp/*.csv | head -1)
dest="data/raw/$(basename "$src" | tr '-' '_')"
cp "$src" "$dest"
```

Expected filename prefixes per dataset: `ITM552301_`, `ITM552101_`, `ITM552201_`.

**8. Confirm**

Print the filename that was saved to `data/raw/`, e.g.:
```
Downloaded: data/raw/ITM552101_20260314_XXXXXX_XX.csv
```

---

## Element ID reference

| Element                              | Element ID                                      |
|--------------------------------------|-------------------------------------------------|
| Submit button                        | `ctl00_MainContent_btnGo`                       |
| Format dropdown                      | `ctl00_MainContent_dlOutputOptions`             |
| direction-age-sex: Direction listbox | `ctl00_MainContent_ctl02_lbVariableOptions`     |
| direction-age-sex: Age listbox       | `ctl00_MainContent_ctl04_lbVariableOptions`     |
| direction-age-sex: Sex listbox       | `ctl00_MainContent_ctl07_lbVariableOptions`     |
| direction-age-sex: Estimate listbox  | `ctl00_MainContent_ctl09_lbVariableOptions`     |
| direction-age-sex: Time listbox      | `ctl00_MainContent_ctl12_lbVariableOptions`     |
