"""
VA Builders Summit Scraper
Extracts construction and cleaning contract opportunities from vabuilderssummit.com
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import re

class VABuildersSummitScraper:
    """Scraper for VA Builders Summit website"""
    
    def __init__(self):
        self.base_url = "https://www.vabuilderssummit.com/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_all_internal_links(self):
        """
        Get all internal links from the VA Builders Summit website
        
        Returns:
            list: List of valid internal URLs
        """
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a", href=True)
            
            # Convert relative URLs to absolute
            full_links = [urljoin(self.base_url, link["href"]) for link in links]
            
            # Filter for internal links only
            internal_links = [
                link for link in set(full_links) 
                if link.startswith(self.base_url)
            ]
            
            return sorted(internal_links)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching base URL: {e}")
            return []
    
    def verify_link(self, url, timeout=5):
        """
        Verify if a link is accessible
        
        Args:
            url (str): URL to verify
            timeout (int): Request timeout in seconds
            
        Returns:
            dict: Status information
        """
        try:
            response = self.session.head(url, allow_redirects=True, timeout=timeout)
            return {
                "url": url,
                "status": "success" if response.status_code == 200 else "warning",
                "status_code": response.status_code,
                "accessible": response.status_code == 200
            }
        except requests.exceptions.RequestException as e:
            return {
                "url": url,
                "status": "error",
                "error": str(e),
                "accessible": False
            }
    
    def verify_all_links(self, links):
        """
        Verify accessibility of multiple links
        
        Args:
            links (list): List of URLs to verify
            
        Returns:
            dict: Categorized results
        """
        results = {
            "accessible": [],
            "warnings": [],
            "errors": []
        }
        
        print(f"🔍 Verifying {len(links)} links...")
        
        for i, link in enumerate(links, 1):
            result = self.verify_link(link)
            
            if result["accessible"]:
                results["accessible"].append(result)
                print(f"✅ [{i}/{len(links)}] {link}")
            elif result.get("status_code"):
                results["warnings"].append(result)
                print(f"⚠️ [{i}/{len(links)}] {link} (Status: {result['status_code']})")
            else:
                results["errors"].append(result)
                print(f"❌ [{i}/{len(links)}] {link} (Error: {result.get('error', 'Unknown')})")
            
            # Be respectful - don't hammer the server
            time.sleep(0.5)
        
        return results
    
    def extract_event_data(self, url):
        """
        Extract event/opportunity data from a specific page
        
        Args:
            url (str): URL to scrape
            
        Returns:
            dict: Extracted opportunity data
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract title
            title_tag = soup.find("h1") or soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else "Untitled Event"
            
            # Extract description
            description_meta = soup.find("meta", {"name": "description"})
            description = description_meta["content"] if description_meta else ""
            
            # Try to find main content
            if not description:
                content_div = soup.find("div", {"class": re.compile(r"content|main|description", re.I)})
                if content_div:
                    description = content_div.get_text(strip=True)[:500]
            
            # Extract date information
            date_patterns = [
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
                r'\b\d{4}-\d{2}-\d{2}\b',       # YYYY-MM-DD
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
            ]
            
            date_found = None
            page_text = soup.get_text()
            for pattern in date_patterns:
                match = re.search(pattern, page_text, re.I)
                if match:
                    date_found = match.group()
                    break
            
            # Extract location
            location = "Virginia"  # Default
            location_keywords = ["location:", "where:", "venue:", "address:"]
            for keyword in location_keywords:
                location_tag = soup.find(text=re.compile(keyword, re.I))
                if location_tag:
                    location_text = location_tag.parent.get_text(strip=True)
                    location = location_text.split(":", 1)[-1].strip()
                    break
            
            return {
                "title": title,
                "description": description,
                "url": url,
                "date": date_found,
                "location": location,
                "source": "VA Builders Summit",
                "scraped_at": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error scraping {url}: {e}")
            return None
    
    def scrape_all_opportunities(self):
        """
        Scrape all opportunities from VA Builders Summit
        
        Returns:
            list: List of opportunity dictionaries
        """
        print("🚀 Starting VA Builders Summit scraper...")
        
        # Get all internal links
        links = self.get_all_internal_links()
        print(f"📋 Found {len(links)} internal links")
        
        # Verify links
        verified = self.verify_all_links(links)
        accessible_links = [r["url"] for r in verified["accessible"]]
        
        print(f"\n✅ {len(accessible_links)} accessible pages")
        print(f"⚠️ {len(verified['warnings'])} warnings")
        print(f"❌ {len(verified['errors'])} errors")
        
        # Extract data from accessible pages
        opportunities = []
        print(f"\n🔍 Extracting data from accessible pages...")
        
        for i, link in enumerate(accessible_links, 1):
            print(f"📄 [{i}/{len(accessible_links)}] Scraping {link}")
            data = self.extract_event_data(link)
            
            if data and data.get("title"):
                opportunities.append(data)
                print(f"   ✅ Extracted: {data['title'][:60]}...")
            
            time.sleep(1)  # Be respectful
        
        print(f"\n✅ Scraped {len(opportunities)} opportunities")
        return opportunities
    
    def save_to_database(self, opportunities, db_session):
        """
        Save scraped opportunities to database
        
        Args:
            opportunities (list): List of opportunity dicts
            db_session: SQLAlchemy database session
            
        Returns:
            int: Number of opportunities saved
        """
        from sqlalchemy import text
        
        saved_count = 0
        
        for opp in opportunities:
            try:
                # Check if already exists
                existing = db_session.execute(text('''
                    SELECT id FROM government_contracts 
                    WHERE url = :url
                '''), {"url": opp["url"]}).fetchone()
                
                if existing:
                    print(f"⏭️ Skipping duplicate: {opp['title'][:50]}")
                    continue
                
                # Insert new opportunity
                db_session.execute(text('''
                    INSERT INTO government_contracts 
                    (title, agency, location, url, description, posted_date, deadline, 
                     contract_type, naics_code, data_source)
                    VALUES 
                    (:title, :agency, :location, :url, :description, :posted_date, :deadline,
                     :contract_type, :naics_code, :data_source)
                '''), {
                    "title": opp["title"],
                    "agency": "VA Builders Summit",
                    "location": opp["location"],
                    "url": opp["url"],
                    "description": opp["description"],
                    "posted_date": opp.get("date", datetime.now().strftime("%Y-%m-%d")),
                    "deadline": None,  # Extract if available
                    "contract_type": "Construction/Cleaning",
                    "naics_code": "561720",  # Janitorial Services
                    "data_source": "VA Builders Summit Web Scraper"
                })
                
                saved_count += 1
                print(f"✅ Saved: {opp['title'][:50]}")
                
            except Exception as e:
                print(f"❌ Error saving {opp['title'][:50]}: {e}")
                continue
        
        db_session.commit()
        return saved_count


# CLI usage
if __name__ == "__main__":
    scraper = VABuildersSummitScraper()
    
    # Option 1: Just get and verify links
    print("=" * 60)
    print("VA BUILDERS SUMMIT LINK VERIFICATION")
    print("=" * 60)
    
    links = scraper.get_all_internal_links()
    results = scraper.verify_all_links(links)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Accessible: {len(results['accessible'])}")
    print(f"⚠️ Warnings: {len(results['warnings'])}")
    print(f"❌ Errors: {len(results['errors'])}")
    
    # Option 2: Full scrape (uncomment to use)
    # opportunities = scraper.scrape_all_opportunities()
    # print(f"\n📊 Total opportunities found: {len(opportunities)}")
    # 
    # for opp in opportunities[:5]:  # Show first 5
    #     print(f"\n📄 {opp['title']}")
    #     print(f"   🔗 {opp['url']}")
    #     print(f"   📍 {opp['location']}")
