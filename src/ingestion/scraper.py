from __future__ import annotations

"""
Ingestion — Scraper / Document Loader

Loads pre-processed mutual fund scheme data from disk (produced by
Phase 2's download + extract pipeline).  Two loading modes:

  • Structured JSON → flattens into natural-language paragraphs
  • Raw text          → returns the human-readable .txt dump as-is

Both modes attach rich metadata (scheme_name, source_url, category, etc.)
so every downstream chunk is fully traceable.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.config import (
    METADATA_FILE,
    PROCESSED_DATA_DIR,
)


# ───────────────────────────────────────────────────────────
# Data-classes (plain dicts — no extra deps)
# ───────────────────────────────────────────────────────────

def _build_metadata(source: dict) -> dict:
    """Build a canonical metadata dict for a single source entry."""
    return {
        "source_id": source["id"],
        "scheme_name": source["scheme"],
        "source_url": source["url"],
        "category": source.get("category", ""),
        "format": source.get("format", "html"),
        "downloaded_at": source.get("downloaded_at", ""),
        "ingestion_date": datetime.now(timezone.utc).isoformat(),
    }


# ───────────────────────────────────────────────────────────
# JSON → Natural-language paragraphs
# ───────────────────────────────────────────────────────────

def _flatten_json_to_text(data: dict, source: dict) -> str:
    """Convert structured scheme JSON into natural-language paragraphs.

    Produces longer, more coherent text passages that chunk well with
    RecursiveCharacterTextSplitter.
    """
    parts: list[str] = []

    scheme = data.get("scheme_name", source.get("scheme", "Unknown"))
    parts.append(f"Scheme: {scheme}")

    # ── Basic info ──
    info_lines = []
    if data.get("amc_name"):
        info_lines.append(f"AMC (Asset Management Company): {data['amc_name']}")
    if data.get("category"):
        info_lines.append(f"Category: {data['category']}")
    if data.get("sub_category"):
        info_lines.append(f"Sub-Category: {data['sub_category']}")
    if data.get("plan_type"):
        info_lines.append(f"Plan Type: {data['plan_type']}")
    if data.get("scheme_type"):
        info_lines.append(f"Scheme Type: {data['scheme_type']}")
    if data.get("launch_date"):
        info_lines.append(f"Launch Date: {data['launch_date']}")
    if data.get("benchmark"):
        info_lines.append(f"Benchmark Index: {data['benchmark']}")
    if data.get("risk_level"):
        info_lines.append(f"Risk Level (Riskometer): {data['risk_level']}")
    if data.get("fund_manager"):
        info_lines.append(f"Fund Manager: {data['fund_manager']}")
    if data.get("isin"):
        info_lines.append(f"ISIN: {data['isin']}")
    if info_lines:
        parts.append("Scheme Information:\n" + "\n".join(info_lines))

    # ── Description ──
    if data.get("description"):
        parts.append(f"Investment Objective: {data['description']}")

    # ── NAV ──
    nav = data.get("nav", {})
    if nav.get("current_nav"):
        parts.append(
            f"Current NAV of {scheme} is ₹{nav['current_nav']} "
            f"as of {nav.get('nav_date', 'N/A')}."
        )

    # ── Costs ──
    cost_lines = []
    if data.get("expense_ratio"):
        cost_lines.append(f"Expense Ratio: {data['expense_ratio']}%")
    if data.get("exit_load"):
        cost_lines.append(f"Exit Load: {data['exit_load']}")
    if data.get("stamp_duty"):
        cost_lines.append(f"Stamp Duty: {data['stamp_duty']}")
    if cost_lines:
        parts.append("Costs & Fees:\n" + "\n".join(cost_lines))

    # ── AUM ──
    aum = data.get("aum")
    if aum:
        aum_str = f"₹{aum:,.2f} Cr" if isinstance(aum, (int, float)) else str(aum)
        parts.append(f"Assets Under Management (AUM): {aum_str}")

    # ── Minimum investment ──
    mi = data.get("min_investment", {})
    if mi:
        mi_lines = []
        if mi.get("lumpsum"):
            mi_lines.append(f"Minimum Lumpsum Investment: ₹{mi['lumpsum']}")
        if mi.get("sip"):
            mi_lines.append(f"Minimum SIP Investment: ₹{mi['sip']}")
        if mi.get("additional"):
            mi_lines.append(f"Minimum Additional Investment: ₹{mi['additional']}")
        if mi_lines:
            parts.append("Minimum Investment Details:\n" + "\n".join(mi_lines))

    # ── Lock-in ──
    lock = data.get("lock_in", {})
    if lock:
        years = lock.get("years", 0)
        months = lock.get("months", 0)
        days = lock.get("days", 0)
        if years or months or days:
            lock_parts = []
            if years:
                lock_parts.append(f"{years} year{'s' if years > 1 else ''}")
            if months:
                lock_parts.append(f"{months} month{'s' if months > 1 else ''}")
            if days:
                lock_parts.append(f"{days} day{'s' if days > 1 else ''}")
            parts.append(f"Lock-in Period: {', '.join(lock_parts)}")
        else:
            parts.append("Lock-in Period: None")

    # ── Returns ──
    sr = data.get("simple_return", {})
    if sr:
        ret_lines = []
        label_map = {
            "return1y": "1 Year", "return3y": "3 Year", "return5y": "5 Year",
            "return10y": "10 Year", "return_since_created": "Since Inception",
        }
        for key, label in label_map.items():
            val = sr.get(key)
            if val is not None:
                ret_lines.append(f"{label} Return: {val}%")
        if ret_lines:
            parts.append("Lumpsum Returns:\n" + "\n".join(ret_lines))

    sip = data.get("sip_return", {})
    if sip:
        sip_lines = []
        label_map = {
            "return1y": "1 Year", "return3y": "3 Year", "return5y": "5 Year",
            "return10y": "10 Year",
        }
        for key, label in label_map.items():
            val = sip.get(key)
            if val is not None:
                sip_lines.append(f"{label} SIP Return (XIRR): {val}%")
        if sip_lines:
            parts.append("SIP Returns:\n" + "\n".join(sip_lines))

    # ── Return stats (CAGR + risk metrics) ──
    rstats = data.get("return_stats", [])
    if rstats and isinstance(rstats, list) and len(rstats) > 0:
        rs = rstats[0]
        risk_lines = []
        if rs.get("sharpe_ratio") is not None:
            risk_lines.append(f"Sharpe Ratio: {rs['sharpe_ratio']:.4f}")
        if rs.get("sortino_ratio") is not None:
            risk_lines.append(f"Sortino Ratio: {rs['sortino_ratio']:.4f}")
        if rs.get("beta") is not None:
            risk_lines.append(f"Beta: {rs['beta']:.4f}")
        if rs.get("alpha") is not None:
            risk_lines.append(f"Alpha: {rs['alpha']:.4f}")
        if rs.get("standard_deviation") is not None:
            risk_lines.append(f"Standard Deviation: {rs['standard_deviation']:.2f}")
        if risk_lines:
            parts.append("Risk & Performance Metrics:\n" + "\n".join(risk_lines))

    # ── Holdings ──
    holdings = data.get("top_holdings", [])
    if holdings:
        h_lines = []
        for i, h in enumerate(holdings, 1):
            sector = f" ({h.get('sector', '')})" if h.get("sector") else ""
            h_lines.append(f"{i}. {h.get('name', 'N/A')}{sector} — {h.get('percentage', '?')}%")
        parts.append("Top Holdings:\n" + "\n".join(h_lines))

    # ── Fund manager details ──
    fmds = data.get("fund_manager_details", [])
    if fmds:
        for fm in fmds:
            name = fm.get("name", "")
            exp = fm.get("experience", "")
            if name or exp:
                parts.append(f"Fund Manager: {name}. {exp}".strip())

    # ── Category/Tax info ──
    cat_info = data.get("category_info", {})
    if cat_info:
        if cat_info.get("tax_impact"):
            parts.append(f"Tax Impact: {cat_info['tax_impact']}")
        if cat_info.get("description"):
            parts.append(f"Category Description: {cat_info['description']}")

    return "\n\n".join(parts)


# ───────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────

def load_document_from_json(source: dict) -> tuple[str, dict]:
    """Load a single scheme's structured JSON and return (text, metadata).

    Args:
        source: A single entry from ``metadata.json["sources"]``.

    Returns:
        (clean_text, metadata_dict)
    """
    json_path = PROCESSED_DATA_DIR / f"{source['id']}_data.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Processed JSON not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    text = _flatten_json_to_text(data, source)
    metadata = _build_metadata(source)
    return text, metadata


def load_document_from_text(source: dict) -> tuple[str, dict]:
    """Load a single scheme's human-readable text file and return (text, metadata).

    Args:
        source: A single entry from ``metadata.json["sources"]``.

    Returns:
        (clean_text, metadata_dict)
    """
    txt_path = PROCESSED_DATA_DIR / f"{source['id']}.txt"
    if not txt_path.exists():
        raise FileNotFoundError(f"Processed text not found: {txt_path}")

    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    metadata = _build_metadata(source)
    return text, metadata


def load_all_documents(
    mode: str = "json",
    metadata_path: Optional[Path] = None,
) -> list[tuple[str, dict]]:
    """Load all scheme documents from processed data.

    Args:
        mode: ``"json"`` (structured → NL paragraphs) or ``"text"`` (raw .txt).
        metadata_path: Override for ``metadata.json`` path (useful for tests).

    Returns:
        List of (text, metadata) tuples — one per scheme.
    """
    meta_file = metadata_path or METADATA_FILE
    with open(meta_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    loader = load_document_from_json if mode == "json" else load_document_from_text
    documents: list[tuple[str, dict]] = []

    for source in metadata["sources"]:
        try:
            doc = loader(source)
            documents.append(doc)
        except FileNotFoundError as e:
            print(f"[WARN] Skipping {source['id']}: {e}")

    return documents
