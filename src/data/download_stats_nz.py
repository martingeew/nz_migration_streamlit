"""
Download NZ migration data from Stats NZ Infoshare.

Usage:
    python download_stats_nz.py                      # download all datasets
    python download_stats_nz.py --dataset itm552301  # specific dataset only

Schedule with Windows Task Scheduler or cron to run after each Stats NZ release.
Check the Stats NZ release calendar for ITM release dates:
https://www.stats.govt.nz/release-calendar

Dependencies:
    pip install playwright
    playwright install chromium
"""

import argparse
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

INFOSHARE_HOME = "https://infoshare.stats.govt.nz/"

# ---------------------------------------------------------------------------
# Dataset configs
# tree_postback: the postback argument to expand the parent category in the
#   browse tree (Tourism > ITM). This reveals the dataset links.
# link_text: exact text of the dataset link to click after expansion.
# listboxes: variable selections on the SelectVariables page.
#   "all" = select every option; a list = select only those values.
# ---------------------------------------------------------------------------

DATASETS = {
    "itm552301": {
        "name": "Estimated migration by direction and country of citizenship (Monthly)",
        # Click each link in order to step through the tree.
        # Each postback updates VIEWSTATE/EVENTVALIDATION before the next click.
        "tree_path": [
            "Tourism",
            "International Travel and Migration - ITM",
            "Estimated migration by direction and country of citizenship, 12/16-month rule (Monthly)",
        ],
        "listboxes": {
            "ctl00_MainContent_ctl02_lbVariableOptions": "all",  # Travel Direction
            "ctl00_MainContent_ctl04_lbVariableOptions": "all",  # Citizenship
            "ctl00_MainContent_ctl07_lbVariableOptions": [
                "Estimate"
            ],  # Estimate type only
            "ctl00_MainContent_ctl09_lbVariableOptions": "all",  # Time
        },
    },
    "itm_citizenship_visa": {
        "name": "Estimated migrant arrivals by citizenship, visa type and CLPR (Monthly)",
        "tree_path": [
            "Tourism",
            "International Travel and Migration - ITM",
            "Estimated migrant arrivals by citizenship, visa type and CLPR, 12/16-month rule (Monthly)",
        ],
        # Cell count: 1 direction × 1 CLPR × 7 visa types × 24 citizenships × 303 months ≈ 7k (< 100k limit)
        # CLPR = Country of Last/First Permanent Residence; select India only for India-focused analysis
        "listboxes": {
            "ctl00_MainContent_ctl02_lbVariableOptions": "all",              # Direction (all)
            "ctl00_MainContent_ctl04_lbVariableOptions": ["India"],          # CLPR: India only
            "ctl00_MainContent_ctl07_lbVariableOptions": "all",              # Visa type (all 7)
            "ctl00_MainContent_ctl09_lbVariableOptions": "all",              # Citizenship (24 countries)
            "ctl00_MainContent_ctl12_lbVariableOptions": ["Estimate"],       # Estimate type only
            "ctl00_MainContent_ctl14_lbVariableOptions": "all",              # Time (all months)
        },
    },
    "itm_direction_region": {
        "name": "Estimated migration by direction, citizenship and NZ area (Monthly)",
        "tree_path": [
            "Tourism",
            "International Travel and Migration - ITM",
            "Estimated migration by direction, citizenship and NZ area, 12/16-month rule (Monthly)",
        ],
        # Cell count: 3 directions × 1 citizenship × 108 NZ areas × 143 months ≈ 46k (< 100k limit)
        # Citizenship dimension limited to TOTAL to stay within cell cap
        "listboxes": {
            "ctl00_MainContent_ctl02_lbVariableOptions": ["Monthly"],              # Period: Monthly only
            "ctl00_MainContent_ctl04_lbVariableOptions": "all",                    # Direction (Arrivals/Departures/Net)
            "ctl00_MainContent_ctl07_lbVariableOptions": ["TOTAL ALL CITIZENSHIPS"],  # All citizenships combined
            "ctl00_MainContent_ctl09_lbVariableOptions": "all",                    # NZ Area (108 regions)
            "ctl00_MainContent_ctl12_lbVariableOptions": "all",                    # Estimate type (Estimate only)
            "ctl00_MainContent_ctl14_lbVariableOptions": "all",                    # Time (all months)
        },
    },
}

RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
FORMAT_DROPDOWN_ID = "ctl00_MainContent_dlOutputOptions"
SUBMIT_BUTTON_ID = "ctl00_MainContent_btnGo"
TREE_ID = "ctl00_MainContent_tvBrowseNodes"


def select_all_options(page, listbox_id: str) -> None:
    page.wait_for_selector(f"#{listbox_id}")
    page.evaluate(
        f"""
        const lb = document.getElementById('{listbox_id}');
        for (let i = 0; i < lb.options.length; i++) {{
            lb.options[i].selected = true;
        }}
        lb.dispatchEvent(new Event('change', {{bubbles: true}}));
    """
    )


def select_specific_options(page, listbox_id: str, values: list[str]) -> None:
    page.wait_for_selector(f"#{listbox_id}")
    page.locator(f"#{listbox_id}").select_option(values)


def navigate_to_dataset(page, config: dict) -> None:
    """Step through the browse tree one level at a time, then land on SelectVariables."""
    # Always start from a clean browse tree state
    page.goto(INFOSHARE_HOME)
    page.wait_for_selector(f"#{TREE_ID}")
    tree = page.locator(f"#{TREE_ID}")
    for step in config["tree_path"][:-1]:
        # Click each intermediate node and wait for the tree to update
        tree.get_by_role("link", name=step, exact=True).click()
        page.wait_for_load_state("networkidle")
        print(f"  Expanded: {step}")
    # Final click navigates to SelectVariables
    final = config["tree_path"][-1]
    tree.get_by_role("link", name=final, exact=True).click()
    page.wait_for_url("**/SelectVariables.aspx**")
    print(f"  Navigated to SelectVariables: {page.url}")


def download_dataset(page, key: str, config: dict, output_dir: Path) -> Path:
    print(f"\n{'='*60}")
    print(f"Downloading: {config['name']}")
    print(f"{'='*60}")

    navigate_to_dataset(page, config)

    # Select variables
    for listbox_id, selection in config["listboxes"].items():
        if selection == "all":
            select_all_options(page, listbox_id)
        else:
            select_specific_options(page, listbox_id, selection)

    # Set format to CSV
    page.locator(f"#{FORMAT_DROPDOWN_ID}").select_option("Comma delimited (.csv)")

    # Accept any confirm dialog (e.g. "more than 256 columns" warning for wide datasets)
    page.once("dialog", lambda d: d.accept())

    # Click submit and capture the download (large datasets can take >30s)
    with page.expect_download(timeout=180_000) as download_info:
        page.locator(f"#{SUBMIT_BUTTON_ID}").click()

    download = download_info.value
    dest_path = output_dir / download.suggested_filename
    download.save_as(dest_path)
    print(f"  Saved: {dest_path.name}")
    return dest_path


def main(datasets_to_run: list[str] | None = None) -> None:
    output_dir = RAW_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if datasets_to_run is None:
        datasets_to_run = list(DATASETS.keys())

    print(
        f"Stats NZ Infoshare downloader — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    print(f"Output directory: {output_dir}")

    downloaded = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Visit homepage to establish ASP.NET session
        print("Initialising session...")
        page.goto(INFOSHARE_HOME)
        page.wait_for_selector(f"#{TREE_ID}")
        print("  Session ready.")

        for key in datasets_to_run:
            if key not in DATASETS:
                print(f"Unknown dataset key: {key}. Available: {list(DATASETS.keys())}")
                continue
            path = download_dataset(page, key, DATASETS[key], output_dir)
            downloaded.append(path)

        browser.close()

    print(f"\nDone. {len(downloaded)} file(s) downloaded:")
    for p in downloaded:
        print(f"  {p}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Stats NZ Infoshare data")
    parser.add_argument(
        "--dataset",
        nargs="+",
        help="Dataset key(s) to download. Defaults to all. Choices: " + ", ".join(DATASETS.keys()),
    )
    args = parser.parse_args()
    main(datasets_to_run=args.dataset)
