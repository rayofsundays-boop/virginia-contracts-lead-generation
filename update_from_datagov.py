"""
Update federal contracts database from Data.gov bulk files
Run this script to fetch and populate contracts from USAspending.gov and other Data.gov sources
"""
import os
import sys
import sqlite3
from dotenv import load_dotenv
from datagov_bulk_fetcher import DataGovBulkFetcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_database_connection():
    """Get database connection (SQLite for local, PostgreSQL for production)"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith('postgres'):
        # Production PostgreSQL
        import psycopg2
        conn = psycopg2.connect(database_url)
        return conn, 'postgresql'
    else:
        # Local SQLite
        db_path = os.path.join(os.path.dirname(__file__), 'leads.db')
        conn = sqlite3.connect(db_path)
        return conn, 'sqlite'

def insert_contracts(contracts):
    """Insert contracts into database"""
    if not contracts:
        logger.warning("⚠️  No contracts to insert")
        return 0
    
    try:
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        inserted = 0
        skipped = 0
        
        for contract in contracts:
            try:
                # Use parameterized query (safe from SQL injection)
                if db_type == 'postgresql':
                    query = """
                        INSERT INTO federal_contracts 
                        (title, agency, department, location, value, deadline, description, 
                         naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (notice_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            agency = EXCLUDED.agency,
                            location = EXCLUDED.location,
                            value = EXCLUDED.value,
                            deadline = EXCLUDED.deadline
                    """
                else:  # SQLite
                    query = """
                        INSERT OR REPLACE INTO federal_contracts 
                        (title, agency, department, location, value, deadline, description, 
                         naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                
                cursor.execute(query, (
                    contract['title'],
                    contract['agency'],
                    contract.get('department', ''),
                    contract['location'],
                    contract['value'],
                    contract.get('deadline', ''),
                    contract['description'],
                    contract.get('naics_code', ''),
                    contract.get('sam_gov_url', ''),
                    contract['notice_id'],
                    contract.get('set_aside', ''),
                    contract.get('posted_date', '')
                ))
                
                inserted += 1
                
            except Exception as e:
                logger.warning(f"⚠️  Skipped contract {contract.get('notice_id', 'unknown')}: {e}")
                skipped += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Inserted {inserted} contracts, skipped {skipped}")
        return inserted
        
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return 0

def main():
    """Main function to fetch and update contracts"""
    logger.info("🚀 Starting Data.gov bulk data update...")
    
    # Initialize fetcher
    fetcher = DataGovBulkFetcher()
    
    # Fetch from USAspending.gov (last 30 days)
    logger.info("\n📦 Fetching from USAspending.gov bulk download...")
    usaspending_contracts = fetcher.fetch_usaspending_contracts(days_back=90)
    
    # Insert into database
    if usaspending_contracts:
        logger.info(f"\n💾 Inserting {len(usaspending_contracts)} contracts into database...")
        inserted = insert_contracts(usaspending_contracts)
        logger.info(f"✅ Successfully updated {inserted} federal contracts from Data.gov bulk files")
    else:
        logger.warning("⚠️  No contracts fetched from USAspending.gov")
        
        # Try searching Data.gov catalog as fallback
        logger.info("\n🔍 Searching Data.gov catalog for alternative datasets...")
        datasets = fetcher.search_datagov_datasets("federal contracts virginia cleaning janitorial")
        
        if datasets:
            logger.info(f"\n📚 Found {len(datasets)} relevant datasets:")
            for i, ds in enumerate(datasets[:5], 1):
                print(f"{i}. {ds['title']}")
                print(f"   URL: {ds['url']}")
                if ds.get('resources'):
                    print(f"   Resources: {len(ds['resources'])} files available")
                print()
    
    logger.info("\n✅ Data.gov bulk update complete!")

if __name__ == '__main__':
    main()
