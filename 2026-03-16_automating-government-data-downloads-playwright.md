# No API? No Problem — Automating Government Data Downloads with Claude Code

Every month I update a [NZ migration dashboard](https://autonomousecon.substack.com/p/new-zealands-millennial-migration?r=2o1mc). The underlying data comes from Stats NZ Infoshare — a legacy government portal with no public API, no direct download links, and a multi-step form you have to click through manually every time.

Three separate datasets. Each requiring the same ritual in addition to some follow-up formatting. About 30 minutes every month, for as long as I keep the dashboard running.

This post shows you how I automated that process using Playwright browser automation — both as a Python script for unattended scheduled runs and as a Claude Code slash command for interactive use. The patterns apply to any  website that serves data through a form rather than an API.

> **[Video: Playwright MCP automation in action — navigating Stats NZ and downloading a CSV]**

---

### The problem: 3 datasets, no API, 30 minutes of clicking each month

Stats NZ publishes its migration data through Infoshare — a portal built on ASP.NET WebForms, a framework from the early 2000s that was already old when it was new. There is no API. There are no permanent download links. Every download starts from the homepage, navigates a tree structure, selects variable combinations from listboxes, and submits a form to trigger a file download.

The three datasets I need for the dashboard:

- **ITM552301** — migration by direction and country of citizenship (monthly)
- **ITM552101** — migration by direction, age group, and sex (monthly)
- **ITM552201** — migrant arrivals by visa type (monthly)

None of this is complex. But it's 30 minutes of clicking, every month, for as long as the dashboard runs. That's 6 hours a year just to keep the current datasets fresh. Add more datasets and that number grows. There's also the mental overhead of remembering to do it.

To solve this problem, I needed browser automation. A script or tool that navigates the site exactly as a human would, but runs in the background without you watching.

---

### Which browser tool to use (and why Firecrawl won't work here)

Before building anything, I looked at four options:

| Tool | Verdict |
|------|---------|
| **Playwright** ✅ | Best: headless, schedulable, captures file downloads natively |
| **Claude Chrome Extension** | Good for interactive/exploratory use — not schedulable |
| **Firecrawl** | Not suitable — extracts page content as markdown, can't submit forms |
| **Tavily** | Not suitable — a search API, no browser interaction at all |

Headless means the browser runs as a background process with no visible window i.e. no screen required, no user watching. It behaves exactly like a normal browser but can be triggered from a script or a scheduler.

The key requirement is that the site needs to be driven like a human would — start from the homepage, click through a tree menu, make selections, then hit a button to trigger the download. There's no shortcut URL you can hit directly. Scraping tools that just read page content don't help here. You need something that can actually click things.

Playwright handles all of this natively, runs headless for scheduling, captures downloads to a local directory. I tested it via two interfaces: a Python library for scripted runs, and a Model Context Protocol (MCP) plugin that works interactively inside Claude Code sessions.

This is also what makes it useful well beyond downloading data. The same approach works for booking concert tickets, checking stock levels before they sell out, or filling in any form that requires human-equivalent interaction on a schedule.

One exception: sites with login or CAPTCHAs. The Chrome Extension uses your existing browser session, so it's already gets past both. For those cases it's the easier option. Playwright can handle them (persistent browser profile, manual pause, or a paid solving service), but it's more work.

---

### Two ways to automate it: Claude slash command and Python script

Both work end-to-end. They suit different situations.

**The Claude Code slash command (`/download-stats-nz`)**

A markdown file in `.claude/commands/` that gives Claude step-by-step instructions for navigating Infoshare using the Playwright MCP plugin. Run it inside a Claude Code session and Claude navigates the browser interactively, selecting variables and downloading the file to `data/raw/`. I have a separate command for each of the three datasets — `/download-stats-nz direction-citizenship`, `/download-stats-nz age-sex`, `/download-stats-nz visa-type` — so each one knows exactly which tree path to follow and which variables to select.

The Playwright MCP plugin is an add-on for Claude Code that gives Claude direct control over a browser window. To set it up, just ask Claude Code to install the Playwright MCP plugin and it will walk you through the steps.

**The Python script (`download_stats_nz.py`)**

The same navigation logic, but written directly in Python using the Playwright library — no Claude involved. It runs without an active Claude session, has no LLM token cost, and can be scheduled with cron or Task Scheduler to run unattended.

I have a post covering how to automate python scripts [here].

The Python script is the better choice for anything running on a schedule. The slash command is better for one-off interactive downloads where you want to see what's happening as it runs — or for building and testing the automation before converting it to a script.

---

### 6 patterns that work on any website

These aren't Stats NZ-specific. I'd apply all of them the next time I need to automate any site that serves data through forms.

**1. Always open the homepage.** Even if you know the direct URL. Many sites require a homepage visit to establish a server-side session. Make it explicit in your slash command or script.

**2. Navigate tree structures one click at a time.** The site needs to register each click before the next one fires. Skip a level and you'll get an error. Click, wait for the page to update, then click again.

**3. Use the Playwright `browser_click` command for moving between pages, and `browser_evaluate` for in-page actions like selecting from a listbox or clicking a download button.**

**4. Know your data limits before automating selection.** Calculate `dimensions × options × time periods` before writing selection logic. Document the number. Use an explicit filter for oversized dimensions — not "select all".

**5. Add a post-processing step to normalise the download.** Playwright MCP saves files with auto-generated names using hyphens; your project may expect a specific naming convention with underscores. Run a consistent cleanup step at the end of every download — rename the file, move it to the right folder — so the rest of your pipeline always sees the same format regardless of what the browser produced.

**6. Verify the output before the script exits.** Check the file exists and has a non-zero size. For a scheduled script you're not watching, a silent failure — no file, empty file, wrong file — can go unnoticed until the dashboard breaks a month later.

---

The next post takes this further — automating the entire dashboard workflow end to end, so the data downloads, processes, and updates without me touching it at all.

---

### Bonus: Copy-and-paste prompts to build your own automation

The prompts below are structured to work on any website — not just Stats NZ. Paste them into Claude with your website URL and a description of what you want, and you'll get a working slash command or Python script without having to figure out the site's internals yourself. Each prompt includes the rules I learned along the way so you don't have to repeat my mistakes.

[PAYWALL]

**For a Claude Code slash command:**

> I want to automate downloading data from a website on a repeating basis. Please explore the website using the browser tools, then write a reusable slash command I can run whenever I need fresh data. Save it as a markdown file in `.claude/commands/` in my project repo.
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
- A sample of the file you expect to get back, if you have one
- Any known cell or row limits
- Whether login is required (if so, handle credentials separately first)
- Any buttons that submit forms, place orders, or delete things — name them explicitly so Claude avoids them

You don't need to provide element IDs, CSS selectors, or the order to click things. Claude discovers those.

---

**For a scheduled Python Playwright script:**

> I want a Python script using Playwright (`pip install playwright`) that automates downloading a file from a website. It should run unattended and be schedulable with cron or Task Scheduler. Set up a virtual environment in the repo for the project dependencies — see [this post](https://autonomousecon.substack.com/p/run-your-data-projects-like-a-professional?r=2o1mc) for how to structure it.
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

The full Python script and slash command are in the [project repo on GitHub](https://github.com/martingeew/nz_migration_streamlit) — see `src/data/download_stats_nz.py` and `.claude/commands/download-stats-nz.md`. Here's a walkthrough of the key parts.

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
