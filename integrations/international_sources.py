import os
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
logger = logging.getLogger(__name__)

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


def _normalize_value(raw: Any) -> Optional[int]:
    """Best-effort normalization of a monetary value to an integer amount in base currency.
    Returns None when ambiguous or not parseable. Logs a warning on ambiguity.
    """
    if raw is None:
        return None
    try:
        if isinstance(raw, (int, float)):
            return int(float(raw))
        # Remove common currency symbols and thousands separators
        cleaned = ''.join(c for c in str(raw) if c.isdigit() or c == '.')
        if cleaned.count('.') > 1 or cleaned == '':
            logger.warning("international_sources: ambiguous value '%s'", raw)
            return None
        return int(float(cleaned))
    except Exception:
        logger.warning("international_sources: failed to parse value '%s'", raw)
        return None


def _normalize_deadline(raw: Any) -> str:
    """Normalize various date formats to MM/DD/YYYY. Returns '' when unavailable.
    Accepts ISO strings; tries several common formats.
    """
    if not raw:
        return ''
    s = str(raw)
    # Contracts Finder often uses ISO 8601
    try:
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
        return dt.strftime('%m/%d/%Y')
    except Exception:
        pass
    # Try common human formats
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%m/%d/%y'):
        try:
            return datetime.strptime(s, fmt).strftime('%m/%d/%Y')
        except Exception:
            continue
    logger.warning("international_sources: unrecognized deadline format '%s'", s)
    return s  # Return original for visibility if we couldn't parse


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
            raw_value = _safe_get(tender, ["value", "amount"])  # could be str/float/int/None
            value = _normalize_value(raw_value)
            if value is None:
                logger.warning("UK CF: missing/ambiguous value for '%s' (id=%s)", tender.get("title"), rel.get("id"))

            raw_deadline = _safe_get(tender, ["tenderPeriod", "endDate"]) or ""
            bid_deadline = _normalize_deadline(raw_deadline)
            if not bid_deadline:
                logger.warning("UK CF: missing deadline for '%s' (id=%s)", tender.get("title"), rel.get("id"))

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
            if not url:
                logger.warning("UK CF: missing URL for '%s' (id=%s)", tender.get("title"), rel.get("id"))

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
                "estimated_value": str(value) if value is not None else None,
                "bid_deadline": bid_deadline or None,
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
        logger.exception("UK CF: fetch failed")
        return []


def fetch_international_cleaning(limit_per_source: int = 50) -> List[Dict[str, Any]]:
    """Aggregate multiple international sources (currently UK Contracts Finder)."""
    results: List[Dict[str, Any]] = []
    try:
        results += fetch_uk_contracts_finder_cleaning(limit=limit_per_source)
    except Exception:
        pass
    # Generic RSS adapter (configurable via env var INTERNATIONAL_RSS_URL)
    try:
        results += fetch_rss_cleaning_generic(limit=limit_per_source)
    except Exception:
        logger.warning("Generic RSS adapter failed; continuing with other sources")
    # Placeholder for additional sources to keep adapters small and testable
    try:
        results += fetch_canada_pspc_cleaning(limit=limit_per_source)
    except Exception:
        # Keep failure isolated to the source adapter
        logger.warning("Canada PSPC adapter failed; continuing with other sources")
    return results


def fetch_canada_pspc_cleaning(limit: int = 50) -> List[Dict[str, Any]]:
    """Placeholder adapter for Canada PSPC/TPSGC (Buyandsell successor) cleaning opportunities.

    Implementation note:
    - When enabling, fetch from the official API if available.
    - Map to keys used by supply_contracts just like UK CF.
    - Normalize values and deadlines with _normalize_value/_normalize_deadline.
    - Log warnings for missing/ambiguous fields.

    Returns empty list by default to avoid unexpected network calls.
    """
    logger.info("Canada PSPC adapter is not yet implemented; returning empty list.")
    return []


def fetch_rss_cleaning_generic(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch cleaning-related opportunities from a generic RSS feed.

    Configure feed URL with env var INTERNATIONAL_RSS_URL.
    The function filters items whose title or description contains 'cleaning'.
    This is a flexible, real adapter that can be pointed at any public procurement RSS.
    """
    import xml.etree.ElementTree as ET

    rss_url = os.environ.get('INTERNATIONAL_RSS_URL', '').strip()
    if not rss_url:
        logger.info("Generic RSS adapter disabled (INTERNATIONAL_RSS_URL not set)")
        return []

    try:
        r = requests.get(rss_url, timeout=20)
        r.raise_for_status()
        content = r.content
        try:
            root = ET.fromstring(content)
        except Exception as e:
            logger.exception("RSS parse error")
            return []

        ns = {
            'rss': 'http://purl.org/rss/1.0/'
        }
        items: List[Dict[str, Any]] = []

        # Support both RSS 2.0 and Atom-ish structures
        channel = root.find('channel')
        if channel is not None:
            entries = channel.findall('item')
        else:
            entries = root.findall('.//item')

        for it in entries[:max(1, min(limit, 200))]:
            title = (it.findtext('title') or '').strip()
            link = (it.findtext('link') or '').strip()
            description = (it.findtext('description') or '').strip()
            pub_date = (it.findtext('pubDate') or '').strip()

            text_blob = f"{title}\n{description}".lower()
            if 'clean' not in text_blob:
                # Skip non-cleaning entries
                continue

            mapped: Dict[str, Any] = {
                'title': title or 'Cleaning Services / Supplies',
                'agency': 'International Procurement',
                'location': 'International',
                'product_category': 'Cleaning Services',
                'estimated_value': None,
                'bid_deadline': _normalize_deadline(pub_date),
                'description': description,
                'website_url': link or None,
                'is_small_business_set_aside': False,
                'contact_name': None,
                'contact_email': None,
                'contact_phone': None,
                'is_quick_win': True,
                'status': 'open',
                'posted_date': pub_date,
            }
            items.append(mapped)

        return items
    except Exception:
        logger.exception("Generic RSS fetch failed")
        return []
