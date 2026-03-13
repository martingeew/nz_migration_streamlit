# /download-stats-nz

Download the latest NZ migration CSV (ITM552301 — Estimated migration by direction and country of citizenship, Monthly) from Stats NZ Infoshare using the Playwright MCP browser tools, and save it to `data/raw/`.

---

## Steps

**1. Open the Infoshare homepage**

Use `browser_navigate` to go to `https://infoshare.stats.govt.nz/`. This establishes the ASP.NET session — do not skip this step. Navigating directly to a dataset URL will fail with a session error.

Wait for the browse tree to be visible before proceeding.

**2. Expand Tourism**

Take a `browser_snapshot` to get current element refs. Find the "Tourism" link inside the browse tree (`#ctl00_MainContent_tvBrowseNodes`) and click it. Wait for the page to fully reload (`browser_wait_for` networkidle or until the ITM link is visible) before clicking anything else.

> Important: Each tree click triggers an ASP.NET postback that regenerates EVENTVALIDATION. You must wait for the page to reload between clicks or the next click will fail with a fatal server error.

**3. Expand International Travel and Migration - ITM**

Take a fresh `browser_snapshot`. Find the "International Travel and Migration - ITM" link in the tree and click it. Wait for the page to fully reload before proceeding.

**4. Navigate to the dataset**

Take a fresh `browser_snapshot`. Find and click the link with exact text:
`Estimated migration by direction and country of citizenship, 12/16-month rule (Monthly)`

Wait for the URL to change to `SelectVariables.aspx` before proceeding.

**5. Select all Travel Direction options**

Use `browser_evaluate` to select all options in the Travel Direction listbox:
```javascript
const lb = document.getElementById('ctl00_MainContent_ctl02_lbVariableOptions');
for (let i = 0; i < lb.options.length; i++) { lb.options[i].selected = true; }
lb.dispatchEvent(new Event('change', {bubbles: true}));
```

**6. Select all Citizenship options**

Use `browser_evaluate` to select all options in the Citizenship listbox:
```javascript
const lb = document.getElementById('ctl00_MainContent_ctl04_lbVariableOptions');
for (let i = 0; i < lb.options.length; i++) { lb.options[i].selected = true; }
lb.dispatchEvent(new Event('change', {bubbles: true}));
```

**7. Select "Estimate" only for Estimate type**

Use `browser_select_option` on `#ctl00_MainContent_ctl07_lbVariableOptions` with value `Estimate` only. Do NOT select all — selecting all 4 estimate types results in ~166,000 cells which exceeds the 100,000 cell download limit.

**8. Select all Time options**

Use `browser_evaluate` to select all options in the Time listbox:
```javascript
const lb = document.getElementById('ctl00_MainContent_ctl09_lbVariableOptions');
for (let i = 0; i < lb.options.length; i++) { lb.options[i].selected = true; }
lb.dispatchEvent(new Event('change', {bubbles: true}));
```

**9. Set format to CSV**

Use `browser_select_option` on `#ctl00_MainContent_dlOutputOptions` with value `Comma delimited (.csv)`.

**10. Submit and capture download**

Click `#ctl00_MainContent_btnGo`. The file will download automatically to the `.playwright-mcp/` folder.

> Important: There are TWO Submit buttons on this page. The first (`btnOptions`) navigates to an intermediate options page. The second (`btnGo`) triggers the direct download — use this one. Find it by ref using `browser_snapshot`, it appears after the format dropdown in the row labelled "Submit HelpHelp Comma delimited (.csv) HelpHelp Submit".

**11. Copy to data/raw/**

Use Bash to copy the downloaded file to `data/raw/`:
```bash
# Find the most recently downloaded ITM file and copy it
$file = Get-ChildItem ".playwright-mcp/ITM552301*.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $file.FullName "data/raw/$($file.Name)"
```
Or on Unix (note: Playwright MCP saves with hyphens; rename to underscores to match existing files):
```bash
src=$(ls -t .playwright-mcp/ITM552301*.csv | head -1)
dest="data/raw/$(basename "$src" | tr '-' '_')"
cp "$src" "$dest"
```

**12. Confirm**

Print the filename that was saved to `data/raw/`, e.g.:
```
Downloaded: data/raw/ITM552301_20260313_XXXXXX_XX.csv
```

---

## Element ID reference

| Variable | Element ID |
|---|---|
| Travel Direction listbox | `ctl00_MainContent_ctl02_lbVariableOptions` |
| Citizenship listbox | `ctl00_MainContent_ctl04_lbVariableOptions` |
| Estimate type listbox | `ctl00_MainContent_ctl07_lbVariableOptions` |
| Time listbox | `ctl00_MainContent_ctl09_lbVariableOptions` |
| Format dropdown | `ctl00_MainContent_dlOutputOptions` |
| Submit button | `ctl00_MainContent_btnGo` |
