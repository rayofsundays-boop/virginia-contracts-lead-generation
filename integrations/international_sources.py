import os
import requests
from datetime import datetime
from typing import List, Dict, Any

UK_BASE = "https://www.contractsfinder.service.gov.uk"
UK_SEARCH = UK_BASE + "/Published/Notices/OCDS/Search"


def _safe_get(d: dict, path: list, default=None):
    cur = d
    try:
        for p in path:
            if isinstance(cur, dict):
                cur = cur.get(p)
            elif isinstance(cur, list) and isinstance(p, int):
                cur = cur[p]
            else:
                return default
        return cur if cur is not None else default
    except Exception:
        return default


def fetch_uk_contracts_finder_cleaning(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch open cleaning-related opportunities from UK Contracts Finder (OCDS Search API).
    Returns a list of records mapped to supply_contracts fields.
    """
    params = {
        "limit": str(max(1, min(limit, 200))),
        "noticetype": "Opportunity",
        "keyword": "cleaning",
    }
    try:
        r = requests.get(UK_SEARCH, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        releases = data.get("releases", [])
        mapped = []
        for rel in releases:
            tender = rel.get("tender", {})
            parties = rel.get("parties", [])
            buyer = rel.get("buyer") or {}

            # Contact details from buyer party if present
            contact_name = None
            contact_email = None
            contact_phone = None
            agency = buyer.get("name")

            if parties:
                for p in parties:
                    roles = set(p.get("roles", []))
                    if "buyer" in roles:
                        agency = agency or p.get("name")
                        cp = p.get("contactPoint", {})
                        contact_name = cp.get("name") or contact_name
                        contact_email = cp.get("email") or contact_email
                        contact_phone = cp.get("telephone") or contact_phone
                        if agency and (contact_email or contact_phone):
                            break

            # Value and deadlines
            value = _safe_get(tender, ["value", "amount"]) or 0
            try:
                value = int(float(value))
            except Exception:
                value = 0

            deadline = _safe_get(tender, ["tenderPeriod", "endDate"]) or ""
            # Normalize to MM/DD/YYYY if possible
            bid_deadline = ""
            if deadline:
                try:
                    dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                    bid_deadline = dt.strftime("%m/%d/%Y")
                except Exception:
                    bid_deadline = deadline

            # Main URL - prefer a document URL
            url = None
            docs = []
            for sec in (rel.get("tender", {}), ) + tuple(rel.get(k, {}) for k in ("awards", "contracts")):
                if isinstance(sec, dict):
                    docs = sec.get("documents", []) or docs
                elif isinstance(sec, list):
                    for e in sec:
                        docs = e.get("documents", []) or docs
            if docs:
                url = docs[0].get("url")
            if not url:
                # Fallback to Contracts Finder Notice if id present
                rel_id = rel.get("id")
                if rel_id:
                    url = f"{UK_BASE}/Notice/{rel_id}"

            location = "United Kingdom"
            # Try to derive region/country if present
            items = tender.get("items", [])
            if items:
                addr = _safe_get(items[0], ["deliveryAddresses", 0, "countryName"]) or _safe_get(items[0], ["deliveryAddresses", 0, "region"]) 
                if addr:
                    location = addr

            mapped.append({
                "title": tender.get("title") or "Cleaning Services / Supplies",
                "agency": agency or "UK Public Sector",
                "location": location,
                "product_category": "Cleaning Services",
                "estimated_value": str(value) if value else None,
                "bid_deadline": bid_deadline,
                "description": tender.get("description") or "",
                "website_url": url,
                "is_small_business_set_aside": False,
                "contact_name": contact_name,
                "contact_email": contact_email,
                "contact_phone": contact_phone,
                "is_quick_win": True,
                "status": tender.get("status") or "open",
                "posted_date": rel.get("date") or "",
            })
        return mapped
    except Exception:
        return []


def fetch_international_cleaning(limit_per_source: int = 50) -> List[Dict[str, Any]]:
    """Aggregate multiple international sources (currently UK Contracts Finder)."""
    results: List[Dict[str, Any]] = []
    try:
        results += fetch_uk_contracts_finder_cleaning(limit=limit_per_source)
    except Exception:
        pass
    return results
