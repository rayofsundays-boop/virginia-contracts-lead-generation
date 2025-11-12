import os
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
logger = logging.getLogger(__name__)

UK_BASE = "https://www.contractsfinder.service.gov.uk"
UK_SEARCH = UK_BASE + "/Published/Notices/OCDS/Search"

# NAICS 561720 (Janitorial Services), 561790 (Other Services to Buildings), 561730 (Landscaping/Snow Removal)
# Keywords that match cleaning/janitorial industry scope
CLEANING_KEYWORDS = {
    'cleaning', 'janitorial', 'custodial', 'housekeeping', 'sanitation',
    'disinfection', 'hygiene', 'floor care', 'carpet cleaning', 'window cleaning',
    'waste management', 'trash removal', 'facilities maintenance', 'building services',
    'porter services', 'environmental services', 'grounds maintenance', 'snow removal'
}

# Exclude contracts that are NOT physical cleaning (IT, software, data, consulting, etc.)
EXCLUDE_KEYWORDS = {
    'data cleaning', 'data model', 'data management', 'database', 'data warehouse',
    'software', 'IT services', 'cloud', 'digital', 'cyber', 'information technology',
    'consulting', 'advisory', 'analytics', 'data science', 'machine learning',
    'development', 'programming', 'coding', 'application', 'system integration',
    'enterprise data', 'data governance', 'metadata', 'data quality',
    'business intelligence', 'reporting', 'dashboard', 'ETL', 'data pipeline'
}

def _matches_cleaning_naics(text: str) -> bool:
    """Check if text contains cleaning/janitorial keywords matching NAICS 561720/561790/561730.
    Excludes IT/software/data contracts that use 'cleaning' in non-physical context.
    """
    if not text:
        return False
    text_lower = text.lower()
    
    # First check if any exclude keywords are present (IT, data, software)
    if any(keyword in text_lower for keyword in EXCLUDE_KEYWORDS):
        return False
    
    # Then check if valid cleaning keywords are present
    return any(keyword in text_lower for keyword in CLEANING_KEYWORDS)


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
    Filters for NAICS 561720/561790/561730-related services (janitorial, facilities, building services).
    Returns a list of records mapped to supply_contracts fields.
    """
    # Search with broader keywords to catch all cleaning/janitorial opportunities
    # UK Contracts Finder doesn't support multiple keywords, so we'll search and filter
    params = {
        "limit": str(max(1, min(limit, 200))),
        "noticetype": "Opportunity",
        "keyword": "cleaning janitorial",  # Combined search
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
        
        # Filter to only include contracts matching NAICS 561720/561790/561730 keywords
        filtered_mapped = []
        for contract in mapped:
            title = contract.get('title', '')
            description = contract.get('description', '')
            combined_text = f"{title} {description}"
            
            if _matches_cleaning_naics(combined_text):
                filtered_mapped.append(contract)
            else:
                logger.info("UK CF: Filtered out non-NAICS match: '%s'", title)
        
        logger.info("UK CF: Fetched %d contracts, %d match NAICS cleaning codes", len(mapped), len(filtered_mapped))
        return filtered_mapped
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
    # Optional: Multiple generic RSS URLs (comma-separated)
    try:
        urls = os.environ.get('INTERNATIONAL_RSS_URLS', '')
        if urls:
            for u in [s.strip() for s in urls.split(',') if s.strip()]:
                results += fetch_rss_from_url(u, source_label='International RSS')[:limit_per_source]
    except Exception:
        logger.warning("Multi RSS adapter failed; continuing")
    # Placeholder for additional sources to keep adapters small and testable
    try:
        results += fetch_canada_pspc_cleaning(limit=limit_per_source)
    except Exception:
        # Keep failure isolated to the source adapter
        logger.warning("Canada PSPC adapter failed; continuing with other sources")
    # EU RSS (if configured)
    try:
        results += fetch_rss_eu_cleaning(limit=limit_per_source)
    except Exception:
        logger.warning("EU RSS adapter failed; continuing")
    # Canada RSS (if configured)
    try:
        results += fetch_rss_canada_cleaning(limit=limit_per_source)
    except Exception:
        logger.warning("Canada RSS adapter failed; continuing")
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

            text_blob = f"{title}\n{description}"
            # Filter by NAICS-relevant cleaning keywords
            if not _matches_cleaning_naics(text_blob):
                # Skip non-NAICS cleaning entries
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


def fetch_rss_from_url(url: str, source_label: str = 'RSS', limit: int = 50) -> List[Dict[str, Any]]:
    """Helper to parse an RSS feed URL and map cleaning-related entries.

    Filters by 'clean' in title/description.
    """
    import xml.etree.ElementTree as ET
    if not url:
        return []
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        channel = root.find('channel')
        entries = channel.findall('item') if channel is not None else root.findall('.//item')
        out: List[Dict[str, Any]] = []
        for it in entries[:max(1, min(limit, 200))]:
            title = (it.findtext('title') or '').strip()
            link = (it.findtext('link') or '').strip()
            description = (it.findtext('description') or '').strip()
            pub_date = (it.findtext('pubDate') or '').strip()
            # Filter by NAICS-relevant cleaning keywords
            if not _matches_cleaning_naics(f"{title}\n{description}"):
                continue
            out.append({
                'title': title or 'Cleaning Services / Supplies',
                'agency': source_label,
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
            })
        return out
    except Exception:
        logger.exception("RSS fetch failed for %s", url)
        return []


def fetch_rss_eu_cleaning(limit: int = 50) -> List[Dict[str, Any]]:
    """EU cleaning opportunities via RSS if EU_RSS_URL is configured.

    Provide an EU RSS URL (e.g., a TED search feed) in EU_RSS_URL.
    """
    url = os.environ.get('EU_RSS_URL', '').strip()
    if not url:
        return []
    return fetch_rss_from_url(url, source_label='EU Procurement', limit=limit)


def fetch_rss_canada_cleaning(limit: int = 50) -> List[Dict[str, Any]]:
    """Canada cleaning opportunities via RSS if CANADA_RSS_URL is configured."""
    url = os.environ.get('CANADA_RSS_URL', '').strip()
    if not url:
        return []
    return fetch_rss_from_url(url, source_label='Canada Procurement', limit=limit)
