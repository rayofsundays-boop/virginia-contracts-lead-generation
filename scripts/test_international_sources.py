import os
from pprint import pprint

# Ensure package imports work when running as a script
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from integrations.international_sources import (
    fetch_international_cleaning,
    fetch_uk_contracts_finder_cleaning,
    fetch_rss_cleaning_generic,
    fetch_rss_eu_cleaning,
    fetch_rss_canada_cleaning,
)


def main():
    limit = int(os.environ.get('TEST_LIMIT', '10'))

    print("== Smoke test: UK Contracts Finder (cleaning) ==")
    uk = fetch_uk_contracts_finder_cleaning(limit=limit)
    print(f"UK results: {len(uk)}")
    pprint(uk[:3])

    print("\n== Smoke test: Generic RSS (INTERNATIONAL_RSS_URL) ==")
    rss = fetch_rss_cleaning_generic(limit=limit)
    print(f"RSS results: {len(rss)}")
    pprint(rss[:3])

    print("\n== Optional: EU RSS (EU_RSS_URL) ==")
    eu = fetch_rss_eu_cleaning(limit=limit)
    print(f"EU RSS results: {len(eu)}")
    pprint(eu[:3])

    print("\n== Optional: Canada RSS (CANADA_RSS_URL) ==")
    ca = fetch_rss_canada_cleaning(limit=limit)
    print(f"Canada RSS results: {len(ca)}")
    pprint(ca[:3])

    print("\n== Aggregated (international) ==")
    agg = fetch_international_cleaning(limit_per_source=limit)
    print(f"Total international results: {len(agg)}")
    pprint(agg[:5])


if __name__ == "__main__":
    main()
