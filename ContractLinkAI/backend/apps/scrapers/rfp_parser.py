"""
RFP parser utilities for extracting structured data from RFP pages.
"""
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger('scrapers')


class RFPParser:
    """
    Utility class for parsing RFP details from web pages.
    """
    
    @staticmethod
    def extract_contact_info(soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract contact information from RFP page.
        
        Returns:
            Dictionary with contact_name, contact_email, contact_phone
        """
        contact_info = {
            'contact_name': '',
            'contact_email': '',
            'contact_phone': '',
        }
        
        # Try to find email
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        emails = re.findall(email_pattern, soup.get_text())
        if emails:
            contact_info['contact_email'] = emails[0]
        
        # Try to find phone
        phone_pattern = r'(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, soup.get_text())
        if phones:
            # Join the phone number parts
            contact_info['contact_phone'] = ''.join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
        
        # Try to find contact name
        # Look for common patterns like "Contact: John Doe" or "Procurement Officer: Jane Smith"
        name_patterns = [
            r'Contact[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Officer[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Representative[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        
        text = soup.get_text()
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                contact_info['contact_name'] = match.group(1)
                break
        
        return contact_info
    
    @staticmethod
    def extract_attachments(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract attachment links from RFP page.
        
        Returns:
            List of dictionaries with 'name' and 'url'
        """
        attachments = []
        
        # Find links to PDF, DOC, DOCX, XLS, XLSX files
        attachment_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip']
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            if any(href.lower().endswith(ext) for ext in attachment_extensions):
                from urllib.parse import urljoin
                absolute_url = urljoin(base_url, href)
                
                attachments.append({
                    'name': text or href.split('/')[-1],
                    'url': absolute_url
                })
        
        return attachments
    
    @staticmethod
    def extract_keywords(title: str, description: str) -> List[str]:
        """
        Extract relevant keywords from title and description.
        
        Returns:
            List of keywords
        """
        # Common keywords for cleaning/janitorial services
        relevant_keywords = [
            'janitorial', 'custodial', 'cleaning', 'maintenance',
            'sanitation', 'housekeeping', 'porter', 'floor care',
            'carpet cleaning', 'window cleaning', 'waste removal',
            'restroom', 'sanitization', 'disinfection'
        ]
        
        text = (title + ' ' + description).lower()
        found_keywords = []
        
        for keyword in relevant_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return list(set(found_keywords))
    
    @staticmethod
    def extract_naics_codes(soup: BeautifulSoup) -> List[str]:
        """
        Extract NAICS codes from RFP page.
        
        Returns:
            List of NAICS code strings
        """
        naics_codes = []
        
        # Pattern for NAICS codes (6 digits)
        naics_pattern = r'\b\d{6}\b'
        
        text = soup.get_text()
        matches = re.findall(naics_pattern, text)
        
        # Common NAICS codes for cleaning services
        cleaning_naics = ['561720', '561730', '561790']
        
        for match in matches:
            if match in cleaning_naics or 'naics' in text.lower():
                naics_codes.append(match)
        
        return list(set(naics_codes))
    
    @staticmethod
    def extract_estimated_value(soup: BeautifulSoup) -> Optional[float]:
        """
        Extract estimated contract value from RFP page.
        
        Returns:
            Estimated value as float or None
        """
        # Pattern for currency amounts
        currency_pattern = r'\$[\d,]+(?:\.\d{2})?'
        
        text = soup.get_text()
        
        # Look for value in context
        value_contexts = [
            r'estimated value[:\s]*(\$[\d,]+(?:\.\d{2})?)',
            r'contract value[:\s]*(\$[\d,]+(?:\.\d{2})?)',
            r'total cost[:\s]*(\$[\d,]+(?:\.\d{2})?)',
            r'budget[:\s]*(\$[\d,]+(?:\.\d{2})?)',
        ]
        
        for pattern in value_contexts:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace('$', '').replace(',', '')
                try:
                    return float(value_str)
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def extract_requirements(soup: BeautifulSoup) -> str:
        """
        Extract requirements section from RFP page.
        
        Returns:
            Requirements text
        """
        # Look for sections with common headings
        requirement_headings = [
            'requirements', 'specifications', 'scope of work',
            'statement of work', 'qualifications', 'eligibility'
        ]
        
        requirements_text = []
        
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text(strip=True).lower()
            
            if any(req_heading in heading_text for req_heading in requirement_headings):
                # Get the next sibling elements until the next heading
                current = heading.find_next_sibling()
                section_text = []
                
                while current and current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    text = current.get_text(strip=True)
                    if text:
                        section_text.append(text)
                    current = current.find_next_sibling()
                
                if section_text:
                    requirements_text.extend(section_text)
        
        return ' '.join(requirements_text) if requirements_text else ""
    
    @staticmethod
    def extract_contract_duration(soup: BeautifulSoup) -> str:
        """
        Extract contract duration from RFP page.
        
        Returns:
            Duration string
        """
        text = soup.get_text()
        
        # Patterns for duration
        duration_patterns = [
            r'contract period[:\s]*([^\.]+)',
            r'term[:\s]*(\d+\s+(?:year|month|day)s?)',
            r'duration[:\s]*(\d+\s+(?:year|month|day)s?)',
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
