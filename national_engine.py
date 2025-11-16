"""
National Procurement Engine
Unified scraper that runs all 7 sources and aggregates results
"""

import logging
import sys
from typing import List, Dict, Any, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg2
from psycopg2.extras import execute_values
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from national_scrapers import (
    SymphonyScraper,
    DemandStarScraper,
    BidExpressScraper,
    COMBUYSScraper,
    EMarylandScraper,
    NewHampshireScraper,
    RhodeIslandScraper
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('national_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NationalProcurementScraper:
    """
    Unified scraper that runs all 7 sources and manages results.
    """
    
    def __init__(self, db_url: str = None):
        """
        Initialize national scraper.
        
        Args:
            db_url: PostgreSQL connection URL (format: postgresql://user:pass@host:port/dbname)
        """
        self.db_url = db_url or os.getenv('DATABASE_URL')
        
        # Initialize all scrapers
        self.scrapers = {
            'symphony': SymphonyScraper(),
            'demandstar': DemandStarScraper(),
            'bidexpress': BidExpressScraper(),
            'commbuys': COMBUYSScraper(),
            'emaryland': EMarylandScraper(),
            'newhampshire': NewHampshireScraper(),
            'rhodeisland': RhodeIslandScraper()
        }
        
        self.results = {
            'total_opportunities': 0,
            'by_source': {},
            'by_state': {},
            'errors': []
        }
    
    def run_all(self, parallel: bool = True) -> List[Dict[str, Any]]:
        """
        Run all 7 scrapers and aggregate results.
        
        Args:
            parallel: Run scrapers in parallel (faster but more resource intensive)
            
        Returns:
            List of all contracts from all sources
        """
        logger.info("=" * 80)
        logger.info("Starting National Procurement Scraper")
        logger.info("=" * 80)
        
        all_contracts = []
        
        if parallel:
            all_contracts = self._run_parallel()
        else:
            all_contracts = self._run_sequential()
        
        # Deduplicate by solicitation number + state
        unique_contracts = self._deduplicate(all_contracts)
        
        # Normalize and validate
        validated_contracts = self._validate_contracts(unique_contracts)
        
        # Calculate statistics
        self._calculate_stats(validated_contracts)
        
        # Log summary
        self._log_summary()
        
        logger.info("=" * 80)
        logger.info(f"National scraper completed: {len(validated_contracts)} unique opportunities")
        logger.info("=" * 80)
        
        return validated_contracts
    
    def _run_parallel(self) -> List[Dict[str, Any]]:
        """
        Run all scrapers in parallel using ThreadPoolExecutor.
        
        Returns:
            Combined list of contracts
        """
        all_contracts = []
        
        with ThreadPoolExecutor(max_workers=7) as executor:
            # Submit all scraper tasks
            future_to_scraper = {
                executor.submit(self._run_scraper, name, scraper): name
                for name, scraper in self.scrapers.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_scraper):
                scraper_name = future_to_scraper[future]
                try:
                    contracts = future.result(timeout=300)  # 5 minute timeout per scraper
                    all_contracts.extend(contracts)
                    logger.info(f"✅ {scraper_name}: {len(contracts)} opportunities")
                except Exception as e:
                    logger.error(f"❌ {scraper_name} failed: {e}")
                    self.results['errors'].append({
                        'source': scraper_name,
                        'error': str(e)
                    })
        
        return all_contracts
    
    def _run_sequential(self) -> List[Dict[str, Any]]:
        """
        Run all scrapers sequentially (safer, slower).
        
        Returns:
            Combined list of contracts
        """
        all_contracts = []
        
        for name, scraper in self.scrapers.items():
            try:
                contracts = self._run_scraper(name, scraper)
                all_contracts.extend(contracts)
                logger.info(f"✅ {name}: {len(contracts)} opportunities")
            except Exception as e:
                logger.error(f"❌ {name} failed: {e}")
                self.results['errors'].append({
                    'source': name,
                    'error': str(e)
                })
        
        return all_contracts
    
    def _run_scraper(self, name: str, scraper) -> List[Dict[str, Any]]:
        """
        Run a single scraper with error handling.
        
        Args:
            name: Scraper name
            scraper: Scraper instance
            
        Returns:
            List of contracts
        """
        logger.info(f"Starting {name} scraper...")
        
        try:
            contracts = scraper.scrape()
            
            # Alert if scraper returns 0 results
            if len(contracts) == 0:
                logger.warning(f"⚠️  {name} returned 0 results - may need attention")
                self.results['errors'].append({
                    'source': name,
                    'error': 'Returned 0 results'
                })
            
            return contracts
            
        except Exception as e:
            logger.error(f"Error in {name} scraper: {e}")
            raise
    
    def _deduplicate(self, contracts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate contracts by solicitation number + state.
        
        Args:
            contracts: List of contracts
            
        Returns:
            Deduplicated list
        """
        seen: Set[str] = set()
        unique = []
        
        for contract in contracts:
            key = f"{contract['state']}:{contract['solicitation_number']}"
            if key not in seen:
                seen.add(key)
                unique.append(contract)
        
        duplicates_removed = len(contracts) - len(unique)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate contracts")
        
        return unique
    
    def _validate_contracts(self, contracts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and normalize contract data.
        
        Args:
            contracts: List of contracts
            
        Returns:
            Validated contracts
        """
        validated = []
        
        for contract in contracts:
            # Ensure required fields exist
            if not contract.get('title') or contract['title'] == 'No Title':
                continue
            
            if not contract.get('state'):
                contract['state'] = 'US'
            
            # Normalize state to uppercase
            contract['state'] = contract['state'].upper()
            
            # Ensure link is present
            if not contract.get('link'):
                logger.warning(f"Contract missing link: {contract.get('solicitation_number')}")
            
            validated.append(contract)
        
        return validated
    
    def _calculate_stats(self, contracts: List[Dict[str, Any]]) -> None:
        """
        Calculate statistics about scraped data.
        
        Args:
            contracts: List of contracts
        """
        self.results['total_opportunities'] = len(contracts)
        
        # Count by source
        for contract in contracts:
            source = contract.get('source', 'unknown')
            self.results['by_source'][source] = self.results['by_source'].get(source, 0) + 1
        
        # Count by state
        for contract in contracts:
            state = contract.get('state', 'US')
            self.results['by_state'][state] = self.results['by_state'].get(state, 0) + 1
    
    def _log_summary(self) -> None:
        """
        Log summary of scraping results.
        """
        logger.info("\n" + "=" * 80)
        logger.info("SCRAPING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Opportunities: {self.results['total_opportunities']}")
        
        logger.info("\nBy Source:")
        for source, count in sorted(self.results['by_source'].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {source:20s}: {count:4d} opportunities")
        
        logger.info(f"\nBy State (top 10):")
        top_states = sorted(self.results['by_state'].items(), key=lambda x: x[1], reverse=True)[:10]
        for state, count in top_states:
            logger.info(f"  {state:3s}: {count:4d} opportunities")
        
        if self.results['errors']:
            logger.info(f"\nErrors: {len(self.results['errors'])}")
            for error in self.results['errors']:
                logger.error(f"  {error['source']}: {error['error']}")
        
        logger.info("=" * 80 + "\n")
    
    def save_to_postgresql(self, contracts: List[Dict[str, Any]]) -> int:
        """
        Save contracts to PostgreSQL database.
        
        Args:
            contracts: List of contracts to save
            
        Returns:
            Number of contracts saved
        """
        if not self.db_url:
            logger.error("No database URL provided, cannot save to PostgreSQL")
            return 0
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS national_contracts (
                    id SERIAL PRIMARY KEY,
                    state VARCHAR(2) NOT NULL,
                    title TEXT NOT NULL,
                    solicitation_number VARCHAR(255),
                    due_date VARCHAR(50),
                    link TEXT,
                    agency TEXT,
                    source VARCHAR(50) NOT NULL,
                    scraped_at TIMESTAMP DEFAULT NOW(),
                    description TEXT,
                    organization_type VARCHAR(100),
                    UNIQUE(state, solicitation_number)
                )
            """)
            conn.commit()
            
            # Prepare data for insertion
            values = [
                (
                    contract['state'],
                    contract['title'],
                    contract.get('solicitation_number', 'N/A'),
                    contract.get('due_date', ''),
                    contract.get('link', ''),
                    contract.get('agency', 'N/A'),
                    contract['source'],
                    contract.get('description', ''),
                    contract.get('organization_type', '')
                )
                for contract in contracts
            ]
            
            # Insert with ON CONFLICT UPDATE
            execute_values(
                cursor,
                """
                INSERT INTO national_contracts 
                (state, title, solicitation_number, due_date, link, agency, source, description, organization_type)
                VALUES %s
                ON CONFLICT (state, solicitation_number) 
                DO UPDATE SET
                    title = EXCLUDED.title,
                    due_date = EXCLUDED.due_date,
                    link = EXCLUDED.link,
                    agency = EXCLUDED.agency,
                    scraped_at = NOW()
                """,
                values
            )
            
            conn.commit()
            saved = len(values)
            logger.info(f"✅ Saved {saved} contracts to PostgreSQL")
            
            cursor.close()
            conn.close()
            
            return saved
            
        except Exception as e:
            logger.error(f"Error saving to PostgreSQL: {e}")
            return 0
    
    def print_sample_results(self, contracts: List[Dict[str, Any]], limit: int = 20) -> None:
        """
        Print first N results for inspection.
        
        Args:
            contracts: List of contracts
            limit: Number to print
        """
        logger.info("\n" + "=" * 80)
        logger.info(f"SAMPLE RESULTS (first {limit} opportunities)")
        logger.info("=" * 80)
        
        for i, contract in enumerate(contracts[:limit], 1):
            logger.info(f"\n#{i}")
            logger.info(f"  State: {contract['state']}")
            logger.info(f"  Title: {contract['title'][:80]}")
            logger.info(f"  Solicitation #: {contract['solicitation_number']}")
            logger.info(f"  Due Date: {contract.get('due_date', 'N/A')}")
            logger.info(f"  Agency: {contract.get('agency', 'N/A')}")
            logger.info(f"  Source: {contract['source']}")
            logger.info(f"  Link: {contract.get('link', 'N/A')[:80]}")
        
        logger.info("\n" + "=" * 80 + "\n")


def main():
    """
    Main entry point for national scraper.
    """
    # Get database URL from environment or use default
    db_url = os.getenv('DATABASE_URL')
    
    # Initialize scraper
    scraper = NationalProcurementScraper(db_url=db_url)
    
    # Run all scrapers
    contracts = scraper.run_all(parallel=True)
    
    # Print sample results
    scraper.print_sample_results(contracts, limit=20)
    
    # Save to database if configured
    if db_url:
        scraper.save_to_postgresql(contracts)
    else:
        logger.warning("No DATABASE_URL found, skipping PostgreSQL save")
        logger.info("Set DATABASE_URL environment variable to enable database storage")
    
    return contracts


if __name__ == '__main__':
    main()
