import requests
import logging
import time
from typing import Dict, List, Optional, Any, Generator
from datetime import datetime, timezone
import json
from loki_logger import get_logger, log_api_call


class HubSpotAPIService:
    """
    Service for interacting with HubSpot CRM API v3 for deals extraction
    """
    
    def __init__(self, access_token: str, base_url: str = "https://api.hubapi.com"):
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'HubSpot-Deals-ETL-Service/1.0'
        })
        
        # Rate limiting configuration (150 requests per 10 seconds)
        self.rate_limit = 150
        self.rate_period = 10  # seconds
        self.request_interval = self.rate_period / self.rate_limit  # ~0.067 seconds
        self.last_request_time = 0
        
        self.logger.debug(
            "HubSpot API service initialized",
            extra={
                'operation': 'hubspot_api_init', 
                'base_url': base_url,
                'rate_limit': self.rate_limit,
                'rate_period': self.rate_period
            }
        )
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            self.logger.debug(
                f"Rate limiting: sleeping for {sleep_time:.3f} seconds",
                extra={'operation': 'rate_limit_wait', 'sleep_time': sleep_time}
            )
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _handle_rate_limit_response(self, response: requests.Response) -> bool:
        """Handle 429 rate limit responses with exponential backoff"""
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            self.logger.warning(
                "Rate limited by HubSpot API",
                extra={
                    'operation': 'rate_limit_handler',
                    'retry_after': retry_after,
                    'status_code': 429
                }
            )
            time.sleep(retry_after)
            return True
        return False
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with rate limiting and retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            self._wait_for_rate_limit()
            
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Handle rate limiting
                if self._handle_rate_limit_response(response):
                    continue  # Retry after rate limit wait
                
                # Handle other errors
                if response.status_code >= 400:
                    self.logger.warning(
                        f"HTTP {response.status_code} error",
                        extra={
                            'operation': 'http_request',
                            'method': method,
                            'url': url,
                            'status_code': response.status_code,
                            'attempt': attempt + 1
                        }
                    )
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                
                wait_time = (2 ** attempt) + (time.time() % 1)  # Exponential backoff with jitter
                self.logger.warning(
                    f"Request failed, retrying in {wait_time:.2f}s",
                    extra={
                        'operation': 'request_retry',
                        'attempt': attempt + 1,
                        'error': str(e),
                        'wait_time': wait_time
                    }
                )
                time.sleep(wait_time)
        
        raise Exception(f"Max retries ({max_retries}) exceeded")
    
    def validate_credentials(self) -> bool:
        """
        Validate HubSpot API access token by making a test request
        """
        try:
            self.logger.debug(
                "Validating HubSpot access token",
                extra={'operation': 'validate_credentials'}
            )
            
            url = f"{self.base_url}/crm/v3/objects/deals"
            params = {'limit': 1}
            
            response = self._make_request('GET', url, params=params)
            is_valid = response.status_code == 200
            
            if is_valid:
                self.logger.info(
                    "HubSpot credentials validation successful",
                    extra={'operation': 'validate_credentials'}
                )
            else:
                self.logger.warning(
                    "HubSpot credentials validation failed",
                    extra={
                        'operation': 'validate_credentials',
                        'status_code': response.status_code
                    }
                )
            
            return is_valid
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "HubSpot credentials validation error",
                extra={'operation': 'validate_credentials', 'error': str(e)},
                exc_info=True
            )
            return False
    
    def get_deals(self, 
                  limit: int = 100, 
                  after: Optional[str] = None,
                  properties: Optional[List[str]] = None,
                  archived: bool = False,
                  **filters) -> Dict[str, Any]:
        """
        Get deals from HubSpot CRM API v3
        
        Args:
            limit: Number of deals to retrieve (max 100)
            after: Pagination cursor
            properties: List of properties to include
            archived: Include archived deals
            **filters: Additional filters (dealstage, pipeline, etc.)
        
        Returns:
            Dict containing deals data and pagination info
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(
                "Retrieving deals from HubSpot",
                extra={
                    'operation': 'get_deals',
                    'limit': limit,
                    'has_cursor': after is not None,
                    'archived': archived,
                    'properties_count': len(properties) if properties else 0
                }
            )
            
            # Build parameters
            params = {
                'limit': min(limit, 100),  # HubSpot API limit
                'archived': str(archived).lower()
            }
            
            if after:
                params['after'] = after
            
            # Add properties
            if properties:
                params['properties'] = ','.join(properties)
            else:
                # Default properties for deals
                default_properties = [
                    'dealname', 'amount', 'dealstage', 'closedate', 'pipeline',
                    'dealtype', 'hubspot_owner_id', 'description', 'createdate',
                    'hs_lastmodifieddate', 'hs_deal_stage_probability'
                ]
                params['properties'] = ','.join(default_properties)
            
            # Add additional filters
            for key, value in filters.items():
                if value is not None:
                    params[key] = value
            
            url = f"{self.base_url}/crm/v3/objects/deals"
            response = self._make_request('GET', url, params=params)
            
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            result = response.json()
            
            deals_count = len(result.get('results', []))
            has_more = 'paging' in result and 'next' in result['paging']
            
            self.logger.info(
                "Deals retrieved successfully",
                extra={
                    'operation': 'get_deals',
                    'status_code': response.status_code,
                    'duration_ms': round(duration_ms, 2),
                    'deals_count': deals_count,
                    'has_more': has_more
                }
            )
            
            log_api_call(
                self.logger,
                "hubspot_get_deals",
                method='GET',
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )
            
            return result
            
        except requests.exceptions.RequestException as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self.logger.error(
                "Error fetching deals from HubSpot",
                extra={
                    'operation': 'get_deals',
                    'error': str(e),
                    'duration_ms': round(duration_ms, 2),
                    'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                },
                exc_info=True
            )
            
            log_api_call(
                self.logger,
                "hubspot_get_deals",
                method='GET',
                status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else 500,
                duration_ms=round(duration_ms, 2)
            )
            
            raise
    
    def get_deal_by_id(self, deal_id: str, properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get a specific deal by ID
        
        Args:
            deal_id: HubSpot deal ID
            properties: List of properties to include
        
        Returns:
            Dict containing deal data
        """
        try:
            self.logger.debug(
                "Retrieving deal by ID",
                extra={'operation': 'get_deal_by_id', 'deal_id': deal_id}
            )
            
            params = {}
            if properties:
                params['properties'] = ','.join(properties)
            
            url = f"{self.base_url}/crm/v3/objects/deals/{deal_id}"
            response = self._make_request('GET', url, params=params)
            
            result = response.json()
            
            self.logger.debug(
                "Deal retrieved by ID",
                extra={
                    'operation': 'get_deal_by_id',
                    'deal_id': deal_id,
                    'deal_name': result.get('properties', {}).get('dealname')
                }
            )
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Error fetching deal by ID",
                extra={'operation': 'get_deal_by_id', 'deal_id': deal_id, 'error': str(e)},
                exc_info=True
            )
            raise
    
    def get_deal_properties(self) -> List[Dict[str, Any]]:
        """
        Get all available deal properties from HubSpot
        
        Returns:
            List of property definitions
        """
        try:
            self.logger.debug(
                "Retrieving deal properties",
                extra={'operation': 'get_deal_properties'}
            )
            
            url = f"{self.base_url}/crm/v3/properties/deals"
            response = self._make_request('GET', url)
            
            result = response.json()
            properties = result.get('results', [])
            
            self.logger.info(
                "Deal properties retrieved",
                extra={
                    'operation': 'get_deal_properties',
                    'properties_count': len(properties)
                }
            )
            
            return properties
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Error fetching deal properties",
                extra={'operation': 'get_deal_properties', 'error': str(e)},
                exc_info=True
            )
            raise
    
    def get_pipelines(self) -> List[Dict[str, Any]]:
        """
        Get all deal pipelines from HubSpot
        
        Returns:
            List of pipeline definitions
        """
        try:
            self.logger.debug(
                "Retrieving deal pipelines",
                extra={'operation': 'get_pipelines'}
            )
            
            url = f"{self.base_url}/crm/v3/pipelines/deals"
            response = self._make_request('GET', url)
            
            result = response.json()
            pipelines = result.get('results', [])
            
            self.logger.info(
                "Deal pipelines retrieved",
                extra={
                    'operation': 'get_pipelines',
                    'pipelines_count': len(pipelines)
                }
            )
            
            return pipelines
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Error fetching deal pipelines",
                extra={'operation': 'get_pipelines', 'error': str(e)},
                exc_info=True
            )
            raise
    
    def get_all_deals(self, 
                      properties: Optional[List[str]] = None,
                      archived: bool = False,
                      **filters) -> Generator[Dict[str, Any], None, None]:
        """
        Generator that yields all deals with automatic pagination
        
        Args:
            properties: List of properties to include
            archived: Include archived deals
            **filters: Additional filters
        
        Yields:
            Individual deal dictionaries
        """
        after = None
        page_count = 0
        total_deals = 0
        
        self.logger.info(
            "Starting paginated deals extraction",
            extra={
                'operation': 'get_all_deals',
                'archived': archived,
                'properties_count': len(properties) if properties else 0
            }
        )
        
        while True:
            try:
                page_count += 1
                response = self.get_deals(
                    limit=100,
                    after=after,
                    properties=properties,
                    archived=archived,
                    **filters
                )
                
                deals = response.get('results', [])
                if not deals:
                    break
                
                for deal in deals:
                    total_deals += 1
                    yield deal
                
                # Check for next page
                paging = response.get('paging', {})
                if 'next' not in paging:
                    break
                
                after = paging['next']['after']
                
                self.logger.debug(
                    f"Completed page {page_count}",
                    extra={
                        'operation': 'get_all_deals',
                        'page': page_count,
                        'deals_in_page': len(deals),
                        'total_deals': total_deals,
                        'has_next': True
                    }
                )
                
            except Exception as e:
                self.logger.error(
                    f"Error on page {page_count}",
                    extra={
                        'operation': 'get_all_deals',
                        'page': page_count,
                        'error': str(e)
                    },
                    exc_info=True
                )
                raise
        
        self.logger.info(
            "Completed paginated deals extraction",
            extra={
                'operation': 'get_all_deals',
                'total_pages': page_count,
                'total_deals': total_deals
            }
        )
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to HubSpot API and return comprehensive status
        
        Returns:
            Dict with connection test results
        """
        self.logger.info(
            "Testing HubSpot API connection",
            extra={'operation': 'test_connection'}
        )
        
        results = {
            'credentials_valid': False,
            'api_reachable': False,
            'deals_accessible': False,
            'properties_accessible': False,
            'pipelines_accessible': False,
            'rate_limit_info': None,
            'error': None
        }
        
        try:
            # Test credentials
            results['credentials_valid'] = self.validate_credentials()
            results['api_reachable'] = results['credentials_valid']
            
            if results['credentials_valid']:
                # Test deals access
                try:
                    test_deals = self.get_deals(limit=1)
                    results['deals_accessible'] = True
                    
                    # Extract rate limit info from headers if available
                    # Note: HubSpot doesn't always provide rate limit headers
                    results['rate_limit_info'] = {
                        'limit': self.rate_limit,
                        'period_seconds': self.rate_period,
                        'requests_per_second': round(self.rate_limit / self.rate_period, 2)
                    }
                    
                except Exception as e:
                    self.logger.warning(
                        "Deals access test failed",
                        extra={'operation': 'test_connection', 'error': str(e)}
                    )
                
                # Test properties access (optional)
                try:
                    properties = self.get_deal_properties()
                    results['properties_accessible'] = len(properties) > 0
                except Exception as e:
                    self.logger.debug(
                        "Properties access test failed (optional)",
                        extra={'operation': 'test_connection', 'error': str(e)}
                    )
                
                # Test pipelines access (optional)
                try:
                    pipelines = self.get_pipelines()
                    results['pipelines_accessible'] = len(pipelines) > 0
                except Exception as e:
                    self.logger.debug(
                        "Pipelines access test failed (optional)",
                        extra={'operation': 'test_connection', 'error': str(e)}
                    )
                
                self.logger.info(
                    "HubSpot connection test completed",
                    extra={
                        'operation': 'test_connection',
                        'credentials_valid': results['credentials_valid'],
                        'deals_accessible': results['deals_accessible'],
                        'properties_accessible': results['properties_accessible'],
                        'pipelines_accessible': results['pipelines_accessible']
                    }
                )
            else:
                self.logger.warning(
                    "HubSpot connection test failed - invalid credentials",
                    extra={'operation': 'test_connection'}
                )
                
        except Exception as e:
            results['error'] = str(e)
            self.logger.error(
                "HubSpot connection test error",
                extra={'operation': 'test_connection', 'error': str(e)},
                exc_info=True
            )
        
        return results