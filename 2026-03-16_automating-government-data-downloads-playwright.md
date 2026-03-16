# No API? No Problem — Automating Government Data Downloads with Claude Code

Every month I update a [NZ migration dashboard](https://autonomousecon.substack.com/p/new-zealands-millennial-migration?r=2o1mc). The underlying data comes from Stats NZ Infoshare — a legacy government portal with no public API, no direct download links, and a multi-step web form that requires clicking through a tree menu, selecting variables from listboxes, and hitting a submit button that triggers a file download.

Three separate datasets. Each requiring the same ritual. About 30 minutes of my month, every month, for as long as I keep the dashboard running.

This post shows you how I automated that process using Playwright browser automation — both as a Python script for unattended scheduled runs and as a Claude Code slash command for interactive use. The patterns apply to any government or institutional site that serves data through a form rather than an API.

> **[Video: Playwright MCP automation in action — navigating Stats NZ and downloading a CSV]**

---

### The problem: 3 datasets, no API, 30 minutes of clicking each month

Stats NZ publishes its migration data through Infoshare — a portal built on ASP.NET WebForms, a framework from the early 2000s that was already old when it was new. There is no API. There are no permanent download links. Every download starts from the homepage, navigates a tree structure, selects variable combinations from listboxes, and submits a form that checks whether your selection exceeds 100,000 cells before deciding whether to return a file.

The three datasets I need for the dashboard:

- **ITM552301** — migration by direction and country of citizenship (monthly)
- **ITM552101** — migration by direction, age group, and sex (monthly)
- **ITM552201** — migrant arrivals by visa type (monthly)

None of this is complex. But 30 minutes of repetitive clicking per month, 12 months a year, adds up — and more than the time, it's the kind of task where skipping one month breaks the dashboard's data continuity.

The fix is browser automation. A script that navigates the site exactly as a human would, but runs in the background without you watching.

---

### Which browser tool to use (and why Firecrawl won't work here)

Before building anything, I looked at four options:

| Tool | Verdict |
|------|---------|
| **Playwright** ✅ | Best: headless, schedulable, captures file downloads natively |
| **Claude Chrome Extension** | Good for interactive/exploratory use — not schedulable |
| **Firecrawl** | Not suitable — extracts page content as markdown, can't submit forms |
| **Tavily** | Not suitable — a search API, no browser interaction at all |

The key requirement is stateful form interaction: the site needs a session established from the homepage, the tree navigation updates server-side tokens at each level, and the final download is triggered by a button click — not a direct URL. Scraping tools that read page content don't help here. You need a browser that can click things.

Playwright handles all of this natively, runs headless for scheduling, captures downloads to a local directory, and has two interfaces: a Python library for scripted runs, and a Model Context Protocol (MCP) plugin that works interactively inside Claude Code sessions.

This is also what makes it useful well beyond downloading government data. The same approach works for booking concert tickets at midnight, checking stock levels before they sell out, or filling in any form that requires human-equivalent interaction on a schedule.

One exception: sites with login or CAPTCHAs. The Chrome Extension uses your existing browser session, so it's already past both. For those cases it's the easier option — Playwright can handle them (persistent browser profile, manual pause, or a paid solving service), but it's more work. For a public portal like Stats NZ, it's a non-issue.

---

### How Stats NZ Infoshare fights you (and how to win)

Three gotchas specific to Infoshare — and common to most ASP.NET WebForms sites:

**1. You must start from the homepage every time.**

Navigating directly to a dataset URL returns a session error. The homepage sets up invisible ASP.NET session state. Skip it and nothing works downstream. I hardcoded this as step 1 in both the Python script and the slash command, with a comment explaining why — so future me doesn't remove it.

**2. Navigate the tree one click at a time.**

The EVENTVALIDATION token that ASP.NET issues is only valid for nodes visible at the current level of the tree. Click Tourism → expand ITM → click a dataset. You cannot skip Tourism and click ITM directly — the server returns a `fatal_error` redirect. Each click has to wait for the page to fully load before the next one fires.

In the Python script, this means calling `page.wait_for_load_state("networkidle")` after every intermediate tree click. In the MCP slash command, `browser_click` handles the wait automatically.

**3. Select all — but check the cell limit first.**

Stats NZ caps downloads at 100,000 cells. `directions × citizenships × months` for ITM552301 is around 8,000 cells — well within the limit. `directions × age groups × sex × estimate types × months` for ITM552101 is over 350,000 cells — well over.

For ITM552101, I select only 13 grouped age bands and only the "Estimate" type. The cell count drops to around 60,000. I document this calculation as a comment in the script so the logic is visible when the data is updated next year.

---

### Two ways to automate it: slash command and Python script

Both work end-to-end. They suit different situations.

**The Claude Code slash command (`/download-stats-nz`)**

A markdown file in `.claude/commands/` that gives Claude step-by-step instructions for navigating Infoshare using the Playwright MCP plugin. Run it inside a Claude Code session and Claude navigates the browser interactively, selecting variables and downloading the file to `data/raw/`. It consolidates all the form selections into a single JavaScript call rather than clicking each option individually — for a dataset with ~200 citizenship options, that's a meaningful speedup.

**The Python script (`download_stats_nz.py`)**

The same navigation logic, but packaged as a standalone script that runs without Claude. No LLM token cost per execution, fully schedulable with cron or Task Scheduler, and the download capture is more reliable for unattended runs.

The Python script is the better choice for anything running on a schedule. The slash command is better for one-off interactive downloads where you want to see what's happening as it runs — or for building and testing the automation before converting it to a script.

---

### 5 patterns that work on any website

These aren't Stats NZ-specific. I'd apply all of them the next time I need to automate any site that serves data through forms.

**1. Always open the homepage.** Even if you know the direct URL. Many sites require a homepage visit to establish a server-side session. Document why in the code — so nobody removes it later thinking it's redundant.

**2. Navigate tree structures one click at a time.** Server-side navigation patterns issue tokens scoped to the current level. Jumping ahead invalidates them. Click and wait, then click and wait again.

**3. Use `browser_click` for navigation, `browser_evaluate` for DOM manipulation.** `browser_evaluate` in Claude Code resolves before ASP.NET postback navigation completes — you end up on a stale page. Reserve `evaluate` for in-page operations: selecting options, clicking submit buttons that trigger downloads (not page loads).

**4. Know your data limits before automating selection.** Calculate `dimensions × options × time periods` before writing selection logic. Document the number. Use an explicit filter for oversized dimensions — not "select all".

**5. Normalise filenames at the end.** Playwright MCP saves downloads with hyphens; your project may expect underscores. The mismatch is invisible until it breaks a downstream glob pattern. Add a rename step and document what the raw output looks like.

---

The next post covers what happens with the data once it lands in `data/raw/` — processing the raw multi-row-header CSVs into a clean long format and building the Streamlit dashboard on top.

The `download_stats_nz.py` script and the `/download-stats-nz` slash command are both in the [project repo](#).

---

### Bonus: Copy-and-paste prompts to build your own automation

The prompts below are structured to work on any website — not just Stats NZ. Paste them into Claude with your website URL and a description of what you want, and you'll get a working slash command or Python script without having to learn any of the ASP.NET internals yourself. Each prompt includes the rules I learned the hard way so you don't have to repeat my mistakes.

[PAYWALL]

**For a Claude Code slash command:**

> I want to automate downloading data from a website on a repeating basis. Please explore the website using the browser tools, then write a reusable slash command I can run whenever I need fresh data.
>
> As you work, follow these rules — they come from hard experience:
>
> 1. **Always open the homepage first**, even if you know the direct URL to the data. Many websites require a homepage visit to set up an invisible session before deeper pages will work.
> 2. **Navigate any menu tree one link at a time.** If the website has a menu tree or wizard, click each level individually and wait for the page to fully load before moving to the next. Never try to jump ahead.
> 3. **If a page is too large to read, save it to a file and search it** rather than trying to read it inline.
> 4. **Use the element's permanent ID to click buttons**, not a position or snapshot reference — especially for the final download button.
> 5. **Look for multiple submit buttons** and verify which one triggers the download — forms often have a "preview" button and a "download" button that look similar.
> 6. **Before selecting all options, check whether the result would be too large.** Many sites have a row or cell limit. If it's close, be selective rather than choosing everything.
> 7. **In the command file, write a short note explaining *why* each non-obvious step is done that way**, so the command still works when run months later without re-investigating the site.

**What to provide before running:**
- What data you want and which filters or breakdowns matter to you
- Any known cell or row limits
- Whether login is required (if so, handle credentials separately first)
- Any buttons that submit forms, place orders, or delete things — name them explicitly so Claude avoids them

You don't need to provide element IDs, CSS selectors, or the order to click things. Claude discovers those.

---

**For a scheduled Python Playwright script:**

> I want a Python script using Playwright (`pip install playwright`) that automates downloading a file from a website. It should run unattended and be schedulable with cron or Task Scheduler.
>
> Design rules — these come from hard experience:
>
> 1. **Start from the homepage** before navigating anywhere. The script should `goto(homepage)` and wait for a known element to confirm the session is ready before doing anything else.
> 2. **Navigate any menu tree one link at a time**, calling `page.wait_for_load_state("networkidle")` after each intermediate click. Never skip a level.
> 3. **Always call `page.wait_for_selector("#element_id")` before any `page.evaluate()`** that accesses that element. Evaluating before render throws a null reference error.
> 4. **When selecting options programmatically in JavaScript, always dispatch a change event** after: `element.dispatchEvent(new Event('change', {bubbles: true}))`. Without it, server-side listeners won't fire.
> 5. **Wrap the download-triggering click in `with page.expect_download() as download_info:`**. Use `download.suggested_filename` to preserve the server's original filename.
> 6. **Use a config dict to separate dataset-specific settings from execution logic** — tree path, element IDs, which options to select. Adding a new dataset should require only a new dict entry.
> 7. **Use role-based selectors (`get_by_role`) for navigation links** and **stable element IDs for form controls**. Navigation link text is stable even as the DOM shifts; form element IDs are hardcoded server-side and never change.

**What to provide before running:**
- What data you want and which options to select on the site
- Any known cell or row limits
- Whether multiple datasets need to be downloaded in one run
- The destination directory for saved files
- The first 6–8 rows of a sample raw file if you also want a processing step — header depth, forward-fill structure, and data shape are immediately visible from those rows and save Claude from having to download the file just to inspect it

---

**Stats NZ reference implementation**

Here's what Claude produced for the Stats NZ case — useful as a reference when interpreting the prompt output for your own site.

For the slash command, all listbox selections go in a single `browser_evaluate` call. This avoids one round trip per option (important when a listbox has 200+ entries) and dispatches the `change` events that ASP.NET's form listeners need:

```javascript
() => {
  const allListboxes = Array.from(document.querySelectorAll('[id$="_lbVariableOptions"]'));
  allListboxes.forEach(lb => {
    for (let i = 0; i < lb.options.length; i++) lb.options[i].selected = true;
    lb.dispatchEvent(new Event('change', {bubbles: true}));
  });
  // Narrow to Estimate only (avoids the 100k cell limit)
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
  return 'done';
}
```

For the Python script, wrap the submit click in `expect_download()` — without this the file ends up in a temp location and is silently lost. `suggested_filename` preserves the server's own name, which for Stats NZ embeds the dataset ID and a timestamp:

```python
with page.expect_download() as download_info:
    page.evaluate("document.getElementById('ctl00_MainContent_btnGo').click()")

download = download_info.value
download.save_as(output_dir / download.suggested_filename)
# Saves as e.g. ITM552301_20260314_112426_6.csv
```
