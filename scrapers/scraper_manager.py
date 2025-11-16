"""
Scraper Manager and Scheduler
Coordinates all scrapers and provides admin interface
"""

import sqlite3
from datetime import datetime
import logging
from typing import List, Dict, Optional
import threading
import time

from scrapers.base_scraper import logger
from scrapers.eva_virginia_scraper import EVAVirginiaScraper
from scrapers.state_portal_scraper import StatePortalScraper
from scrapers.city_county_scraper import CityCountyScraper


class ScraperManager:
    """
    Manages all scrapers and provides scheduling capabilities
    """
    
    def __init__(self, db_path: str = 'leads.db'):
        """
        Initialize scraper manager
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.scrapers = {
            'eva_virginia': EVAVirginiaScraper(),
            'state_portals': StatePortalScraper(),
            'city_county': CityCountyScraper()
        }
        
        self.scraper_status = {}
        self.is_running = False
        self._ensure_scraper_log_table()
    
    def _ensure_scraper_log_table(self):
        """Create scraper log table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraper_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scraper_name TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    status TEXT DEFAULT 'running',
                    contracts_found INTEGER DEFAULT 0,
                    contracts_saved INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating scraper_logs table: {e}")
    
    def run_scraper(self, scraper_name: str, save_to_db: bool = True) -> Dict:
        """
        Run a specific scraper
        
        Args:
            scraper_name: Name of scraper to run
            save_to_db: Whether to save results to database
            
        Returns:
            Dictionary with scraper results
        """
        if scraper_name not in self.scrapers:
            return {
                'success': False,
                'error': f'Unknown scraper: {scraper_name}'
            }
        
        scraper = self.scrapers[scraper_name]
        
        # Log start
        log_id = self._log_scraper_start(scraper_name)
        
        try:
            logger.info(f"Starting scraper: {scraper_name}")
            start_time = datetime.now()
            
            # Run the scraper
            contracts = scraper.scrape()
            
            contracts_saved = 0
            
            if save_to_db and contracts:
                # Save to database
                conn = sqlite3.connect(self.db_path)
                contracts_saved = scraper.save_contracts(contracts, conn)
                conn.close()
            
            # Log completion
            duration = (datetime.now() - start_time).total_seconds()
            
            self._log_scraper_complete(
                log_id,
                status='success',
                contracts_found=len(contracts),
                contracts_saved=contracts_saved
            )
            
            result = {
                'success': True,
                'scraper': scraper_name,
                'contracts_found': len(contracts),
                'contracts_saved': contracts_saved,
                'duration_seconds': duration,
                'started_at': start_time.isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ {scraper_name} complete: {contracts_saved}/{len(contracts)} contracts saved")
            return result
        
        except Exception as e:
            logger.error(f"❌ {scraper_name} failed: {e}")
            
            self._log_scraper_complete(
                log_id,
                status='error',
                error_message=str(e)
            )
            
            return {
                'success': False,
                'scraper': scraper_name,
                'error': str(e)
            }
    
    def run_all_scrapers(self, save_to_db: bool = True) -> Dict:
        """
        Run all scrapers sequentially
        
        Args:
            save_to_db: Whether to save results to database
            
        Returns:
            Dictionary with aggregated results
        """
        logger.info("Running all scrapers...")
        
        results = {
            'started_at': datetime.now().isoformat(),
            'scrapers': {},
            'total_contracts_found': 0,
            'total_contracts_saved': 0
        }
        
        for scraper_name in self.scrapers.keys():
            result = self.run_scraper(scraper_name, save_to_db)
            results['scrapers'][scraper_name] = result
            
            if result.get('success'):
                results['total_contracts_found'] += result.get('contracts_found', 0)
                results['total_contracts_saved'] += result.get('contracts_saved', 0)
        
        results['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"✅ All scrapers complete: {results['total_contracts_saved']} total contracts saved")
        return results
    
    def get_scraper_logs(self, limit: int = 50) -> List[Dict]:
        """
        Get recent scraper execution logs
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of log dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT *
                FROM scraper_logs
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,))
            
            logs = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return logs
        
        except Exception as e:
            logger.error(f"Error fetching scraper logs: {e}")
            return []
    
    def get_scraper_stats(self) -> Dict:
        """
        Get statistics for all scrapers
        
        Returns:
            Dictionary with scraper statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get stats for each scraper
            cursor.execute("""
                SELECT 
                    scraper_name,
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed_runs,
                    SUM(contracts_saved) as total_contracts_saved,
                    MAX(started_at) as last_run_at
                FROM scraper_logs
                GROUP BY scraper_name
            """)
            
            stats = {}
            for row in cursor.fetchall():
                stats[row['scraper_name']] = dict(row)
            
            conn.close()
            return stats
        
        except Exception as e:
            logger.error(f"Error fetching scraper stats: {e}")
            return {}
    
    def _log_scraper_start(self, scraper_name: str) -> int:
        """Log scraper start and return log ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scraper_logs (scraper_name, started_at, status)
                VALUES (?, ?, 'running')
            """, (scraper_name, datetime.now()))
            
            log_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return log_id
        
        except Exception as e:
            logger.error(f"Error logging scraper start: {e}")
            return 0
    
    def _log_scraper_complete(self, log_id: int, status: str, 
                            contracts_found: int = 0,
                            contracts_saved: int = 0,
                            error_message: str = None):
        """Log scraper completion"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE scraper_logs
                SET completed_at = ?,
                    status = ?,
                    contracts_found = ?,
                    contracts_saved = ?,
                    error_message = ?
                WHERE id = ?
            """, (
                datetime.now(),
                status,
                contracts_found,
                contracts_saved,
                error_message,
                log_id
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error logging scraper complete: {e}")
    
    def schedule_daily_scrape(self, hour: int = 2, minute: int = 0):
        """
        Schedule daily scraper runs
        
        Args:
            hour: Hour to run (0-23, default 2 AM)
            minute: Minute to run (0-59, default 0)
        """
        def run_scheduled():
            while self.is_running:
                now = datetime.now()
                
                # Check if it's time to run
                if now.hour == hour and now.minute == minute:
                    logger.info("⏰ Scheduled scraper run starting...")
                    self.run_all_scrapers(save_to_db=True)
                    
                    # Sleep for 60 seconds to avoid running multiple times in same minute
                    time.sleep(60)
                else:
                    # Check every 30 seconds
                    time.sleep(30)
        
        self.is_running = True
        thread = threading.Thread(target=run_scheduled, daemon=True)
        thread.start()
        
        logger.info(f"✅ Scheduled daily scraper run at {hour:02d}:{minute:02d}")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("Scheduler stopped")


# Global scraper manager instance
_manager = None


def get_scraper_manager(db_path: str = 'leads.db') -> ScraperManager:
    """Get or create scraper manager instance"""
    global _manager
    
    if _manager is None:
        _manager = ScraperManager(db_path)
    
    return _manager
