"""
Automated Daily Federal Contract Fetcher
Runs daily to fetch new contracts from Data.gov/USAspending.gov
"""
import sys
import os
import logging
from datetime import datetime, timedelta
import sqlite3
from datagov_bulk_fetcher import DataGovBulkFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_fetch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutoFetcher:
    """Automated contract fetching system"""
    
    def __init__(self):
        self.db_path = 'leads.db'
        self.fetcher = DataGovBulkFetcher()
        
    def fetch_and_save(self, days_back=7):
        """
        Fetch new contracts and save to database
        
        Args:
            days_back: How many days back to search (default 7 for daily runs)
        """
        logger.info("=" * 80)
        logger.info(f"🤖 AUTOMATED DAILY FETCH - {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        logger.info("=" * 80)
        
        try:
            # Fetch contracts from Data.gov
            logger.info(f"📦 Fetching contracts from last {days_back} days...")
            contracts = self.fetcher.fetch_usaspending_contracts(days_back=days_back)
            
            if not contracts:
                logger.warning("⚠️  No contracts found in this fetch")
                return 0
            
            logger.info(f"✅ Retrieved {len(contracts)} contracts from Data.gov")
            
            # Save to database
            saved_count = self._save_to_database(contracts)
            
            # Log summary
            logger.info("=" * 80)
            logger.info(f"📊 DAILY FETCH SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Contracts fetched:     {len(contracts)}")
            logger.info(f"New contracts added:   {saved_count}")
            logger.info(f"Duplicates skipped:    {len(contracts) - saved_count}")
            logger.info(f"Success rate:          {(saved_count/len(contracts)*100):.1f}%")
            logger.info("=" * 80)
            
            # Get total counts
            self._log_database_stats()
            
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Error during automated fetch: {e}", exc_info=True)
            return 0
    
    def _save_to_database(self, contracts):
        """Save contracts to database, avoiding duplicates"""
        if not contracts:
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            skipped_count = 0
            
            for contract in contracts:
                try:
                    # Check for duplicates (by notice_id or title+agency)
                    cursor.execute("""
                        SELECT id FROM federal_contracts 
                        WHERE notice_id = ? OR (title = ? AND agency = ?)
                    """, (
                        contract.get('notice_id', ''),
                        contract['title'],
                        contract['agency']
                    ))
                    
                    if cursor.fetchone():
                        skipped_count += 1
                        continue
                    
                    # Insert new contract
                    cursor.execute("""
                        INSERT INTO federal_contracts 
                        (title, agency, department, location, value, deadline, description,
                         sam_gov_url, naics_code, notice_id, set_aside, posted_date, 
                         data_source, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        contract['title'],
                        contract['agency'],
                        contract.get('department', ''),
                        contract['location'],
                        contract['value'],
                        contract['deadline'],
                        contract.get('description', ''),
                        contract['sam_gov_url'],
                        contract.get('naics_code', '561720'),
                        contract.get('notice_id', f"AUTO-{datetime.now().strftime('%Y%m%d')}-{saved_count}"),
                        contract.get('set_aside', 'Unrestricted'),
                        contract.get('posted_date', datetime.now().strftime('%Y-%m-%d')),
                        'Data.gov/USAspending (Auto)',
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving contract '{contract.get('title', 'Unknown')}': {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Saved {saved_count} new contracts, skipped {skipped_count} duplicates")
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Database error: {e}", exc_info=True)
            return 0
    
    def _log_database_stats(self):
        """Log current database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM federal_contracts")
            federal = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM federal_contracts WHERE data_source LIKE '%Data.gov%'")
            datagov = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contracts")
            local = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM supply_contracts")
            supply = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM commercial_opportunities")
            commercial = cursor.fetchone()[0]
            
            total = federal + local + supply + commercial
            
            logger.info("\n📊 CURRENT DATABASE TOTALS")
            logger.info("-" * 80)
            logger.info(f"Federal Contracts:          {federal:>4} ({datagov} from Data.gov)")
            logger.info(f"Local Government:           {local:>4}")
            logger.info(f"Supply Contracts:           {supply:>4}")
            logger.info(f"Commercial Opportunities:   {commercial:>4}")
            logger.info(f"{'='*40}")
            logger.info(f"TOTAL OPPORTUNITIES:        {total:>4}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")


def main():
    """Main execution function"""
    logger.info("\n🚀 Starting automated daily fetch...")
    
    # Initialize fetcher
    fetcher = AutoFetcher()
    
    # Fetch contracts from last 7 days (configurable)
    days_back = int(os.environ.get('FETCH_DAYS_BACK', 7))
    
    # Run the fetch
    saved = fetcher.fetch_and_save(days_back=days_back)
    
    if saved > 0:
        logger.info(f"\n✅ SUCCESS! Added {saved} new federal contracts")
    else:
        logger.info("\n✅ Fetch completed (no new contracts)")
    
    logger.info("\n" + "=" * 80)
    logger.info("Next scheduled run: Tomorrow at 3:00 AM EST")
    logger.info("=" * 80 + "\n")
    
    return saved


if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
