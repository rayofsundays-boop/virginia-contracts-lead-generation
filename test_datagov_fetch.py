"""
Test script to fetch federal contracts directly from Data.gov/USAspending.gov
"""
import sys
import logging
from datagov_bulk_fetcher import DataGovBulkFetcher
import sqlite3
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_to_database(contracts):
    """Save fetched contracts to database"""
    if not contracts:
        logger.warning("No contracts to save")
        return 0
    
    try:
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        saved_count = 0
        skipped_count = 0
        
        for contract in contracts:
            try:
                # Check if contract already exists (by title + agency)
                cursor.execute("""
                    SELECT id FROM federal_contracts 
                    WHERE title = ? AND agency = ?
                """, (contract['title'], contract['agency']))
                
                if cursor.fetchone():
                    skipped_count += 1
                    continue
                
                # Insert new contract
                cursor.execute("""
                    INSERT INTO federal_contracts 
                    (title, agency, location, value, deadline, sam_gov_url, naics_code, notice_id, data_source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract['title'],
                    contract['agency'],
                    contract['location'],
                    contract['value'],
                    contract['deadline'],
                    contract['sam_gov_url'],
                    contract.get('naics_code', '561720'),
                    contract.get('notice_id', f"DATAGOV-{datetime.now().strftime('%Y%m%d')}-{saved_count}"),
                    'Data.gov/USAspending',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error saving contract: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Saved {saved_count} new contracts, skipped {skipped_count} duplicates")
        return saved_count
        
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return 0

def main():
    logger.info("=" * 80)
    logger.info("🚀 FETCHING FEDERAL CONTRACTS FROM DATA.GOV / USASPENDING.GOV")
    logger.info("=" * 80)
    
    # Initialize fetcher
    fetcher = DataGovBulkFetcher()
    
    # Fetch contracts (90 days for bulk data)
    logger.info("\n📦 Fetching contracts from last 90 days...")
    contracts = fetcher.fetch_usaspending_contracts(days_back=90)
    
    logger.info("\n" + "=" * 80)
    logger.info(f"📊 RESULTS: Found {len(contracts)} contracts")
    logger.info("=" * 80)
    
    if contracts:
        # Show sample contracts
        logger.info("\n📋 Sample Contracts (first 5):\n")
        for i, contract in enumerate(contracts[:5], 1):
            logger.info(f"{i}. {contract['title']}")
            logger.info(f"   Agency: {contract['agency']}")
            logger.info(f"   Location: {contract['location']}")
            logger.info(f"   Value: {contract['value']}")
            logger.info(f"   NAICS: {contract.get('naics_code', 'N/A')}")
            logger.info(f"   URL: {contract['sam_gov_url'][:80]}...")
            logger.info("")
        
        # Ask to save to database
        logger.info("\n💾 Saving to database...")
        saved = save_to_database(contracts)
        
        if saved > 0:
            logger.info(f"\n✅ SUCCESS! Added {saved} new federal contracts to database")
            logger.info("   View them at: http://localhost:5000/federal-contracts")
        else:
            logger.info("\n⚠️  No new contracts added (all were duplicates)")
    else:
        logger.info("\n⚠️  No contracts found. This could mean:")
        logger.info("   • USAspending.gov API might be down")
        logger.info("   • No contracts matching criteria in last 90 days")
        logger.info("   • Network connectivity issues")
    
    logger.info("\n" + "=" * 80)

if __name__ == '__main__':
    main()
