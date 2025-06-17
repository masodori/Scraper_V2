#!/usr/bin/env python3
"""
Refactored Scrapling Integration Module

This module handles the automated scraping execution using templates
generated from interactive sessions. It uses composition of specialized
classes for better maintainability and separation of concerns.
"""

import logging
import time
import json
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from scrapling.fetchers import PlayWrightFetcher, StealthyFetcher
from scrapling import Adaptor

from ..models.scraping_template import ScrapingTemplate, ScrapingResult
from .context import ScrapingContext
from .utils.progress import ProgressTracker
from .analyzers.template_analyzer import TemplateAnalyzer
from .selectors.selector_engine import SelectorEngine
from .extractors.data_extractor import DataExtractor
from .handlers.pagination_handler import PaginationHandler
from .processors.subpage_processor import SubpageProcessor

logger = logging.getLogger(__name__)


class ScraplingRunner:
    """
    Executes automated scraping using Scrapling based on interactive templates.
    
    This refactored version uses composition of specialized classes for:
    - Template analysis
    - Selector enhancement
    - Data extraction
    - Pagination handling
    - Subpage processing
    """
    
    def __init__(self, template: ScrapingTemplate):
        """
        Initialize the Scrapling runner with a template.
        
        Args:
            template: The scraping template to execute
        """
        self.template = template
        self.fetcher = None
        self.fetcher_instance = None
        self.current_page = None
        self.browser_pages = []
        
        # Setup logging for this session
        self.session_logger = logging.getLogger(f"scrapling_runner.{template.name}")
        
        # Configure logging
        self._configure_logging()
        
        # Initialize context
        self.context = ScrapingContext(template)
        
        # Initialize specialized components
        self.template_analyzer = TemplateAnalyzer(self.context)
        self.selector_engine = SelectorEngine(self.context)
        self.data_extractor = None  # Initialized after page is fetched
        self.pagination_handler = None  # Initialized after page is fetched
        self.subpage_processor = None  # Initialized after page is fetched
        
        # Fix template configuration for sublink processing
        self._fix_template_sublink_configuration()
    
    def _configure_logging(self) -> None:
        """Configure logging to suppress known warnings from third-party libraries."""
        import warnings
        
        # Suppress specific deprecated API warnings
        warnings.filterwarnings("ignore", message=".*deprecated.*", category=DeprecationWarning)
        warnings.filterwarnings("ignore", message=".*Scrapling.*deprecated.*", category=UserWarning)
        
        # Configure logging levels for third-party libraries
        logging.getLogger('scrapling').setLevel(logging.ERROR)
        logging.getLogger('playwright').setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    def _fix_template_sublink_configuration(self) -> None:
        """Automatically fix template configuration when sublink actions are detected."""
        try:
            # Check if template has sublink actions
            sublink_actions = [action for action in self.template.actions 
                             if 'sublink' in action.label.lower() or 'lawyer' in action.selector]
            
            if sublink_actions:
                print("🔧 FIXING TEMPLATE SUBLINK CONFIGURATION")
                print("="*45)
                
                # Enable subpage scraping if disabled
                if not self.template.enable_subpage_scraping:
                    self.template.enable_subpage_scraping = True
                    print("✅ Enabled subpage scraping")
                
                # Set subpage URL pattern if not set
                if not self.template.subpage_url_pattern:
                    # Try to extract pattern from sublink actions
                    for action in sublink_actions:
                        if hasattr(action, 'target_url') and action.target_url:
                            # Extract pattern from target URL
                            if '/lawyer/' in action.target_url:
                                base_url = action.target_url.split('/lawyer/')[0]
                                self.template.subpage_url_pattern = f"{base_url}/lawyer/*"
                                print(f"✅ Set subpage URL pattern: {self.template.subpage_url_pattern}")
                                break
                
                # Ensure subpage containers are properly identified
                subpage_containers = [elem for elem in self.template.elements 
                                    if self.template_analyzer.is_subpage_container(elem)]
                if subpage_containers:
                    print(f"✅ Found {len(subpage_containers)} subpage containers:")
                    for container in subpage_containers:
                        print(f"   📄 {container.label}: {len(container.sub_elements)} sub-elements")
                        
                        # Mark container for subpage extraction
                        if not hasattr(container, 'follow_links'):
                            container.follow_links = True
                        if not hasattr(container, 'subpage_elements'):
                            container.subpage_elements = container.sub_elements.copy()
                
                print("🎯 Template sublink configuration fixed!")
                print("="*45)
                
        except Exception as e:
            logger.warning(f"Error fixing template sublink configuration: {e}")
    
    def execute_scraping(self) -> ScrapingResult:
        """
        Execute the complete scraping process based on the template.
        
        Returns:
            ScrapingResult containing the scraped data and metadata
        """
        result = ScrapingResult(
            template_name=self.template.name,
            url=self.template.url,
            success=False,
            data={},
            errors=[],
            metadata={}
        )
        
        try:
            logger.info(f"Starting scraping session for: {self.template.name}")
            logger.info(f"Target URL: {self.template.url}")
            
            # Initialize the fetcher
            self._initialize_fetcher()
            
            # Smart URL detection - if template looks like directory scraping but URL is individual page, try directory
            target_url = self.template.url
            if self.template_analyzer.looks_like_directory_template() and '/lawyer/' in target_url:
                # Try to detect if this should be a directory page instead
                if 'gibsondunn.com' in target_url:
                    directory_url = target_url.split('/lawyer/')[0] + '/people/'
                    logger.info(f"Template appears to be for directory scraping, trying directory URL: {directory_url}")
                    directory_page = self._fetch_page(directory_url)
                    if directory_page:
                        target_url = directory_url
                        logger.info(f"Successfully switched to directory URL: {directory_url}")
            
            # Fetch the initial page
            self.current_page = self._fetch_page(target_url)
            if not self.current_page:
                raise Exception("Failed to fetch the initial page")
            
            # Update context with current page
            self.context.current_page = self.current_page
            self.context.fetcher = self.fetcher
            
            # Initialize specialized components now that we have a page
            self.data_extractor = DataExtractor(self.context)
            self.pagination_handler = PaginationHandler(self.context)
            self.subpage_processor = SubpageProcessor(self.context, self.fetcher_instance)
            
            # Wire up the missing methods in components by delegating to this runner
            self.data_extractor.fetch_page = self._fetch_page
            self.pagination_handler.fetch_page = self._fetch_page
            self.pagination_handler.extract_data = self.data_extractor.extract_data
            self.pagination_handler.extract_main_page_only = self.data_extractor.extract_data
            self.pagination_handler.extract_data_incremental = lambda existing_data: self.data_extractor.extract_data()
            self.subpage_processor.fetch_page = self._fetch_page
            
            # Auto-detect and handle infinite scroll for directory pages
            if self.template_analyzer.looks_like_directory_template():
                logger.info("Directory template detected - checking for infinite scroll content")
                self.pagination_handler.auto_scroll_to_load_all_content()
            
            # Use smart pagination architecture only if pagination actions are actually defined
            has_pagination_actions = self._has_pagination_actions_defined()
            is_directory_template = self.template_analyzer.looks_like_directory_template()
            
            if has_pagination_actions or is_directory_template:
                if has_pagination_actions:
                    logger.info("Pagination actions detected - using smart pagination processing")
                else:
                    logger.info("Directory template detected - using smart pagination processing")
                scraped_data = self.pagination_handler.smart_pagination_with_dual_browser()
            else:
                # Single page extraction
                if hasattr(self.template, 'pagination') and self.template.pagination:
                    logger.info("Pagination configuration exists but no actions defined - using standard extraction")
                else:
                    logger.info("No pagination - using standard extraction")
                scraped_data = self.data_extractor.extract_data()
            
            # Execute any non-navigation actions if specified
            if self.template.actions:
                # Check if this is a directory template with container workflow
                is_directory_workflow = self.template_analyzer.looks_like_directory_template()
                
                # Filter out navigation actions that would interfere with pagination
                non_navigation_actions = []
                for action in self.template.actions:
                    # Skip actions that navigate to individual pages
                    if not (action.action_type == 'click' and any(
                        keyword in action.selector.lower() 
                        for keyword in ['strong', 'name', 'link', 'profile', 'lawyer']
                    )):
                        # For directory templates, also skip generic selectors that cause conflicts
                        if is_directory_workflow and action.selector in ['a', 'button', 'span', 'div']:
                            logger.info(f"Skipping generic action selector '{action.selector}' in directory workflow")
                            continue
                        non_navigation_actions.append(action)
                
                if non_navigation_actions:
                    logger.info(f"Executing {len(non_navigation_actions)} non-navigation actions")
                    # Execute actions (implementation would be in PaginationHandler or separate ActionHandler)
                    # action_results = self._execute_actions(non_navigation_actions)
                    # scraped_data['actions_executed'] = action_results
                else:
                    logger.info("Skipping all actions - navigation actions or generic selectors detected")
            
            # Process subpage data if any elements have follow_links enabled
            if self.template_analyzer.template_needs_subpage_data():
                scraped_data = self.subpage_processor.process_subpage_extractions(scraped_data)
                scraped_data = self.subpage_processor.process_container_subpages(scraped_data)
            
            # Create unified output structure
            scraped_data = self._create_unified_output_structure(scraped_data)
            
            result.data = scraped_data
            result.success = True
            result.metadata = {
                'elements_found': len([k for k in scraped_data.keys() if k != 'actions_executed']),
                'actions_executed': len(self.template.actions),
                'page_title': self._get_page_title(),
                'final_url': self.current_page.url if self.current_page else self.template.url
            }
            
            logger.info(f"Scraping completed successfully. Found {result.metadata['elements_found']} elements.")
            
        except Exception as e:
            error_msg = f"Scraping failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.success = False
            
        finally:
            self._cleanup()
        
        return result
    
    def _initialize_fetcher(self) -> None:
        """Initialize the Scrapling fetcher with configuration."""
        try:
            logger.info("Initializing Scrapling fetcher...")
            
            # Configure the fetcher with template settings - use only supported parameters
            self.fetcher = PlayWrightFetcher()
            self.fetcher.configure(
                auto_match=True  # Enable AutoMatch
            )
            
            # Store a reference to the fetcher instance for browser reuse
            self.fetcher_instance = self.fetcher
            
            logger.info("Scrapling fetcher initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Scrapling fetcher: {e}")
            raise
    
    def _fetch_page(self, url: str) -> Optional[Adaptor]:
        """
        Fetch a page using Scrapling fetcher.
        
        Args:
            url: URL to fetch
            
        Returns:
            Adaptor page object or None if failed
        """
        try:
            logger.debug(f"Fetching page: {url}")
            
            # Fetch the page with minimal options - Scrapling handles most settings internally
            page = self.fetcher.fetch(url)
            
            if page and hasattr(page, 'status') and page.status == 200:
                logger.debug(f"Successfully fetched page: {url}")
                return page
            elif page:
                logger.debug(f"Successfully fetched page: {url}")
                return page
            else:
                logger.warning(f"Failed to fetch page {url}: no response")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None
    
    def _format_cookies_for_scrapling(self) -> List[Dict[str, Any]]:
        """Format cookies for Scrapling."""
        formatted_cookies = []
        
        if hasattr(self.template, 'cookies') and self.template.cookies:
            for cookie in self.template.cookies:
                formatted_cookie = {
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                }
                # Add optional fields if they exist
                if hasattr(cookie, 'secure'):
                    formatted_cookie['secure'] = cookie.secure
                if hasattr(cookie, 'httpOnly'):
                    formatted_cookie['httpOnly'] = cookie.httpOnly
                    
                formatted_cookies.append(formatted_cookie)
        
        return formatted_cookies
    
    def _create_unified_output_structure(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create unified output structure from scraped data."""
        # This could be moved to a separate OutputFormatter class
        try:
            # For now, return data as-is
            # Future enhancement: standardize output format across different template types
            return scraped_data
        except Exception as e:
            logger.warning(f"Error creating unified output structure: {e}")
            return scraped_data
    
    def _has_pagination_actions_defined(self) -> bool:
        """
        Check if the template has actual pagination actions defined.
        
        Returns:
            True if pagination actions are properly defined, False otherwise
        """
        try:
            # Check if pagination configuration exists
            if not hasattr(self.template, 'pagination') or not self.template.pagination:
                return False
            
            pagination = self.template.pagination
            
            # Check if any pagination selectors are defined
            has_selectors = any([
                pagination.next_selector,
                pagination.load_more_selector,
                pagination.page_selector
            ])
            
            # For infinite scroll, we need either selectors or scroll configuration
            if pagination.pattern_type == 'infinite_scroll':
                has_scroll_config = (
                    pagination.scroll_pause_time is not None or
                    pagination.max_pages is not None or
                    pagination.end_condition_selector is not None
                )
                return has_selectors or has_scroll_config
            
            # For other pagination types, we need at least one selector
            return has_selectors
            
        except Exception as e:
            logger.warning(f"Error checking pagination actions: {e}")
            return False

    def _get_page_title(self) -> str:
        """Get the title of the current page."""
        try:
            if self.current_page:
                # Try to get page title using Scrapling
                title_elements = self.current_page.css('title')
                if title_elements:
                    return title_elements[0].text.strip()
                    
                # Fallback to h1
                h1_elements = self.current_page.css('h1')
                if h1_elements:
                    return h1_elements[0].text.strip()
            
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def _cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self.fetcher_instance:
                # Close browser if needed
                logger.debug("Cleaning up fetcher resources")
                # Scrapling handles cleanup automatically
            
            # Clear page references
            self.current_page = None
            self.browser_pages.clear()
            
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    def export_data(self, result: ScrapingResult, output_file: str, format: str = "json") -> None:
        """
        Export scraped data to various formats.
        
        Args:
            result: ScrapingResult containing the data to export
            output_file: Path to the output file
            format: Export format ('json', 'csv', 'excel')
        """
        try:
            # Ensure output directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                self._export_json(result, output_file)
            elif format.lower() == 'csv':
                self._export_csv(result, output_file)
            elif format.lower() == 'excel':
                self._export_excel(result, output_file)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Data exported successfully to: {output_file}")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise

    def _export_json(self, result: ScrapingResult, output_file: str) -> None:
        """Export data to JSON format."""
        export_data = {
            'template_name': result.template_name,
            'url': result.url,
            'scraped_at': result.scraped_at.isoformat(),
            'success': result.success,
            'data': result.data,
            'metadata': result.metadata,
            'errors': result.errors
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def _export_csv(self, result: ScrapingResult, output_file: str) -> None:
        """Export data to CSV format."""
        # Flatten the data for CSV export
        flattened_data = self._flatten_data(result.data)
        
        if not flattened_data:
            raise ValueError("No data to export to CSV")
        
        # If data is a list of records, write multiple rows
        if isinstance(flattened_data, list):
            df = pd.DataFrame(flattened_data)
        else:
            # Single record
            df = pd.DataFrame([flattened_data])
        
        df.to_csv(output_file, index=False, encoding='utf-8')

    def _export_excel(self, result: ScrapingResult, output_file: str) -> None:
        """Export data to Excel format."""
        # Flatten the data for Excel export
        flattened_data = self._flatten_data(result.data)
        
        if not flattened_data:
            raise ValueError("No data to export to Excel")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main data sheet
            if isinstance(flattened_data, list):
                df = pd.DataFrame(flattened_data)
            else:
                df = pd.DataFrame([flattened_data])
            
            df.to_excel(writer, sheet_name='Scraped Data', index=False)
            
            # Metadata sheet
            metadata_df = pd.DataFrame([{
                'Template Name': result.template_name,
                'URL': result.url,
                'Scraped At': result.scraped_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Success': result.success,
                'Elements Found': result.metadata.get('elements_found', 0),
                'Actions Executed': result.metadata.get('actions_executed', 0)
            }])
            
            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            # Errors sheet (if any)
            if result.errors:
                errors_df = pd.DataFrame([{'Error': error} for error in result.errors])
                errors_df.to_excel(writer, sheet_name='Errors', index=False)

    def _flatten_data(self, data: Dict[str, Any]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Flatten nested data structures for tabular export.
        
        Args:
            data: Dictionary containing scraped data
            
        Returns:
            Flattened data suitable for CSV/Excel export
        """
        flattened = {}
        
        for key, value in data.items():
            if key == 'actions_executed':
                continue  # Skip actions for tabular export
                
            if isinstance(value, list):
                if len(value) == 1:
                    flattened[key] = value[0]
                elif len(value) > 1:
                    # For multiple values, create separate columns
                    for i, item in enumerate(value):
                        flattened[f"{key}_{i+1}"] = item
                else:
                    flattened[key] = ""
            elif isinstance(value, dict):
                # Flatten nested dictionaries
                for subkey, subvalue in value.items():
                    flattened[f"{key}_{subkey}"] = subvalue
            else:
                flattened[key] = value
        
        return flattened

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self._cleanup()
        except:
            pass


# Export both original and refactored versions for gradual migration
__all__ = ['ScraplingRunner']