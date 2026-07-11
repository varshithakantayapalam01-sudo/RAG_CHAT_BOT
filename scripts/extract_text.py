"""
Phase 2.3 — Extract structured data from Groww HTML pages.

Groww uses Next.js and embeds all scheme data as JSON in <script> tags.
This script extracts that JSON, parses key fields, and saves both:
  1. Structured JSON data → data/processed/<id>_data.json
  2. Human-readable text  → data/processed/<id>.txt
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

METADATA_FILE = PROJECT_ROOT / "data" / "metadata.json"
RAW_GROWW_DIR = PROJECT_ROOT / "data" / "raw" / "groww"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def extract_json_data(html_path: Path) -> dict:
    """Extract the embedded Next.js JSON data from a Groww page.

    Groww embeds all fund data in a <script> tag containing a large
    JSON object with 'pageProps' → 'mfServerSideData'.
    """
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Find all JSON-like script blocks
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)

    # Look for the main data block (largest one with pageProps)
    for script in scripts:
        script = script.strip()
        if script.startswith("{") and "pageProps" in script[:200]:
            try:
                data = json.loads(script)
                return data
            except json.JSONDecodeError:
                continue

    # Fallback: look for __NEXT_DATA__
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return {}


def extract_scheme_details(data: dict) -> dict:
    """Extract key scheme details from the parsed JSON data."""
    page_props = data.get("props", {}).get("pageProps", {})
    mf = page_props.get("mfServerSideData", {})

    details = {
        "scheme_name": mf.get("scheme_name", ""),
        "amc_name": mf.get("amc", mf.get("fund_house", "")),
        "category": mf.get("category", ""),
        "sub_category": mf.get("sub_category", ""),
        "super_category": mf.get("super_category", ""),
        "plan_type": mf.get("plan_type", ""),
        "scheme_type": mf.get("scheme_type", ""),
        "launch_date": mf.get("launch_date", ""),
        "benchmark": mf.get("benchmark_name", mf.get("benchmark", "")),
        "risk_level": mf.get("nfo_risk", ""),
        "fund_manager": mf.get("fund_manager", ""),
        "isin": mf.get("isin", ""),
        "description": mf.get("description", ""),
        "nav": {
            "current_nav": mf.get("nav", ""),
            "nav_date": mf.get("nav_date", ""),
        },
        "expense_ratio": mf.get("expense_ratio", ""),
        "exit_load": mf.get("exit_load", ""),
        "stamp_duty": mf.get("stamp_duty", ""),
        "aum": mf.get("aum", ""),
        "min_investment": {
            "lumpsum": mf.get("min_investment_amount", ""),
            "sip": mf.get("min_sip_investment", ""),
            "additional": mf.get("mini_additional_investment", ""),
        },
        "lock_in": mf.get("lock_in", {}),
        "groww_rating": mf.get("groww_rating", ""),
        "portfolio_turnover": mf.get("portfolio_turnover", ""),
    }

    # Fund manager details
    fm_details = mf.get("fund_manager_details", [])
    if fm_details:
        details["fund_manager_details"] = [
            {
                "name": fm.get("fund_manager_name", fm.get("name", "")),
                "experience": fm.get("experience", ""),
            }
            for fm in fm_details
            if isinstance(fm, dict)
        ]

    # Returns data
    return_stats = mf.get("return_stats", [])
    if return_stats:
        details["return_stats"] = return_stats

    sip_return = mf.get("sip_return", {})
    if sip_return:
        details["sip_return"] = sip_return

    simple_return = mf.get("simple_return", {})
    if simple_return:
        details["simple_return"] = simple_return

    # Holdings
    holdings = mf.get("holdings", [])
    if holdings and isinstance(holdings, list):
        details["top_holdings"] = [
            {
                "name": h.get("company_name", h.get("name", "")),
                "sector": h.get("sector_name", h.get("sector", "")),
                "percentage": h.get("corpus_per", h.get("percentage", "")),
                "instrument_type": h.get("instrument_type", ""),
            }
            for h in holdings[:10]
            if isinstance(h, dict)
        ]

    # Stats (risk ratios etc.)
    stats = mf.get("stats", [])
    if stats:
        details["stats"] = stats

    # Peer comparison
    peers = mf.get("peerComparison", [])
    if peers:
        details["peer_comparison"] = peers[:5]

    # Category info
    cat_info = mf.get("category_info", {})
    if cat_info:
        details["category_info"] = cat_info

    return details


def format_as_readable_text(details: dict, source: dict) -> str:
    """Format extracted details as human-readable text."""
    lines = []
    lines.append(f"Source: {source['url']}")
    lines.append(f"Scheme: {source['scheme']}")
    lines.append(f"Category: {source['category']}")
    lines.append(f"Downloaded: {source.get('downloaded_at', 'N/A')}")
    lines.append("=" * 60)
    lines.append("")

    # Scheme Info
    lines.append("SCHEME INFORMATION")
    lines.append("-" * 40)
    lines.append(f"  Scheme Name:      {details.get('scheme_name', 'N/A')}")
    lines.append(f"  AMC:              {details.get('amc_name', 'N/A')}")
    lines.append(f"  Category:         {details.get('category', 'N/A')}")
    lines.append(f"  Sub-Category:     {details.get('sub_category', 'N/A')}")
    lines.append(f"  Plan Type:        {details.get('plan_type', 'N/A')}")
    lines.append(f"  Scheme Type:      {details.get('scheme_type', 'N/A')}")
    lines.append(f"  Launch Date:      {details.get('launch_date', 'N/A')}")
    lines.append(f"  Benchmark:        {details.get('benchmark', 'N/A')}")
    lines.append(f"  Risk Level:       {details.get('risk_level', 'N/A')}")
    lines.append(f"  Fund Manager:     {details.get('fund_manager', 'N/A')}")
    lines.append(f"  ISIN:             {details.get('isin', 'N/A')}")
    lines.append(f"  Groww Rating:     {details.get('groww_rating', 'N/A')}")
    lines.append("")

    # Description
    desc = details.get("description", "")
    if desc:
        lines.append("DESCRIPTION")
        lines.append("-" * 40)
        lines.append(f"  {desc}")
        lines.append("")

    # NAV
    nav = details.get("nav", {})
    lines.append("NAV DETAILS")
    lines.append("-" * 40)
    lines.append(f"  Current NAV:      {nav.get('current_nav', 'N/A')}")
    lines.append(f"  NAV Date:         {nav.get('nav_date', 'N/A')}")
    lines.append("")

    # Costs
    lines.append("COSTS & FEES")
    lines.append("-" * 40)
    lines.append(f"  Expense Ratio:    {details.get('expense_ratio', 'N/A')}")
    lines.append(f"  Exit Load:        {details.get('exit_load', 'N/A')}")
    lines.append(f"  Stamp Duty:       {details.get('stamp_duty', 'N/A')}")
    lines.append("")

    # AUM
    aum = details.get("aum", "")
    aum_display = f"{aum:,.2f} Cr" if isinstance(aum, (int, float)) else str(aum)
    lines.append("FUND SIZE")
    lines.append("-" * 40)
    lines.append(f"  AUM:              {aum_display}")
    lines.append(f"  Turnover:         {details.get('portfolio_turnover', 'N/A')}%")
    lines.append("")

    # Minimum Investment
    min_inv = details.get("min_investment", {})
    lines.append("MINIMUM INVESTMENT")
    lines.append("-" * 40)
    lines.append(f"  Lumpsum:          Rs. {min_inv.get('lumpsum', 'N/A')}")
    lines.append(f"  SIP:              Rs. {min_inv.get('sip', 'N/A')}")
    lines.append(f"  Additional:       Rs. {min_inv.get('additional', 'N/A')}")
    lines.append("")

    # Lock-in
    lock_in = details.get("lock_in", {})
    if lock_in:
        lines.append("LOCK-IN PERIOD")
        lines.append("-" * 40)
        for k, v in lock_in.items():
            lines.append(f"  {k}: {v}")
        lines.append("")

    # Returns
    simple_return = details.get("simple_return", {})
    if simple_return:
        lines.append("LUMPSUM RETURNS")
        lines.append("-" * 40)
        for period, value in simple_return.items():
            if isinstance(value, (int, float)):
                lines.append(f"  {period}: {value}%")
        lines.append("")

    sip_return = details.get("sip_return", {})
    if sip_return:
        lines.append("SIP RETURNS (XIRR)")
        lines.append("-" * 40)
        for period, value in sip_return.items():
            if isinstance(value, (int, float)):
                lines.append(f"  {period}: {value}%")
        lines.append("")

    # Top Holdings
    top_holdings = details.get("top_holdings", [])
    if top_holdings:
        lines.append("TOP HOLDINGS")
        lines.append("-" * 40)
        for i, h in enumerate(top_holdings, 1):
            pct = h.get("percentage", "?")
            name = h.get("name", "N/A")
            sector = h.get("sector", "")
            sector_str = f" ({sector})" if sector else ""
            lines.append(f"  {i:2d}. {name}{sector_str} - {pct}%")
        lines.append("")

    # Fund Manager Details
    fm_details = details.get("fund_manager_details", [])
    if fm_details:
        lines.append("FUND MANAGER DETAILS")
        lines.append("-" * 40)
        for fm in fm_details:
            lines.append(f"  {fm.get('name', 'N/A')} (Exp: {fm.get('experience', 'N/A')})")
        lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Extracting structured data from Groww HTML pages")
    print("=" * 60)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    for source in metadata["sources"]:
        source_id = source["id"]
        scheme = source["scheme"]
        html_file = RAW_GROWW_DIR / f"{source_id}.html"
        json_file = PROCESSED_DIR / f"{source_id}_data.json"
        txt_file = PROCESSED_DIR / f"{source_id}.txt"

        if not html_file.exists():
            print(f"\n[SKIP] {source_id}: HTML file not found")
            continue

        print(f"\n[{source_id}] {scheme}")

        # Step 1: Extract raw JSON data
        raw_data = extract_json_data(html_file)
        if not raw_data:
            print(f"  ERROR: No JSON data found in HTML")
            continue

        # Step 2: Extract structured scheme details
        details = extract_scheme_details(raw_data)

        # Step 3: Save structured JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(details, f, indent=2, ensure_ascii=False, default=str)
        print(f"  JSON: {json_file.relative_to(PROJECT_ROOT)} ({len(json.dumps(details)):,} chars)")

        # Step 4: Save human-readable text
        readable = format_as_readable_text(details, source)
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(readable)
        print(f"  Text: {txt_file.relative_to(PROJECT_ROOT)} ({len(readable):,} chars)")

        # Print quick summary
        print(f"  NAV:      {details.get('nav', {}).get('current_nav', 'N/A')}")
        print(f"  Expense:  {details.get('expense_ratio', 'N/A')}")
        print(f"  AUM:      {details.get('aum', 'N/A')}")

    print(f"\n{'='*60}")
    print(f"Review files in: data/processed/")
    print(f"  *_data.json  = Structured JSON (for ingestion)")
    print(f"  *.txt        = Human-readable text (for review)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
