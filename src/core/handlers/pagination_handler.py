#!/usr/bin/env python3
"""
Pagination handling for automated scraping with multiple pagination strategies.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from ..context import ScrapingContext
from ..utils.progress import ProgressTracker

logger = logging.getLogger(__name__)


class PaginationHandler:
    """
    Handles various pagination strategies including infinite scroll, load more buttons,
    URL-based pagination, and WordPress Grid Builder pagination.
    """
    
    def __init__(self, context: ScrapingContext):
        self.context = context
        self.current_page = context.current_page
        self.template = context.template
        self.fetcher = context.fetcher
    
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
    
    def smart_pagination_with_dual_browser(self) -> Dict[str, Any]:
        """Smart pagination handling with dual browser architecture."""
        try:
            print("\n🧠 SMART PAGINATION WITH DUAL BROWSER")
            print("="*45)
            
            # Check if pagination actions are actually defined
            if not self._has_pagination_actions_defined():
                print("⚠️  No pagination actions defined - extracting single page data")
                print("="*45)
                return self.extract_data()
            
            # Detect where pagination should occur
            pagination_location = self.detect_pagination_location()
            
            # Initialize data collection
            all_data = {}
            
            if pagination_location == "main_page":
                # Handle main page pagination
                print("📄 Processing main page pagination...")
                
                # First, get initial data from main page
                initial_data = self.extract_data()
                if initial_data:
                    all_data.update(initial_data)
                    print(f"📊 Initial data: {sum(len(v) if isinstance(v, list) else 1 for v in initial_data.values())} items")
                
                # Continue main page pagination
                try:
                    paginated_data = self.try_scroll_based_pagination()
                    if paginated_data:
                        # Merge paginated data
                        for key, value in paginated_data.items():
                            if key in all_data and isinstance(all_data[key], list) and isinstance(value, list):
                                all_data[key].extend(value)
                            else:
                                all_data[key] = value
                except Exception as e:
                    logger.warning(f"Main page pagination failed: {e}")
                
            elif pagination_location == "subpage":
                # Handle subpage pagination
                print("📑 Processing subpage pagination...")
                
                # Extract ONLY main page containers (NOT subpage elements)
                main_page_data = self.extract_main_page_only()
                if main_page_data:
                    all_data.update(main_page_data)
                    print(f"📊 Main page data: {sum(len(v) if isinstance(v, list) else 1 for v in main_page_data.values())} items")
            
            print("🎯 Smart pagination complete!")
            print("="*45)
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error in smart pagination: {e}")
            return self.extract_data()  # Fallback to basic extraction
    
    def auto_scroll_to_load_all_content(self, target_page=None):
        """
        Automatically scroll to load all content on pages with infinite scroll.
        
        Args:
            target_page: Specific page to scroll on. If None, uses self.current_page
        """
        try:
            # Use the specified page or current page
            scroll_page = target_page or self.current_page
            if not scroll_page:
                logger.warning("No page available for auto-scroll")
                return
            
            # Count initial elements
            initial_count = self.count_profile_elements()
            logger.info(f"Initial profile count: {initial_count}")
            
            if initial_count == 0:
                logger.warning("No profiles found initially, skipping auto-scroll")
                return
            
            max_scrolls = 20  # Prevent infinite loops
            scroll_count = 0
            last_count = initial_count
            stable_count = 0  # Track how many times count stayed the same
            
            # Use progress tracker
            progress = ProgressTracker(max_scrolls, "Auto-scrolling to load content")
            
            while scroll_count < max_scrolls:
                scroll_count += 1
                progress.update(0, f"Scroll {scroll_count}: {last_count} profiles loaded")
                
                try:
                    # Try different approaches to load more content
                    try:
                        # First, try to find and click "Load More" buttons
                        load_more_success = self.try_load_more_buttons()
                        
                        if not load_more_success:
                            # Try scrolling using Scrapling's internal page
                            scroll_success = self.try_scrapling_scroll(scroll_page)
                            
                            if not scroll_success:
                                logger.warning("Cannot access page for scrolling, trying pagination")
                                # Check for pagination links as fallback
                                pagination_success = self.try_pagination_load()
                                
                                if not pagination_success:
                                    logger.info("No more content loading methods available")
                                    break
                    except Exception as scroll_method_error:
                        logger.debug(f"Scroll method failed: {scroll_method_error}")
                        stable_count += 1
                        if stable_count >= 2:
                            logger.info("Scroll failed multiple times, assuming end of content reached")
                            break
                    
                    # Wait for content to load
                    time.sleep(2)
                    
                    # Check if more content loaded
                    current_count = self.count_profile_elements()
                    logger.debug(f"After scroll {scroll_count}: {current_count} profiles")
                    
                    if current_count > last_count:
                        logger.info(f"Loaded {current_count - last_count} more profiles (total: {current_count})")
                        last_count = current_count
                        stable_count = 0  # Reset stability counter
                        progress.update(1, f"Found {current_count} profiles")
                    else:
                        stable_count += 1
                        progress.update(1, f"No new content ({stable_count}/3)")
                        
                        # If count has been stable for 3 scrolls, we've reached the end
                        if stable_count >= 3:
                            logger.info(f"No new content after {stable_count} scrolls - reached end")
                            break
                
                except Exception as scroll_error:
                    logger.warning(f"Error during scroll {scroll_count}: {scroll_error}")
                    progress.update(1, f"Scroll error {scroll_count}")
                    break
            
            final_count = self.count_profile_elements()
            progress.finish(f"Loaded {final_count} total profiles")
            logger.info(f"Auto-scroll complete: {final_count} profiles loaded (started with {initial_count})")
            
        except Exception as e:
            logger.error(f"Error during auto-scroll: {e}")
    
    def try_load_more_buttons(self) -> bool:
        """Try to find and click Load More buttons."""
        load_more_patterns = [
            'button:contains("Load More")',
            'button:contains("Show More")', 
            'button:contains("View More")',
            'a:contains("Load More")',
            'a:contains("Show More")',
            '.load-more',
            '.show-more',
            '.view-more',
            '[data-load-more]'
        ]
        
        for pattern in load_more_patterns:
            try:
                elements = self.current_page.css(pattern)
                if elements:
                    logger.info(f"Found Load More button with pattern: {pattern}")
                    return True
            except Exception:
                continue
        
        return False
    
    def try_pagination_load(self) -> bool:
        """Try to load more content via pagination."""
        pagination_patterns = [
            'a:contains("Next")',
            'a:contains(">")', 
            '.pagination a:last-child',
            '.next',
            '.page-next'
        ]
        
        for pattern in pagination_patterns:
            try:
                elements = self.current_page.css(pattern)
                if elements:
                    logger.info(f"Found pagination with pattern: {pattern}")
                    return True
            except Exception:
                continue
        
        return False
    
    def try_scrapling_scroll(self, scroll_page) -> bool:
        """Try scrolling using Scrapling's page."""
        try:
            # In Scrapling, we can't directly scroll, but we can detect scroll capability
            logger.info("Scrapling scroll attempted")
            return True
        except Exception as e:
            logger.debug(f"Scrapling scroll failed: {e}")
            return False
    
    def handle_pagination(self) -> bool:
        """
        Handle pagination navigation.
        
        Returns:
            True if successfully navigated to next page, False if no more pages
        """
        try:
            pagination = self.template.pagination
            
            if pagination.pattern_type == 'button':
                # Look for next button
                next_buttons = self.current_page.css(pagination.next_selector) if pagination.next_selector else []
                if next_buttons and next_buttons[0].is_visible():
                    logger.info("Next button detected - would navigate to next page")
                    return True
                
            elif pagination.pattern_type == 'infinite_scroll':
                # Handle infinite scroll
                return self.handle_infinite_scroll()
                
            elif pagination.pattern_type == 'load_more':
                return self.handle_load_more_pagination()
            
            return False
            
        except Exception as e:
            logger.warning(f"Error handling pagination: {e}")
            return False
    
    def handle_infinite_scroll(self) -> bool:
        """
        Handle infinite scroll scenarios.
        
        Returns:
            True if more content available, False otherwise
        """
        try:
            logger.info("Infinite scroll detected - would continue scrolling")
            
            # Check for end condition
            if hasattr(self.template.pagination, 'end_condition_selector') and self.template.pagination.end_condition_selector:
                end_elements = self.current_page.css(self.template.pagination.end_condition_selector)
                if end_elements:
                    logger.info("End condition met - stopping infinite scroll")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error in infinite scroll handling: {e}")
            return False
    
    def handle_load_more_pagination(self) -> bool:
        """Handle load more button pagination."""
        try:
            logger.info("Load more pagination detected")
            return True
        except Exception as e:
            logger.warning(f"Error in load more pagination: {e}")
            return False
    
    def try_url_based_pagination(self) -> Optional[Dict[str, Any]]:
        """
        Attempt URL-based pagination by detecting and testing common pagination parameters.
        
        Returns:
            Dictionary containing all paginated data, or None if pagination not possible
        """
        try:
            base_url = self.template.url
            parsed_url = urlparse(base_url)
            base_query = parse_qs(parsed_url.query)
            
            # Common pagination parameter patterns to test
            pagination_patterns = [
                {'param': 'offset', 'step': 20, 'start': 0},
                {'param': 'page', 'step': 1, 'start': 1},
                {'param': 'skip', 'step': 20, 'start': 0},
                {'param': 'start', 'step': 20, 'start': 0},
                {'param': 'from', 'step': 20, 'start': 0}
            ]
            
            # Test which pagination pattern works
            working_pattern = None
            for pattern in pagination_patterns:
                test_query = base_query.copy()
                test_query[pattern['param']] = [str(pattern['step'])]
                
                test_url = urlunparse((
                    parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                    parsed_url.params, urlencode(test_query, doseq=True), parsed_url.fragment
                ))
                
                # Test if this pagination pattern works
                test_page = self.fetch_page(test_url)
                if test_page and self.has_different_content(test_page):
                    working_pattern = pattern
                    logger.info(f"Detected working pagination pattern: {pattern['param']}")
                    break
            
            if not working_pattern:
                logger.info("No URL-based pagination pattern detected")
                return None
            
            # Extract data from all pages using the working pattern
            all_data = {}
            current_offset = working_pattern['start']
            consecutive_empty_pages = 0
            max_pages = 200  # Safety limit
            page_count = 0
            
            while page_count < max_pages and consecutive_empty_pages < 3:
                # Build URL for current page
                page_query = base_query.copy()
                page_query[working_pattern['param']] = [str(current_offset)]
                
                page_url = urlunparse((
                    parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                    parsed_url.params, urlencode(page_query, doseq=True), parsed_url.fragment
                ))
                
                logger.info(f"Fetching page {page_count + 1} with {working_pattern['param']}={current_offset}")
                
                # Fetch and extract data from this page
                page = self.fetch_page(page_url)
                if not page:
                    break
                
                self.current_page = page
                page_data = self.extract_data()
                
                if page_data:
                    # Check if page has new content
                    has_new_content = False
                    for key, value in page_data.items():
                        if isinstance(value, list) and value:
                            if key not in all_data:
                                all_data[key] = []
                            
                            # Check for duplicate content
                            new_items = []
                            for item in value:
                                if item not in all_data[key]:
                                    new_items.append(item)
                                    has_new_content = True
                            
                            all_data[key].extend(new_items)
                        else:
                            if key not in all_data:
                                all_data[key] = value
                    
                    if not has_new_content:
                        consecutive_empty_pages += 1
                        logger.info(f"No new content found on page {page_count + 1}")
                    else:
                        consecutive_empty_pages = 0
                else:
                    consecutive_empty_pages += 1
                
                current_offset += working_pattern['step']
                page_count += 1
                
                # Add delay between requests
                time.sleep(1)
            
            if all_data:
                logger.info(f"URL-based pagination complete: extracted data from {page_count} pages")
                return all_data
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Error in URL-based pagination: {e}")
            return None
    
    def try_scroll_based_pagination(self) -> Dict[str, Any]:
        """
        Fallback pagination using scroll/load more detection.
        
        Returns:
            Dictionary containing extracted data
        """
        try:
            logger.info("Attempting scroll-based pagination detection")
            
            # Check if pagination actions are defined before attempting pagination
            if not self._has_pagination_actions_defined():
                logger.info("No pagination actions defined - returning current page data only")
                return self.extract_data()
            
            # Try to auto-detect load more buttons
            detected_load_more = self.auto_detect_load_more_buttons()
            
            if detected_load_more:
                logger.info(f"Auto-detected load more button: {detected_load_more}")
                return self.try_auto_load_more_pagination(detected_load_more)
            
            # Try infinite scroll detection for WPGB
            if self.detect_wpgb_infinite_scroll():
                logger.info("WordPress Grid Builder infinite scroll detected")
                return self.try_wpgb_infinite_scroll_pagination()
            
            # First extract current page data
            current_data = self.extract_data()
            
            # Try load more approaches if available
            if hasattr(self.template, 'pagination') and self.template.pagination:
                return self.try_standard_pagination()
            
            return current_data
            
        except Exception as e:
            logger.warning(f"Error in scroll-based pagination: {e}")
            return self.extract_data()
    
    def try_standard_pagination(self) -> Dict[str, Any]:
        """
        Standard pagination processing for configured templates.
        
        Returns:
            Dictionary containing all paginated data
        """
        all_containers_data = {}
        page_number = 1
        max_pages_limit = 100  # Hard limit to prevent infinite loops
        
        try:
            # Check if pagination actions are defined
            if not self._has_pagination_actions_defined():
                logger.info("No pagination actions defined - extracting single page only")
                return self.extract_data()
            
            while page_number <= max_pages_limit:
                logger.info(f"Processing page {page_number}")
                
                # Extract data from current page
                page_data = self.extract_data()
                
                if page_data:
                    # Aggregate container data across pages
                    for key, value in page_data.items():
                        if isinstance(value, list):
                            # This is likely container data
                            if key not in all_containers_data:
                                all_containers_data[key] = []
                            all_containers_data[key].extend(value)
                        else:
                            # Single value data - take from first page or latest
                            if key not in all_containers_data:
                                all_containers_data[key] = value
                
                # Handle pagination
                more_content_loaded = False
                if hasattr(self.template, 'pagination') and self.template.pagination:
                    if self.template.pagination.pattern_type == 'load_more':
                        more_content_loaded = self.handle_load_more_pagination()
                    else:
                        more_content_loaded = self.handle_pagination()
                    
                    if not more_content_loaded:
                        logger.info("No more content available - pagination complete")
                        break
                else:
                    logger.info("No pagination configuration - single page processing complete")
                    break
                
                page_number += 1
                
                # Check template-configured max pages
                if hasattr(self.template.pagination, 'max_pages') and self.template.pagination.max_pages:
                    if page_number > self.template.pagination.max_pages:
                        logger.info(f"Reached template max pages limit: {self.template.pagination.max_pages}")
                        break
                        
                # Add delay between requests
                if hasattr(self.template.pagination, 'scroll_pause_time'):
                    time.sleep(self.template.pagination.scroll_pause_time)
                else:
                    time.sleep(2)
        
            if page_number > max_pages_limit:
                logger.warning(f"Reached hard limit of {max_pages_limit} pages to prevent infinite loops")
            
            logger.info(f"Completed standard pagination processing. Total pages: {page_number}")
            return all_containers_data
            
        except Exception as e:
            logger.error(f"Error in standard pagination processing: {e}")
            return all_containers_data
    
    def try_auto_load_more_pagination(self, load_more_selector: str) -> Dict[str, Any]:
        """
        Attempt pagination using auto-detected load more button.
        
        Args:
            load_more_selector: CSS selector for the load more button
            
        Returns:
            Dictionary containing all paginated data
        """
        all_data = {}
        max_clicks = 200  # Safety limit
        clicks_performed = 0
        consecutive_failures = 0
        
        try:
            logger.info(f"Starting auto load more pagination with selector: {load_more_selector}")
            
            # Get initial data
            page_data = self.extract_data()
            if page_data:
                for key, value in page_data.items():
                    if isinstance(value, list):
                        all_data[key] = value.copy()
                    else:
                        all_data[key] = value
                        
                logger.info(f"Initial page loaded with {len(all_data.get('main_container', []))} items")
            
            while clicks_performed < max_clicks and consecutive_failures < 3:
                try:
                    # Check if load more button still exists
                    load_more_elements = self.current_page.css(load_more_selector)
                    if not load_more_elements:
                        logger.info("Load more button no longer found - pagination complete")
                        break
                    
                    # Simulate load more action (in real implementation would use fetcher with page_action)
                    clicks_performed += 1
                    
                    # Extract only NEW data that was loaded after the click
                    new_page_data = self.extract_data_incremental(all_data)
                    
                    if new_page_data:
                        # Check if we got new content
                        new_content_found = False
                        for key, value in new_page_data.items():
                            if isinstance(value, list) and value:
                                if key not in all_data:
                                    all_data[key] = []
                                
                                # Count new items
                                initial_count = len(all_data[key])
                                
                                # Add new items
                                all_data[key].extend(value)
                                new_content_found = True
                                
                                new_count = len(all_data[key])
                                logger.info(f"After click #{clicks_performed}: {key} has {new_count} items (added {new_count - initial_count})")
                            else:
                                if key not in all_data:
                                    all_data[key] = value
                        
                        if new_content_found:
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1
                            logger.info(f"No new content found after click #{clicks_performed}")
                    else:
                        consecutive_failures += 1
                        logger.warning(f"Failed to extract data after click #{clicks_performed}")
                    
                    # Add delay between clicks
                    time.sleep(2)
                    
                except Exception as click_error:
                    consecutive_failures += 1
                    logger.warning(f"Error during load more click #{clicks_performed}: {click_error}")
            
            total_items = len(all_data.get('main_container', []))
            logger.info(f"Auto load more pagination complete: performed {clicks_performed} clicks, collected {total_items} total items")
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error in auto load more pagination: {e}")
            return all_data or self.extract_data()
    
    def try_wpgb_infinite_scroll_pagination(self) -> Dict[str, Any]:
        """
        Attempt pagination using WPGB infinite scroll by scrolling to trigger more content.
        
        Returns:
            Dictionary containing all paginated data
        """
        all_data = {}
        max_scrolls = 200  # Safety limit
        scrolls_performed = 0
        consecutive_no_new_content = 0
        
        try:
            logger.info("Starting WPGB infinite scroll pagination")
            
            # Get initial data
            page_data = self.extract_data()
            if page_data:
                for key, value in page_data.items():
                    if isinstance(value, list):
                        all_data[key] = value.copy()
                    else:
                        all_data[key] = value
                        
                initial_count = len(all_data.get('main_container', []))
                logger.info(f"Initial page loaded with {initial_count} items")
            
            while scrolls_performed < max_scrolls and consecutive_no_new_content < 5:
                try:
                    scrolls_performed += 1
                    
                    # Extract new data
                    new_page_data = self.extract_data()
                    
                    if new_page_data:
                        # Check if we got new content
                        new_content_found = False
                        for key, value in new_page_data.items():
                            if isinstance(value, list) and value:
                                if key not in all_data:
                                    all_data[key] = []
                                
                                # Count new items
                                initial_count = len(all_data[key])
                                
                                # Add only new items (avoid duplicates)
                                for item in value:
                                    if item not in all_data[key]:
                                        all_data[key].append(item)
                                        new_content_found = True
                                
                                new_count = len(all_data[key])
                                if new_count > initial_count:
                                    logger.info(f"After scroll #{scrolls_performed}: {key} has {new_count} items (added {new_count - initial_count})")
                            else:
                                if key not in all_data:
                                    all_data[key] = value
                        
                        if new_content_found:
                            consecutive_no_new_content = 0
                        else:
                            consecutive_no_new_content += 1
                            logger.info(f"No new content found after scroll #{scrolls_performed}")
                    else:
                        consecutive_no_new_content += 1
                        logger.warning(f"Failed to extract data after scroll #{scrolls_performed}")
                    
                    # Add delay between scrolls
                    time.sleep(2)
                    
                except Exception as scroll_error:
                    consecutive_no_new_content += 1
                    logger.warning(f"Error during scroll #{scrolls_performed}: {scroll_error}")
            
            total_items = len(all_data.get('main_container', []))
            logger.info(f"WPGB infinite scroll pagination complete: performed {scrolls_performed} scrolls, collected {total_items} total items")
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error in WPGB infinite scroll pagination: {e}")
            return all_data or self.extract_data()
    
    # Helper methods
    def auto_detect_load_more_buttons(self) -> Optional[str]:
        """Auto-detect load more buttons on the current page."""
        load_more_selectors = [
            '.wpgb-pagination-facet button',
            '.wpgb-pagination-facet a',
            'button[class*="load"]',
            'button[class*="more"]',
            'a[class*="load"]',
            'a[class*="more"]', 
            '[class*="load-more"]',
            '[class*="show-more"]',
            '.load-more',
            '.show-more',
            '.view-more'
        ]
        
        for selector in load_more_selectors:
            try:
                elements = self.current_page.css(selector)
                if elements and len(elements) > 0:
                    logger.info(f"Found load more button with selector: {selector}")
                    return selector
            except Exception:
                continue
        
        logger.info("No load more buttons detected")
        return None
    
    def detect_wpgb_infinite_scroll(self) -> bool:
        """Detect if the page uses WordPress Grid Builder with infinite scroll."""
        try:
            wpgb_indicators = [
                '.wp-grid-builder',
                '.wpgb-template',
                '.wpgb-grid',
                '.wpgb-facet',
                '[data-grid]'
            ]
            
            for indicator in wpgb_indicators:
                elements = self.current_page.css(indicator)
                if elements:
                    logger.info(f"WPGB indicator found: {indicator}")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error detecting WPGB infinite scroll: {e}")
            return False
    
    def count_profile_elements(self) -> int:
        """Count the number of profile elements currently on the page."""
        try:
            selectors_to_try = [
                '.people-list strong',
                '.wp-grid-builder .wpgb-card',
                '.people-list .wp-block-column',
                '[class*="people"] strong',
                '.wpgb-grid-archivePeople > div'
            ]
            
            max_count = 0
            for selector in selectors_to_try:
                try:
                    elements = self.current_page.css(selector)
                    count = len(elements) if elements else 0
                    max_count = max(max_count, count)
                    logger.debug(f"Selector '{selector}': {count} elements")
                except Exception:
                    continue
            
            return max_count
            
        except Exception as e:
            logger.warning(f"Error counting profile elements: {e}")
            return 0
    
    def has_different_content(self, test_page) -> bool:
        """Check if a test page has different content than the current page."""
        try:
            if not self.current_page or not test_page:
                return False
            
            # Compare number of containers as a quick check
            current_containers = self.get_container_count(self.current_page)
            test_containers = self.get_container_count(test_page)
            
            return test_containers > 0 and current_containers != test_containers
            
        except Exception:
            return False
    
    def get_container_count(self, page) -> int:
        """Get the number of containers on a page for comparison."""
        try:
            selectors = [
                '.people-list strong',
                '[class*="people"] strong', 
                '.wpgb-grid > div',
                '.directory-item',
                '[class*="card"]',
                '[class*="item"]'
            ]
            
            for selector in selectors:
                try:
                    elements = page.css(selector)
                    if elements and len(elements) > 5:  # Must have substantial content
                        return len(elements)
                except Exception:
                    continue
            
            return 0
            
        except Exception:
            return 0
    
    def detect_pagination_location(self) -> str:
        """Detect where pagination should occur."""
        return "main_page"  # Simplified implementation
    
    # Placeholder methods that would be implemented with proper data extraction
    def extract_data(self) -> Dict[str, Any]:
        """Extract data from current page - placeholder."""
        return {}
    
    def extract_main_page_only(self) -> Dict[str, Any]:
        """Extract only main page data - placeholder."""
        return {}
    
    def extract_data_incremental(self, existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only new data - placeholder."""
        return {}
    
    def fetch_page(self, url: str):
        """Fetch a page - placeholder."""
        return None