import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datagov_bulk_fetcher import DataGovBulkFetcher


class TestDataGovFetch(unittest.TestCase):
    def setUp(self):
        self.fetcher = DataGovBulkFetcher()
    
    def test_naics_codes_include_561720(self):
        """Verify 561720 (Janitorial Services) is in NAICS codes"""
        self.assertIn('561720', self.fetcher.naics_codes)
        self.assertEqual(self.fetcher.naics_codes[0], '561720', "561720 should be first for priority")
    
    def test_cleaning_keywords_defined(self):
        """Verify strict cleaning keywords are configured"""
        self.assertTrue(hasattr(self.fetcher, 'cleaning_keywords'))
        self.assertIn('janitor', self.fetcher.cleaning_keywords)
        self.assertIn('cleaning', self.fetcher.cleaning_keywords)
    
    def test_parse_usaspending_award_with_naics_561720(self):
        """Test parsing award with NAICS 561720 (highest priority)"""
        mock_award = {
            'Description': 'Janitorial Services for Federal Building',
            'Awarding Agency': 'General Services Administration',
            'Awarding Sub Agency': 'Public Buildings Service',
            'Place of Performance City': 'Norfolk',
            'Place of Performance State': 'VA',
            'Award Amount': 125000,
            'Period of Performance Current End Date': '2026-12-31',
            'Period of Performance Start Date': '2025-01-01',
            'NAICS Code': '561720',
            'NAICS Description': 'Janitorial Services',
            'Award ID': 'GSA-2025-001',
            'Award Type': 'Firm Fixed Price',
            'Recipient Name': 'ABC Cleaning Services'
        }
        
        result = self.fetcher._parse_usaspending_award(mock_award)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['naics_code'], '561720')
        self.assertIn('Janitorial', result['title'])
        self.assertEqual(result['agency'], 'General Services Administration')
        self.assertEqual(result['location'], 'Norfolk, VA')
        self.assertEqual(result['value'], '$125,000')
        self.assertIn('GSA-2025-001', result['notice_id'])
    
    def test_parse_usaspending_award_minimal_data(self):
        """Test parsing award with minimal/missing data (fallback handling)"""
        mock_award = {
            'Awarding Agency': 'Department of Defense',
            'Award Amount': 50000
        }
        
        result = self.fetcher._parse_usaspending_award(mock_award)
        
        self.assertIsNotNone(result)
        self.assertIn('Department of Defense', result['title'])  # Generated title
        self.assertEqual(result['agency'], 'Department of Defense')
        self.assertEqual(result['value'], '$50,000')
        self.assertEqual(result['naics_code'], '561720')  # Default fallback
    
    def test_parse_usaspending_award_zero_value(self):
        """Test handling awards with zero or missing value"""
        mock_award = {
            'Description': 'Test Contract',
            'Awarding Agency': 'Test Agency',
            'Award Amount': 0
        }
        
        result = self.fetcher._parse_usaspending_award(mock_award)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['value'], 'Contact agency for details')
    
    @patch('datagov_bulk_fetcher.requests.post')
    def test_fetch_usaspending_contracts_success(self, mock_post):
        """Test successful fetch from USAspending API"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'Description': 'Custodial Services',
                    'Awarding Agency': 'Veterans Affairs',
                    'NAICS Code': '561720',
                    'Award Amount': 100000,
                    'Place of Performance State': 'VA',
                    'Award ID': 'VA-2025-100'
                }
            ]
        }
        mock_post.return_value = mock_response
        
        contracts = self.fetcher.fetch_usaspending_contracts(days_back=7)
        
        self.assertGreater(len(contracts), 0)
        self.assertEqual(contracts[0]['naics_code'], '561720')
    
    @patch('datagov_bulk_fetcher.requests.post')
    def test_fetch_usaspending_contracts_api_error(self, mock_post):
        """Test handling API error response"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response
        
        contracts = self.fetcher.fetch_usaspending_contracts(days_back=7)
        
        self.assertEqual(len(contracts), 0)  # Should return empty list on error
    
    @patch('datagov_bulk_fetcher.requests.post')
    def test_prioritization_561720_first(self, mock_post):
        """Test that NAICS 561720 contracts appear first in results"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {'Description': 'General Service', 'Awarding Agency': 'Agency1', 
                 'NAICS Code': '561900', 'Award Amount': 50000, 'Place of Performance State': 'VA', 
                 'Award ID': 'A1'},
                {'Description': 'Janitorial Services', 'Awarding Agency': 'Agency2', 
                 'NAICS Code': '561720', 'Award Amount': 100000, 'Place of Performance State': 'VA', 
                 'Award ID': 'A2'},
                {'Description': 'Landscaping', 'Awarding Agency': 'Agency3', 
                 'NAICS Code': '561730', 'Award Amount': 75000, 'Place of Performance State': 'VA', 
                 'Award ID': 'A3'}
            ]
        }
        mock_post.return_value = mock_response
        
        contracts = self.fetcher.fetch_usaspending_contracts(days_back=7)
        
        # First contract should be the 561720 one (prepended for highest priority)
        cleaning_561720 = [c for c in contracts if c['naics_code'] == '561720']
        self.assertGreater(len(cleaning_561720), 0)
        # Verify 561720 appears early in the list
        first_561720_index = next((i for i, c in enumerate(contracts) if c['naics_code'] == '561720'), None)
        self.assertIsNotNone(first_561720_index)
        self.assertLess(first_561720_index, len(contracts) // 2, "561720 should appear in first half")


if __name__ == '__main__':
    unittest.main()
