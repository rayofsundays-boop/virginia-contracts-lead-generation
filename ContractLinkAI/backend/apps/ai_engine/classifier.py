"""
AI Classification Engine for RFPs.
Uses OpenAI GPT-4o-mini for intelligent classification and metadata extraction.
"""
import openai
from typing import Dict, List, Optional, Tuple
import json
import logging
from django.conf import settings
import time

logger = logging.getLogger('ai_engine')

# Initialize OpenAI client
openai.api_key = settings.OPENAI_API_KEY


class AIClassifier:
    """
    AI-powered RFP classifier using OpenAI GPT models.
    """
    
    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    def classify_rfp(self, title: str, description: str) -> Dict:
        """
        Classify an RFP into categories with confidence scores.
        
        Args:
            title: RFP title
            description: RFP description
            
        Returns:
            Dictionary with classification results
        """
        start_time = time.time()
        
        prompt = self._build_classification_prompt(title, description)
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in government procurement and contract classification. Analyze RFP documents and provide accurate categorization."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            result = json.loads(response.choices[0].message.content)
            result['processing_time_ms'] = processing_time
            result['tokens_used'] = response.usage.total_tokens
            result['model_name'] = self.model
            
            logger.info(f"Classified RFP: {result.get('predicted_category')} ({result.get('confidence_score')})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error classifying RFP: {str(e)}")
            return {
                'predicted_category': 'other',
                'confidence_score': 0.0,
                'reasoning': f'Error: {str(e)}',
                'extracted_keywords': [],
                'top_predictions': []
            }
    
    def classify_rfp_with_confidence(self, title: str, description: str) -> Tuple[str, float]:
        """
        Simplified classification returning category and confidence.
        
        Returns:
            Tuple of (category, confidence_score)
        """
        result = self.classify_rfp(title, description)
        return result.get('predicted_category', 'other'), result.get('confidence_score', 0.0)
    
    def classify_rfp_with_label_explanation(self, title: str, description: str) -> Dict:
        """
        Enhanced classification with detailed reasoning.
        Uses chain-of-thought for improved accuracy.
        
        Returns:
            Dictionary with classification and explanation
        """
        start_time = time.time()
        
        # Multi-pass approach: First get reasoning, then classification
        reasoning_prompt = f"""Analyze this RFP and explain what type of service/product it requires:

Title: {title}
Description: {description[:500]}

Provide a brief analysis of what this RFP is about."""

        explanation_prompt = f"""Based on this RFP, classify it into one of these categories:
- janitorial: Janitorial, cleaning, custodial services
- construction: Construction, renovation, building
- it_services: IT, software, technology services
- consulting: Consulting, advisory services
- maintenance: Maintenance, repair services
- supplies: Supplies, equipment procurement
- professional_services: Professional services (legal, accounting, etc.)
- transportation: Transportation, logistics
- other: Other services

Title: {title}
Description: {description[:500]}

Return a JSON object with:
{{
    "predicted_category": "category_name",
    "confidence_score": 0.0-1.0,
    "reasoning": "your explanation",
    "extracted_keywords": ["keyword1", "keyword2"],
    "top_predictions": [
        {{"category": "category1", "confidence": 0.85}},
        {{"category": "category2", "confidence": 0.10}}
    ]
}}"""
        
        try:
            # First pass: Get reasoning
            reasoning_response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert procurement analyst."
                    },
                    {
                        "role": "user",
                        "content": reasoning_prompt
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            reasoning = reasoning_response.choices[0].message.content
            
            # Second pass: Classification with reasoning context
            classification_response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert procurement analyst. Use the analysis to classify accurately."
                    },
                    {
                        "role": "assistant",
                        "content": reasoning
                    },
                    {
                        "role": "user",
                        "content": explanation_prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            result = json.loads(classification_response.choices[0].message.content)
            result['processing_time_ms'] = processing_time
            result['tokens_used'] = reasoning_response.usage.total_tokens + classification_response.usage.total_tokens
            result['model_name'] = self.model
            result['chain_of_thought'] = reasoning
            
            logger.info(f"Enhanced classification: {result.get('predicted_category')} ({result.get('confidence_score')})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced classification: {str(e)}")
            # Fallback to simple classification
            return self.classify_rfp(title, description)
    
    def _build_classification_prompt(self, title: str, description: str) -> str:
        """Build the classification prompt."""
        return f"""Classify this government RFP/procurement opportunity into one of these categories:

Categories:
- janitorial: Janitorial, cleaning, custodial, sanitation services
- construction: Construction, renovation, building projects
- it_services: IT, software, technology, cybersecurity services
- consulting: Consulting, advisory, strategic planning services
- maintenance: Maintenance, repair, facilities management
- supplies: Supplies, equipment, materials procurement
- professional_services: Professional services (legal, accounting, HR, etc.)
- transportation: Transportation, logistics, fleet services
- other: Other services not fitting above categories

RFP Details:
Title: {title}
Description: {description[:500]}

Return a JSON object with:
{{
    "predicted_category": "category_name",
    "confidence_score": 0.0-1.0,
    "reasoning": "brief explanation",
    "extracted_keywords": ["keyword1", "keyword2", "keyword3"],
    "top_predictions": [
        {{"category": "top_category", "confidence": 0.85}},
        {{"category": "second_category", "confidence": 0.10}},
        {{"category": "third_category", "confidence": 0.05}}
    ]
}}"""


class MetadataExtractor:
    """
    Extract structured metadata from RFP pages using AI.
    """
    
    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
    
    def extract_metadata_from_page(self, page_content: str) -> Dict:
        """
        Extract structured metadata from RFP page content.
        
        Args:
            page_content: HTML or text content of RFP page
            
        Returns:
            Dictionary with extracted metadata
        """
        prompt = f"""Extract key information from this government RFP page:

{page_content[:2000]}

Return a JSON object with:
{{
    "contact_name": "name or empty",
    "contact_email": "email or empty",
    "contact_phone": "phone or empty",
    "estimated_value": "dollar amount or null",
    "contract_duration": "duration text or empty",
    "requirements": "brief summary of requirements",
    "due_date": "date string or empty",
    "naics_codes": ["code1", "code2"],
    "keywords": ["keyword1", "keyword2"]
}}"""
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured data from government procurement documents."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info("Successfully extracted metadata from page")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {}


class CityPortalDiscovery:
    """
    AI-powered discovery of city procurement portals.
    """
    
    def __init__(self):
        self.model = settings.OPENAI_MODEL
    
    def find_city_portal(self, city_name: str, state_code: str) -> Dict:
        """
        Use AI to find procurement portal URL for a city.
        
        Args:
            city_name: Name of the city
            state_code: Two-letter state code
            
        Returns:
            Dictionary with portal information and confidence
        """
        prompt = f"""Find the official government procurement portal for {city_name}, {state_code}.

Provide the most likely official procurement/bidding portal URL where contractors can find RFPs and bids.

Return a JSON object with:
{{
    "portal_url": "full URL or empty if unsure",
    "portal_name": "official portal name",
    "confidence_score": 0.0-1.0,
    "reasoning": "why this is the correct portal",
    "search_queries_used": ["query1", "query2"],
    "alternative_urls": ["url1", "url2"]
}}

Important:
- Only return official government websites (.gov domains preferred)
- Confidence should be high (>0.7) only if certain
- Include reasoning for transparency"""
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at finding government procurement portals. Only suggest official government websites."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['city_name'] = city_name
            result['state_code'] = state_code
            result['model_name'] = self.model
            
            logger.info(f"Found portal for {city_name}, {state_code}: {result.get('portal_url')} (confidence: {result.get('confidence_score')})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding city portal: {str(e)}")
            return {
                'portal_url': '',
                'portal_name': '',
                'confidence_score': 0.0,
                'reasoning': f'Error: {str(e)}',
                'search_queries_used': [],
                'alternative_urls': []
            }
