"""
Automated Procurement Scraper Scheduler
Runs scrapers on a schedule to keep procurement opportunities up-to-date
"""
import schedule
import time
import logging
from datetime import datetime
from sam_gov_fetcher import SAMgovFetcher
from local_gov_scraper import VirginiaLocalGovScraper
from sqlalchemy import create_engine, text
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProcurementScraperScheduler:
    """Automated scheduler for procurement opportunity scrapers"""
    
    def __init__(self):
        # Use the same database as the Flask app
        database_url = os.environ.get('DATABASE_URL', 'sqlite:///contracts.db')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        self.engine = create_engine(database_url)
        self.sam_fetcher = SAMgovFetcher()
        self.local_scraper = VirginiaLocalGovScraper()
    
    def scrape_federal_contracts(self):
        """Scrape federal contracts from SAM.gov"""
        logger.info("🔄 Starting federal contract scraping...")
        try:
            contracts = self.sam_fetcher.fetch_va_cleaning_contracts(days_back=30)
            
            if not contracts:
                logger.warning("⚠️ No federal contracts found")
                return
            
            # Insert into federal_contracts table
            with self.engine.connect() as conn:
                inserted = 0
                for contract in contracts:
                    try:
                        # Check if contract already exists
                        existing = conn.execute(text('''
                            SELECT id FROM federal_contracts 
                            WHERE notice_id = :notice_id
                        '''), {'notice_id': contract.get('notice_id', '')}).fetchone()
                        
                        if not existing:
                            conn.execute(text('''
                                INSERT INTO federal_contracts 
                                (title, agency, location, description, value, deadline, 
                                 naics_code, posted_date, notice_id, sam_gov_url)
                                VALUES 
                                (:title, :agency, :location, :description, :value, :deadline,
                                 :naics_code, :posted_date, :notice_id, :sam_gov_url)
                            '''), {
                                'title': contract['title'],
                                'agency': contract['agency'],
                                'location': contract['location'],
                                'description': contract['description'],
                                'value': contract['value'],
                                'deadline': contract['deadline'],
                                'naics_code': contract['naics_code'],
                                'posted_date': contract.get('posted_date', datetime.now().strftime('%Y-%m-%d')),
                                'notice_id': contract.get('notice_id', ''),
                                'sam_gov_url': contract.get('sam_gov_url', '')
                            })
                            inserted += 1
                        
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Error inserting federal contract: {e}")
                        conn.rollback()
                        continue
                
                logger.info(f"✅ Federal scraping complete: {inserted} new contracts added")
        
        except Exception as e:
            logger.error(f"❌ Federal scraping failed: {e}")
    
    def scrape_local_contracts(self):
        """Scrape local government contracts from Virginia cities"""
        logger.info("🔄 Starting local government contract scraping...")
        try:
            contracts = self.local_scraper.fetch_all_local_contracts()
            
            if not contracts:
                logger.warning("⚠️ No local contracts found")
                return
            
            # Insert into contracts table
            with self.engine.connect() as conn:
                inserted = 0
                for contract in contracts:
                    try:
                        # Check if similar contract already exists (by title and agency)
                        existing = conn.execute(text('''
                            SELECT id FROM contracts 
                            WHERE title = :title AND agency = :agency
                        '''), {
                            'title': contract['title'],
                            'agency': contract['agency']
                        }).fetchone()
                        
                        if not existing:
                            conn.execute(text('''
                                INSERT INTO contracts 
                                (title, agency, location, description, value, deadline, 
                                 naics_code, created_at, website_url, category)
                                VALUES 
                                (:title, :agency, :location, :description, :value, :deadline,
                                 :naics_code, CURRENT_TIMESTAMP, :website_url, :category)
                            '''), {
                                'title': contract['title'],
                                'agency': contract['agency'],
                                'location': contract['location'],
                                'description': contract['description'],
                                'value': contract.get('value', 'Contact for quote'),
                                'deadline': contract.get('deadline', '2026-12-31'),
                                'naics_code': contract.get('naics_code', '561720'),
                                'website_url': contract.get('website_url', ''),
                                'category': contract.get('category', 'Municipal Government')
                            })
                            inserted += 1
                        
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Error inserting local contract: {e}")
                        conn.rollback()
                        continue
                
                logger.info(f"✅ Local scraping complete: {inserted} new contracts added")
        
        except Exception as e:
            logger.error(f"❌ Local scraping failed: {e}")
    
    def run_all_scrapers(self):
        """Run all scrapers sequentially"""
        logger.info("=" * 60)
        logger.info("🚀 Starting scheduled procurement scraping")
        logger.info("=" * 60)
        
        self.scrape_federal_contracts()
        time.sleep(5)  # Small delay between scrapers
        self.scrape_local_contracts()
        
        logger.info("=" * 60)
        logger.info("✅ All scrapers completed")
        logger.info("=" * 60)
    
    def start_scheduler(self):
        """Start the scheduler with defined intervals"""
        logger.info("⏰ Starting procurement scraper scheduler...")
        
        # Run immediately on startup
        self.run_all_scrapers()
        
        # Schedule daily runs
        schedule.every().day.at("02:00").do(self.scrape_federal_contracts)
        schedule.every().day.at("03:00").do(self.scrape_local_contracts)
        
        # Also run every 6 hours for more frequent updates
        schedule.every(6).hours.do(self.run_all_scrapers)
        
        logger.info("✅ Scheduler started:")
        logger.info("   - Federal contracts: Daily at 2:00 AM")
        logger.info("   - Local contracts: Daily at 3:00 AM")
        logger.info("   - Full scrape: Every 6 hours")
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


if __name__ == '__main__':
    scheduler = ProcurementScraperScheduler()
    scheduler.start_scheduler()
