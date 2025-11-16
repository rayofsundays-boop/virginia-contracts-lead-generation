"""
Nationwide Scraper Validation Test - ALL 51 JURISDICTIONS
Tests every state scraper with live calls and verifies output format
"""

import json
import logging
from datetime import datetime
from scrapers.state_portal_scraper_v2 import StatePortalScraperV2
from scrapers.eva_virginia_scraper_v2 import EVAVirginiaScraperV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_contract_format(contract: dict, state: str) -> bool:
    """
    Validate contract matches standardized format
    
    Required fields:
    - state (2-letter code)
    - title (non-empty)
    - solicitation_number
    - due_date
    - link
    - agency
    """
    required_fields = ['state', 'title', 'solicitation_number', 'due_date', 'link', 'agency']
    
    for field in required_fields:
        if field not in contract:
            logger.error(f"❌ {state}: Missing field '{field}'")
            return False
    
    # Validate state code
    if contract['state'] != state:
        logger.warning(f"⚠️  {state}: State mismatch (got '{contract['state']}')")
    
    # Validate title not empty
    if not contract['title'] or len(contract['title'].strip()) == 0:
        logger.warning(f"⚠️  {state}: Empty title")
        return False
    
    return True


def test_single_state(scraper, state_code: str) -> dict:
    """
    Test single state scraper
    
    Returns:
        dict with status, contracts_found, sample_contracts
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"TESTING: {state_code}")
    logger.info(f"{'='*70}\n")
    
    result = {
        'state': state_code,
        'status': 'unknown',
        'contracts_found': 0,
        'valid_contracts': 0,
        'sample_contracts': [],
        'errors': []
    }
    
    try:
        contracts = scraper._scrape_state(state_code)
        
        result['contracts_found'] = len(contracts)
        
        if len(contracts) == 0:
            result['status'] = 'NO_RESULTS'
            logger.warning(f"⚠️  {state_code}: No contracts found (may be none posted)")
        else:
            # Validate first 10 contracts
            valid_count = 0
            for i, contract in enumerate(contracts[:10]):
                if validate_contract_format(contract, state_code):
                    valid_count += 1
                    if i < 3:  # Save first 3 as samples
                        result['sample_contracts'].append(contract)
            
            result['valid_contracts'] = valid_count
            
            if valid_count > 0:
                result['status'] = 'SUCCESS'
                logger.info(f"✅ {state_code}: {valid_count}/{len(contracts[:10])} contracts valid")
            else:
                result['status'] = 'INVALID_FORMAT'
                logger.error(f"❌ {state_code}: No valid contracts (format errors)")
        
        # Print first 3 contracts
        if result['sample_contracts']:
            logger.info(f"\n📄 Sample Contracts from {state_code}:")
            for i, contract in enumerate(result['sample_contracts'], 1):
                logger.info(f"\n  {i}. {contract['title']}")
                logger.info(f"     Number: {contract['solicitation_number']}")
                logger.info(f"     Agency: {contract['agency']}")
                logger.info(f"     Due: {contract['due_date']}")
                logger.info(f"     Link: {contract['link'][:80]}...")
    
    except Exception as e:
        result['status'] = 'FAILED'
        result['errors'].append(str(e))
        logger.error(f"❌ {state_code}: FAILED - {e}")
    
    return result


def test_critical_broken_states():
    """Test states that were previously broken"""
    logger.info("\n" + "="*70)
    logger.info("🔴 TESTING CRITICAL BROKEN STATES (Previously Failing)")
    logger.info("="*70 + "\n")
    
    critical_states = {
        'VA': 'Virginia eVA - 404 (old domain dead, new POST endpoint)',
        'FL': 'Florida - 404 (VBS obsolete, new marketplace)',
        'NE': 'Nebraska - 403 (needed enhanced headers)',
        'NV': 'Nevada - missing re import',
        'GA': 'Georgia - missing re import',
        'HI': 'Hawaii - missing re import',
        'AK': 'Alaska - DNS failure (old domain dead)'
    }
    
    scraper = StatePortalScraperV2(rate_limit=3.0)
    results = []
    
    for state, issue in critical_states.items():
        logger.info(f"\n🔧 {state}: {issue}")
        result = test_single_state(scraper, state)
        results.append(result)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("🔴 CRITICAL STATES SUMMARY")
    logger.info("="*70 + "\n")
    
    for result in results:
        status_emoji = {
            'SUCCESS': '✅',
            'NO_RESULTS': '⚠️ ',
            'FAILED': '❌',
            'INVALID_FORMAT': '❌'
        }.get(result['status'], '❓')
        
        logger.info(f"{status_emoji} {result['state']}: {result['status']} "
                   f"({result['contracts_found']} found, {result['valid_contracts']} valid)")
    
    return results


def test_all_states():
    """Test ALL 51 jurisdictions"""
    logger.info("\n" + "="*70)
    logger.info("🌎 TESTING ALL 51 JURISDICTIONS (50 States + DC)")
    logger.info("="*70 + "\n")
    
    scraper = StatePortalScraperV2(rate_limit=2.0)
    
    all_states = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
        'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
        'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
        'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
        'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    ]
    
    results = []
    
    for state in all_states:
        result = test_single_state(scraper, state)
        results.append(result)
    
    # Final Summary
    logger.info("\n" + "="*70)
    logger.info("🌎 COMPLETE TEST SUMMARY - ALL 51 JURISDICTIONS")
    logger.info("="*70 + "\n")
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    no_results_count = sum(1 for r in results if r['status'] == 'NO_RESULTS')
    failed_count = sum(1 for r in results if r['status'] == 'FAILED')
    invalid_count = sum(1 for r in results if r['status'] == 'INVALID_FORMAT')
    total_contracts = sum(r['contracts_found'] for r in results)
    
    logger.info(f"✅ SUCCESS: {success_count}/{len(all_states)} states")
    logger.info(f"⚠️  NO RESULTS: {no_results_count}/{len(all_states)} states (no bids posted)")
    logger.info(f"❌ FAILED: {failed_count}/{len(all_states)} states")
    logger.info(f"❌ INVALID FORMAT: {invalid_count}/{len(all_states)} states")
    logger.info(f"📊 TOTAL CONTRACTS: {total_contracts} across all states")
    
    # List failed states
    if failed_count > 0:
        logger.info("\n❌ FAILED STATES:")
        for result in results:
            if result['status'] == 'FAILED':
                logger.info(f"  - {result['state']}: {result['errors']}")
    
    # Export results to JSON
    output_file = f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n💾 Results exported to: {output_file}")
    
    return results


def test_virginia_eva_detailed():
    """Detailed test of Virginia eVA with NEW POST endpoint"""
    logger.info("\n" + "="*70)
    logger.info("🔵 VIRGINIA eVA DETAILED TEST (NEW POST ENDPOINT)")
    logger.info("="*70 + "\n")
    
    scraper = EVAVirginiaScraperV2(rate_limit=3.0)
    
    try:
        contracts = scraper.scrape()
        
        logger.info(f"✅ eVA Success: {len(contracts)} contracts found\n")
        
        # Validate format
        valid_count = 0
        for contract in contracts[:10]:
            if validate_contract_format(contract, 'VA'):
                valid_count += 1
        
        logger.info(f"📊 {valid_count}/{min(len(contracts), 10)} contracts have valid format\n")
        
        # Show first 5 contracts
        logger.info("📄 First 5 Contracts:\n")
        for i, contract in enumerate(contracts[:5], 1):
            logger.info(f"{i}. {contract['title']}")
            logger.info(f"   Sol #: {contract['solicitation_number']}")
            logger.info(f"   Agency: {contract['agency']}")
            logger.info(f"   Due: {contract['due_date']}")
            logger.info(f"   Link: {contract['link']}\n")
        
        return {
            'status': 'SUCCESS',
            'contracts_found': len(contracts),
            'valid_contracts': valid_count,
            'sample_contracts': contracts[:3]
        }
    
    except Exception as e:
        logger.error(f"❌ eVA Failed: {e}")
        return {
            'status': 'FAILED',
            'error': str(e)
        }


def main():
    """Main test execution"""
    logger.info("\n" + "="*70)
    logger.info("🚀 NATIONWIDE PROCUREMENT SCRAPER VALIDATION")
    logger.info("="*70)
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70 + "\n")
    
    # Test 1: Critical broken states
    logger.info("PHASE 1: Testing Previously Broken States...")
    critical_results = test_critical_broken_states()
    
    input("\n⏸️  Press Enter to continue to full nationwide test...")
    
    # Test 2: Virginia eVA detailed
    logger.info("\nPHASE 2: Virginia eVA Detailed Test...")
    eva_result = test_virginia_eva_detailed()
    
    input("\n⏸️  Press Enter to test ALL 51 jurisdictions (will take 10-15 minutes)...")
    
    # Test 3: All states
    logger.info("\nPHASE 3: Complete Nationwide Test...")
    all_results = test_all_states()
    
    logger.info("\n" + "="*70)
    logger.info("✅ VALIDATION COMPLETE")
    logger.info("="*70)
    logger.info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("\nCheck validation_results_*.json for detailed output")


if __name__ == '__main__':
    main()
