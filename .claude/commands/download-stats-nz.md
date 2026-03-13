# /download-stats-nz

Download the latest NZ migration CSV (ITM552301 — Estimated migration by direction and country of citizenship, Monthly) from Stats NZ Infoshare using the Playwright MCP browser tools, and save it to `data/raw/`.

---

## Steps

**1. Open the Infoshare homepage**

Use `browser_navigate` to go to `https://infoshare.stats.govt.nz/`. This establishes the ASP.NET session — do not skip this step. Navigating directly to a dataset URL will fail with a session error.

Wait for the browse tree to be visible before proceeding.

**2. Expand Tourism**

Use `browser_click` on the "Tourism" link in the browse tree. The response snapshot will contain the expanded subtree — use the ref from that snapshot for the next step.

**3. Expand International Travel and Migration - ITM**

Use `browser_click` on the "International Travel and Migration - ITM" link.

> The ITM subtree is large — the snapshot will exceed the inline limit and be saved to a file. Immediately follow up with `browser_snapshot` (using `filename: "itm-snapshot.md"`) to get a searchable markdown file, then use Grep to find the ITM552301 ref:
> ```
> Grep pattern="ITM552301" path="itm-snapshot.md" output_mode="content" -C=2
> ```
> Look for the `link [ref=eXXXX]` on the line with `sTourism\\...ITM552301.px` — that's the ref for step 4.

**4. Navigate to the dataset**

Use `browser_click` on the ref found in step 3 (the ITM552301 dataset link). The page will navigate to SelectVariables.aspx.

> Each `browser_click` on a tree node waits for navigation to settle before returning, so no extra `browser_wait_for` calls are needed between steps.

**5. Select all variables and set CSV format (single call)**

Use one `browser_evaluate` call to set all listboxes and the format dropdown at once:
```javascript
const ids = {
  dir:  'ctl00_MainContent_ctl02_lbVariableOptions',
  cit:  'ctl00_MainContent_ctl04_lbVariableOptions',
  est:  'ctl00_MainContent_ctl07_lbVariableOptions',
  time: 'ctl00_MainContent_ctl09_lbVariableOptions',
  fmt:  'ctl00_MainContent_dlOutputOptions',
};
['dir','cit','time'].forEach(k => {
  const lb = document.getElementById(ids[k]);
  for (let i = 0; i < lb.options.length; i++) lb.options[i].selected = true;
  lb.dispatchEvent(new Event('change', {bubbles: true}));
});
const lb3 = document.getElementById(ids.est);
for (let i = 0; i < lb3.options.length; i++)
  lb3.options[i].selected = (lb3.options[i].text === 'Estimate');
lb3.dispatchEvent(new Event('change', {bubbles: true}));
const dd = document.getElementById(ids.fmt);
for (let i = 0; i < dd.options.length; i++)
  if (dd.options[i].text.includes('Comma delimited')) dd.options[i].selected = true;
dd.dispatchEvent(new Event('change', {bubbles: true}));
```

> Do NOT select all 4 estimate types — that results in ~166,000 cells, exceeding the 100,000 cell limit. "Estimate" only = ~41,538 cells.

**6. Submit and capture download**

Use `browser_evaluate` to click btnGo by its stable element ID — no snapshot needed:
```javascript
() => { document.getElementById('ctl00_MainContent_btnGo').click(); return 'clicked'; }
```
The file will download automatically to the `.playwright-mcp/` folder. Look for `Downloading file ITM552301_...csv` in the events.

**7. Copy to data/raw/**

Use Bash to copy the downloaded file to `data/raw/`:
```bash
# Windows PowerShell
$file = Get-ChildItem ".playwright-mcp/ITM552301*.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $file.FullName "data/raw/$($file.Name -replace '-','_')"
```
Or on Unix (Playwright MCP saves with hyphens; rename to underscores to match existing files):
```bash
src=$(ls -t .playwright-mcp/ITM552301*.csv | head -1)
dest="data/raw/$(basename "$src" | tr '-' '_')"
cp "$src" "$dest"
```

**8. Confirm**

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
