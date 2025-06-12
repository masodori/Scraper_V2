#!/usr/bin/env python3
"""
Scrapling Integration Module

This module handles the automated scraping execution using templates
generated from interactive sessions. It integrates with Scrapling's
powerful scraping capabilities while maintaining separation from
the interactive layer.
"""

import logging
import time
import json
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapling.fetchers import PlayWrightFetcher, StealthyFetcher
from scrapling import Adaptor
from colorama import Fore

from ..models.scraping_template import ScrapingTemplate, ScrapingResult, ElementSelector, NavigationAction, CookieData

logger = logging.getLogger(__name__)


class ScraplingRunner:
    """
    Executes automated scraping using Scrapling based on interactive templates.
    
    This class provides a clean separation between the interactive template
    creation and the automated scraping execution, allowing templates to be
    run in headless server environments.
    """
    
    def __init__(self, template: ScrapingTemplate):
        """
        Initialize the Scrapling runner with a template.
        
        Args:
            template: The scraping template to execute
        """
        self.template = template
        self.fetcher = None
        self.current_page = None
        
        # Setup logging for this session
        self.session_logger = logging.getLogger(f"scrapling_runner.{template.name}")
        
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
            if self._looks_like_directory_template() and '/lawyer/' in target_url:
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
            
            # Handle pagination FIRST to collect all containers across pages
            if hasattr(self.template, 'pagination') and self.template.pagination:
                logger.info("Pagination detected - processing all pages/content")
                scraped_data = self._handle_filters_and_pagination()
            else:
                # Single page extraction only
                logger.info("No pagination - extracting current page only")
                scraped_data = self._extract_data()
            
            # Execute any actions if specified (ONLY for non-navigation actions)
            if self.template.actions:
                # Check if this is a directory template with container workflow
                is_directory_workflow = self._looks_like_directory_template()
                
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
                    original_actions = self.template.actions
                    self.template.actions = non_navigation_actions
                    action_results = self._execute_actions()
                    self.template.actions = original_actions
                    scraped_data['actions_executed'] = action_results
                else:
                    logger.info("Skipping all actions - navigation actions or generic selectors detected")
            
            # Process subpage data if any elements have follow_links enabled
            scraped_data = self._process_subpage_extractions(scraped_data)
            
            # Process containers with follow_links for subpage navigation
            scraped_data = self._process_container_subpages(scraped_data)
            
            # Check if we should use dual-engine mode for sublinks
            if self._should_use_dual_engine_mode():
                scraped_data = self._process_dual_engine_sublinks(scraped_data)
            else:
                # Fallback to original intelligent sublink processing
                scraped_data = self._process_intelligent_sublinks(scraped_data)
            
            # Merge directory and subpage data into unified format
            scraped_data = self._merge_directory_with_subpage_data(scraped_data)
            
            result.data = scraped_data
            result.success = True
            result.metadata = {
                'elements_found': len([k for k in scraped_data.keys() if k != 'actions_executed']),
                'actions_executed': len(self.template.actions),
                'page_title': self._get_page_title(),
                'final_url': self.current_page.url if self.current_page else self.template.url
            }
            
            logger.info(f"Scraping completed successfully. Found {result.metadata['elements_found']} elements.")
            # Only show major progress in console
            print(f"{Fore.GREEN}▶ Extracted data from {result.metadata['elements_found']} element(s)")
            
        except Exception as e:
            error_msg = f"Scraping failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.success = False
            
        finally:
            self._cleanup()
        
        return result
    
    def _looks_like_directory_template(self) -> bool:
        """
        Determine if template appears to be designed for directory/listing pages.
        Enhanced detection for lawyer directory patterns.
        
        Returns:
            True if template has directory-like characteristics
        """
        directory_indicators = [
            # Container-based extraction suggests multiple items
            any(hasattr(elem, 'is_container') and elem.is_container for elem in self.template.elements),
            # Multiple elements suggests listing
            any(elem.is_multiple for elem in self.template.elements),
            # Directory-like selectors
            any('people' in elem.selector.lower() or 'list' in elem.selector.lower() 
                or 'grid' in elem.selector.lower() for elem in self.template.elements),
            # Profile link extraction suggests directory
            any(hasattr(elem, 'sub_elements') and elem.sub_elements and 
                any('link' in sub.get('label', '').lower() or 'profile' in sub.get('label', '').lower() 
                    or 'email' in sub.get('label', '').lower()
                    for sub in elem.sub_elements if isinstance(sub, dict))
                for elem in self.template.elements if hasattr(elem, 'sub_elements')),
            # Actions that navigate to profiles
            any('link' in action.label.lower() and '/lawyer/' in getattr(action, 'target_url', '')
                for action in self.template.actions if hasattr(self.template, 'actions')),
            # Profile-like sub-element patterns (name, title, email combinations suggest directory)
            any(hasattr(elem, 'sub_elements') and elem.sub_elements and
                len([sub for sub in elem.sub_elements if isinstance(sub, dict) and 
                     any(keyword in sub.get('label', '').lower() 
                         for keyword in ['name', 'title', 'position', 'email', 'phone'])]) >= 2
                for elem in self.template.elements if hasattr(elem, 'sub_elements'))
        ]
        
        return any(directory_indicators)
    
    def _find_directory_containers(self, element_config: ElementSelector) -> List:
        """
        Smart detection of lawyer profile containers on directory pages.
        
        Args:
            element_config: ElementSelector configuration
            
        Returns:
            List of container elements representing lawyer profiles
        """
        # Try Gibson Dunn specific patterns first
        directory_patterns = [
            ".people.loading",  # Gibson Dunn specific
            ".people-card", 
            ".lawyer-card",
            ".attorney-card",
            ".profile-card",
            "[class*='people']",
            "[class*='lawyer']",
            "[class*='attorney']",
            "[class*='profile']",
            ".directory-item",
            ".staff-member"
        ]
        
        for pattern in directory_patterns:
            try:
                elements = self.current_page.css(pattern, auto_match=True)
                if elements and len(elements) >= 3:  # Need at least 3 for a directory
                    logger.info(f"Found {len(elements)} directory containers with pattern: {pattern}")
                    return elements
            except Exception:
                continue
        
        # Try content-based detection
        content_patterns = [
            "//*[contains(@class, 'card') and contains(., 'Partner')]",
            "//*[contains(@class, 'item') and .//a[contains(@href, '/lawyer/')]]",
            "//*[contains(., '@') and contains(., 'Partner')]//ancestor::*[2]",
            "//*[contains(., 'J.D.') or contains(., 'University')]//ancestor::*[position()<=3 and @class]"
        ]
        
        for pattern in content_patterns:
            try:
                elements = self.current_page.xpath(pattern)
                if elements and len(elements) >= 3:
                    logger.info(f"Found {len(elements)} directory containers with content pattern: {pattern}")
                    return elements
            except Exception:
                continue
        
        return []
    
    def _template_needs_subpage_data(self) -> bool:
        """
        Check if template has elements that require subpage navigation.
        
        Returns:
            True if template has subpage elements or education/credentials elements
        """
        # Check for elements that are typically found on individual profile pages
        subpage_indicators = [
            # Elements with subpage_elements defined
            any(hasattr(elem, 'subpage_elements') and elem.subpage_elements 
                for elem in self.template.elements),
            # Education/credentials elements (typically on individual pages)
            any(hasattr(elem, 'sub_elements') and elem.sub_elements and
                any('education' in sub.get('label', '').lower() or 'cred' in sub.get('label', '').lower()
                    for sub in elem.sub_elements if isinstance(sub, dict))
                for elem in self.template.elements if hasattr(elem, 'sub_elements')),
            # Multiple containers with different purposes (main + subpage data)
            len([elem for elem in self.template.elements if hasattr(elem, 'is_container') and elem.is_container]) >= 2,
            # Actions that navigate to specific pages
            any('link' in action.label.lower() and '/lawyer/' in getattr(action, 'target_url', '')
                for action in self.template.actions if hasattr(self.template, 'actions'))
        ]
        
        return any(subpage_indicators)
    
    def _is_subpage_container(self, element_config: ElementSelector) -> bool:
        """
        Check if a container is meant to extract data from individual subpages.
        
        Args:
            element_config: ElementSelector configuration
            
        Returns:
            True if container should extract data from subpages
        """
        # Primary indicator: follow_links must be explicitly enabled
        follow_links_enabled = getattr(element_config, 'follow_links', False)
        
        # If follow_links is False, this is NOT a subpage container
        if not follow_links_enabled:
            logger.debug(f"Container '{element_config.label}' has follow_links=False, treating as same-page container")
            return False
        
        # If follow_links is True, check for additional indicators to confirm
        subpage_indicators = [
            # Container label suggests subpage data
            any(keyword in element_config.label.lower() 
                for keyword in ['subpage', 'sublink', 'subcon', 'education', 'credential', 'experience', 'bio', 'profile']),
            # Sub-elements that are typically on individual pages
            hasattr(element_config, 'sub_elements') and element_config.sub_elements and
            any(keyword in sub.get('label', '').lower() if isinstance(sub, dict) else getattr(sub, 'label', '').lower()
                for keyword in ['education', 'credential', 'admission', 'bar', 'experience', 'bio', 'creds']
                for sub in element_config.sub_elements),
            # Follow links is enabled (already checked above)
            True
        ]
        
        is_subpage = any(subpage_indicators)
        logger.debug(f"Subpage container check for '{element_config.label}': {is_subpage} (follow_links={follow_links_enabled}, indicators: {subpage_indicators})")
        return is_subpage
    
    def _extract_subpage_container_data(self, profile_url: str, element_config: ElementSelector) -> Dict[str, Any]:
        """
        Extract container data from an individual profile subpage.
        
        Args:
            profile_url: URL of the profile page
            element_config: Container configuration for subpage extraction
            
        Returns:
            Dictionary containing extracted subpage container data
        """
        subpage_data = {}
        original_page = self.current_page
        
        try:
            logger.debug(f"Navigating to subpage for container data: {profile_url}")
            
            # Navigate to the profile page
            subpage = self._fetch_page(profile_url)
            if not subpage:
                logger.warning(f"Failed to fetch subpage: {profile_url}")
                return {}
            
            # Temporarily switch to subpage context
            self.current_page = subpage
            
            # Extract sub-elements from the subpage
            if hasattr(element_config, 'sub_elements') and element_config.sub_elements:
                for sub_element in element_config.sub_elements:
                    try:
                        if isinstance(sub_element, dict):
                            sub_label = sub_element.get('label')
                            sub_selector = sub_element.get('selector')
                            sub_type = sub_element.get('element_type', 'text')
                        else:
                            sub_label = sub_element.label
                            sub_selector = sub_element.selector
                            sub_type = sub_element.element_type
                        
                        # Enhance selector for subpage context
                        # Convert SubElement object to dict format for _map_generic_selector
                        sub_element_dict = {
                            'label': sub_label,
                            'selector': sub_selector,
                            'element_type': sub_type
                        } if not isinstance(sub_element, dict) else sub_element
                        
                        enhanced_selector = self._map_generic_selector(sub_element_dict, "profile")
                        if enhanced_selector != sub_selector:
                            logger.info(f"Enhanced subpage selector for {sub_label}: '{sub_selector}' → '{enhanced_selector}'")
                            sub_selector = enhanced_selector
                        
                        # Find elements on the subpage
                        elements = []
                        selectors_to_try = [s.strip() for s in sub_selector.split(',') if s.strip()]
                        
                        for selector_attempt in selectors_to_try:
                            try:
                                if selector_attempt.startswith('xpath:'):
                                    xpath_expr = selector_attempt[6:]
                                    elements = self.current_page.xpath(xpath_expr)
                                else:
                                    elements = self.current_page.css(selector_attempt)
                                
                                if elements:
                                    logger.debug(f"Found {len(elements)} subpage elements with selector: {selector_attempt}")
                                    break
                            except Exception:
                                continue
                        
                        # Extract data based on element type
                        if elements:
                            if sub_type == 'text' and len(elements) > 1:
                                # Multiple text elements - extract as list
                                text_values = []
                                for elem in elements:
                                    text_content = elem.text if hasattr(elem, 'text') else str(elem)
                                    if text_content and text_content.strip():
                                        text_values.append(text_content.strip())
                                subpage_data[sub_label] = text_values
                            elif elements:
                                # Single element or first element
                                text_content = elements[0].text if hasattr(elements[0], 'text') else str(elements[0])
                                subpage_data[sub_label] = text_content.strip() if text_content else ''
                        else:
                            logger.debug(f"No elements found for subpage {sub_label} with selector {sub_selector}")
                            subpage_data[sub_label] = None
                            
                    except Exception as e:
                        logger.warning(f"Error extracting subpage element {sub_label}: {e}")
                        subpage_data[sub_label] = None
            
            logger.info(f"Successfully extracted {len(subpage_data)} elements from subpage")
            
        except Exception as e:
            logger.error(f"Error during subpage container extraction: {e}")
        
        finally:
            # Restore original page context
            if original_page:
                self.current_page = original_page
        
        return subpage_data
    
    def _extract_subpage_container_data_from_main_containers(self, element_config: ElementSelector) -> List[Dict[str, Any]]:
        """
        Extract subpage container data by using profile links from main containers.
        This handles templates where subpage containers need to extract data from individual lawyer pages.
        
        Args:
            element_config: Subpage container configuration
            
        Returns:
            List of dictionaries containing extracted subpage data
        """
        containers = []
        
        try:
            logger.info(f"Subpage container '{element_config.label}' detected - extracting from individual lawyer pages")
            
            # Find main containers that should have profile links
            main_container_elements = []
            
            # Try to find directory containers using smart detection
            if self._looks_like_directory_template():
                # Use the same directory container detection as main containers
                main_container_elements = self._find_directory_containers(element_config)
                if main_container_elements:
                    logger.info(f"Found {len(main_container_elements)} main containers for subpage extraction")
            
            if not main_container_elements:
                logger.warning("No main containers found for subpage extraction")
                return []
            
            # Process each main container to extract profile links and then subpage data
            for i, container in enumerate(main_container_elements):
                try:
                    # Find profile link in this container
                    profile_link = None
                    
                    # Try to find any link within the container that points to a lawyer page
                    lawyer_links = container.css("a[href*='/lawyer/']")
                    if not lawyer_links:
                        lawyer_links = container.css("a")  # Fallback to any link
                    
                    for link in lawyer_links:
                        href = ''
                        if hasattr(link, 'get_attribute'):
                            href = link.get_attribute('href') or ''
                        elif hasattr(link, 'attrib'):
                            href = link.attrib.get('href', '')
                        
                        if href and ('/lawyer/' in href or href.startswith('/')):
                            full_url = self.current_page.urljoin(href) if href else ''
                            if full_url and '/lawyer/' in full_url:
                                profile_link = full_url
                                logger.debug(f"Found profile link for subpage container {i}: {full_url}")
                                break
                    
                    if not profile_link:
                        logger.warning(f"No profile link found for subpage container {i}")
                        containers.append({'_container_index': i, '_error': 'No profile link found'})
                        continue
                    
                    # Extract subpage data from the individual lawyer page
                    logger.info(f"Extracting subpage data from: {profile_link}")
                    subpage_data = self._extract_subpage_container_data(profile_link, element_config)
                    
                    if subpage_data:
                        subpage_data['_profile_link'] = profile_link
                        subpage_data['_container_index'] = i
                        containers.append(subpage_data)
                        logger.debug(f"Successfully extracted subpage data for container {i}: {list(subpage_data.keys())}")
                    else:
                        logger.warning(f"No subpage data extracted for container {i}")
                        containers.append({'_container_index': i, '_profile_link': profile_link, '_error': 'No data extracted'})
                
                except Exception as container_error:
                    logger.warning(f"Error processing subpage container {i}: {container_error}")
                    containers.append({'_container_index': i, '_error': str(container_error)})
            
            logger.info(f"Successfully processed {len(containers)} subpage containers")
            return containers
            
        except Exception as e:
            logger.error(f"Error extracting subpage container data from main containers: {e}")
            return []
    
    def _map_generic_selector(self, sub_element: dict, context: str = "directory") -> str:
        """
        Map generic selectors to meaningful ones based on label and context.
        
        Args:
            sub_element: Sub-element configuration dict
            context: Context type ("directory" or "profile")
            
        Returns:
            Enhanced selector string
        """
        label = sub_element.get('label', '').lower()
        original_selector = sub_element.get('selector', '')
        
        # Always preserve XPath selectors - they are position-specific and already optimized
        if original_selector.startswith('xpath:'):
            return original_selector
        
        # If selector is already specific, keep it
        if len(original_selector) > 10 and ('.' in original_selector or '#' in original_selector or '[' in original_selector):
            return original_selector
        
        # Map generic selectors based on label
        if 'name' in label:
            if context == "directory":
                return "p.name strong, h3, h2, .name, [class*='name'] strong, strong:first-of-type"
            else:
                return "h1, h2, .entry-title, .page-title, .lawyer-name, .attorney-name"
                
        elif any(keyword in label for keyword in ['title', 'position', 'job']):
            if context == "directory":
                return "p.title span, .title, .position, .job-title, [class*='title'], [class*='position']"
            else:
                return ".position, .title, .job-title, h2 + p, h1 + p"
                
        elif any(keyword in label for keyword in ['email', 'mail']):
            return "a[href^='mailto:'], p.contact-details a[href^='mailto:'], .email, [class*='email'], a[href*='@']"
            
        elif 'phone' in label:
            return "a[href^='tel:'], .phone, [class*='phone'], a[href*='tel']"
            
        elif any(keyword in label for keyword in ['sector', 'practice', 'area']):
            if context == "directory":
                return "p.contact-details span, .practice-area, .sector, [class*='practice'], [class*='sector'], p.title span:nth-child(2)"
            else:
                return ".practice-area, .capabilities, .focus-areas, a[href*='/practice/']"
                
        elif any(keyword in label for keyword in ['link', 'profile', 'url']) or 'email' in label:
            if 'email' in label:
                return "a[href^='mailto:'], .email, [class*='email'], a[href*='@']"
            else:
                return "a[href*='/lawyer/'], a[href*='/attorney/'], a[href*='/people/'], a[href*='/team/'], a"
            
        elif 'education' in label:
            return ".education li, .is-style-no-bullets li, ul[class*='education'] li, .credentials li"
            
        elif any(keyword in label for keyword in ['cred', 'admission', 'bar']):
            return ".admissions li, .bar li, .credentials li, .is-style-no-bullets li"
        
        # Default fallback - return original
        return original_selector
    
    def _initialize_fetcher(self) -> None:
        """Initialize the appropriate Scrapling fetcher based on template settings."""
        try:
            # Initialize PlayWrightFetcher with auto_match enabled
            self.fetcher = PlayWrightFetcher
            # Enable auto_match globally for this fetcher instance
            if hasattr(PlayWrightFetcher, 'auto_match'):
                PlayWrightFetcher.auto_match = True
            logger.info("Initialized PlayWrightFetcher for scraping with AutoMatch enabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize fetcher: {e}")
            raise
    
    def _fetch_page(self, url: str) -> Optional[Adaptor]:
        """
        Fetch a page using the configured fetcher.
        
        Args:
            url: URL to fetch
            
        Returns:
            Adaptor instance for the fetched page or None if failed
        """
        try:
            logger.info(f"Fetching page: {url}")
            
            # Configure fetcher options
            fetch_options = {
                'headless': self.template.headless,
                'network_idle': True,
                'timeout': self.template.wait_timeout * 1000  # Convert to milliseconds
            }
            
            # Fetch the page
            page = self.fetcher.fetch(url, **fetch_options)
            
            if page and page.status == 200:
                logger.info(f"Successfully fetched page. Status: {page.status}")
                return page
            else:
                logger.error(f"Page fetch failed. Status: {page.status if page else 'None'}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None
    
    def _format_cookies_for_scrapling(self) -> List[Dict[str, Any]]:
        """Format cookies from template for Scrapling."""
        cookies = []
        for cookie in self.template.cookies:
            cookie_dict = {
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path
            }
            if hasattr(cookie, 'secure'):
                cookie_dict['secure'] = cookie.secure
            if hasattr(cookie, 'httpOnly'):
                cookie_dict['httpOnly'] = cookie.httpOnly
            
            cookies.append(cookie_dict)
        
        return cookies
    
    def _extract_data(self) -> Dict[str, Any]:
        """
        Extract data from the page using template selectors.
        
        Returns:
            Dictionary containing extracted data
        """
        extracted_data = {}
        
        for element in self.template.elements:
            try:
                logger.debug(f"Extracting data for element: {element.label}")
                
                value = self._extract_element_data(element)
                extracted_data[element.label] = value
                
                logger.debug(f"Successfully extracted {element.label}: {str(value)[:100]}...")
                
            except Exception as e:
                error_msg = f"Failed to extract {element.label}: {str(e)}"
                logger.warning(error_msg)
                
                if element.is_required:
                    raise Exception(error_msg)
                else:
                    extracted_data[element.label] = None
        
        return extracted_data
    
    def _extract_element_data(self, element: ElementSelector) -> Any:
        """
        Extract data from a single element using multiple fallback strategies.
        
        Args:
            element: ElementSelector defining what to extract
            
        Returns:
            Extracted data (string, list, or None)
        """
        if not self.current_page:
            raise Exception("No page available for data extraction")
        
        try:
            # Handle container elements specially
            if hasattr(element, 'is_container') and element.is_container:
                return self._extract_container_data(element)
            
            # Try multiple selection strategies in order of reliability
            found_elements = self._find_elements_with_fallback(element)
            
            if not found_elements:
                if element.is_required:
                    raise Exception(f"Required element not found: {element.selector}")
                return None
            
            # Handle multiple elements
            if element.is_multiple:
                return self._extract_multiple_elements(found_elements, element)
            else:
                return self._extract_single_element(found_elements[0], element)
                
        except Exception as e:
            logger.error(f"Error extracting element {element.label}: {e}")
            raise
    
    def _find_elements_with_fallback(self, element: ElementSelector) -> List:
        """
        Find elements using multiple strategies for maximum reliability.
        
        Args:
            element: ElementSelector configuration
            
        Returns:
            List of found elements
        """
        strategies = [
            # Strategy 1: AutoMatch with original selector
            lambda: self._try_automatch_selector(element),
            # Strategy 2: Semantic XPath generation
            lambda: self._try_semantic_xpath(element),
            # Strategy 3: Content-based selection
            lambda: self._try_content_based_selection(element),
            # Strategy 4: Structure-based selection
            lambda: self._try_structure_based_selection(element),
            # Strategy 5: Original selector as fallback
            lambda: self._try_original_selector(element),
            # Strategy 6: Fuzzy matching with variations
            lambda: self._try_fuzzy_matching(element)
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                elements = strategy()
                if elements:
                    logger.debug(f"Found elements using strategy {i+1} for {element.label}")
                    return elements
            except Exception as e:
                logger.debug(f"Strategy {i+1} failed for {element.label}: {e}")
                continue
        
        return []
    
    def _try_automatch_selector(self, element: ElementSelector) -> List:
        """Try AutoMatch with the original selector."""
        if element.selector_type == 'css':
            return self.current_page.css(element.selector, auto_match=True)
        elif element.selector_type == 'xpath':
            return self.current_page.xpath(element.selector, auto_match=True)
        return []
    
    def _try_semantic_xpath(self, element: ElementSelector) -> List:
        """Generate semantic XPath based on element context."""
        # Generate XPaths based on common patterns
        semantic_xpaths = self._generate_semantic_xpaths(element)
        
        for xpath in semantic_xpaths:
            try:
                elements = self.current_page.xpath(xpath, auto_match=True)
                if elements:
                    return elements
            except Exception:
                continue
        return []
    
    def _try_content_based_selection(self, element: ElementSelector) -> List:
        """Try to find elements based on content patterns with intelligent matching."""
        import re
        
        try:
            # Enhanced pattern matching based on element label
            label = element.label.lower()
            
            # Credential/Bar admission patterns
            if any(keyword in label for keyword in ['cred', 'admission', 'bar', 'license']):
                return self._find_credentials_intelligently()
            
            # Education patterns
            elif 'education' in label:
                return self._find_education_intelligently()
                
            # Position/Title patterns
            elif any(keyword in label for keyword in ['position', 'title', 'role']):
                return self._find_position_intelligently()
                
            # Contact patterns
            elif any(keyword in label for keyword in ['email', 'phone', 'contact']):
                return self._find_contact_intelligently(label)
                
            # Generic text pattern matching
            else:
                return self._find_generic_text_patterns(element)
                
        except Exception as e:
            logger.debug(f"Content-based selection failed: {e}")
            return []
    
    def _find_credentials_intelligently(self) -> List:
        """Find credential/bar admission information using multiple intelligent strategies."""
        strategies = [
            # Strategy 1: Look for common bar patterns
            lambda: self.current_page.xpath("//*[contains(text(), 'Bar') or contains(text(), 'bar')]"),
            # Strategy 2: Look for state/country - credential patterns  
            lambda: self.current_page.xpath("//*[contains(text(), ' - ') and (contains(text(), 'Bar') or contains(text(), 'Court') or contains(text(), 'License'))]"),
            # Strategy 3: Look in credential/admission sections
            lambda: self.current_page.css(".admissions *, .credentials *, .bar *, .license *"),
            # Strategy 4: Look for list items with credential patterns
            lambda: self.current_page.xpath("//li[contains(text(), 'Bar') or contains(text(), 'Court') or contains(text(), 'License') or contains(text(), 'Admission')]"),
            # Strategy 5: Pattern matching for common formats
            lambda: self._find_by_credential_patterns(),
            # Strategy 6: Look in common structural locations
            lambda: self.current_page.css(".bio *, .profile *, .details *").filter(lambda x: self._contains_credential_keywords(x))
        ]
        
        for strategy in strategies:
            try:
                elements = strategy()
                if elements:
                    # Filter to most relevant credential elements
                    filtered = self._filter_credential_elements(elements)
                    if filtered:
                        logger.debug(f"Found {len(filtered)} credential elements")
                        return filtered
            except Exception as e:
                logger.debug(f"Credential strategy failed: {e}")
                continue
        
        return []
    
    def _find_by_credential_patterns(self) -> List:
        """Find credentials using regex patterns for common formats."""
        import re
        
        # Common credential patterns
        patterns = [
            r'\w+\s*-\s*\w*Bar\w*',  # "State - Bar", "Country - Bar Association"
            r'\w+\s*Bar\s*\w*',      # "State Bar", "Bar Association"
            r'\w+\s*Court\s*\w*',    # "Supreme Court", "High Court"
            r'\w+\s*License\w*',     # "State License", "Professional License"
            r'\w+\s*Admission\w*'    # "Bar Admission", "Court Admission"
        ]
        
        found_elements = []
        
        try:
            # Get all text elements on page
            all_text_elements = self.current_page.css("*").filter(lambda x: hasattr(x, 'text') and x.text and x.text.strip())
            
            for element in all_text_elements:
                text = element.text.strip()
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        found_elements.append(element)
                        break
                        
        except Exception as e:
            logger.debug(f"Pattern matching failed: {e}")
            
        return found_elements
    
    def _contains_credential_keywords(self, element) -> bool:
        """Check if element contains credential-related keywords."""
        if not hasattr(element, 'text') or not element.text:
            return False
            
        text = element.text.lower()
        keywords = ['bar', 'court', 'license', 'admission', 'attorney', 'solicitor', 'barrister']
        return any(keyword in text for keyword in keywords)
    
    def _filter_credential_elements(self, elements) -> List:
        """Filter elements to return most relevant credential information."""
        if not elements:
            return []
            
        # Score elements based on credential relevance
        scored_elements = []
        
        for element in elements:
            score = 0
            if hasattr(element, 'text') and element.text:
                text = element.text.lower()
                
                # Higher score for more specific credential terms
                if 'bar' in text: score += 3
                if 'court' in text: score += 3
                if 'license' in text: score += 2
                if 'admission' in text: score += 2
                if ' - ' in text: score += 2  # Common format: "State - Bar"
                if any(state in text for state in ['california', 'new york', 'texas', 'florida', 'egypt', 'england']): score += 1
                
                # Penalize very long text (likely not specific credentials)
                if len(text) > 200: score -= 2
                
                scored_elements.append((score, element))
        
        # Sort by score and return top elements
        scored_elements.sort(key=lambda x: x[0], reverse=True)
        return [elem for score, elem in scored_elements if score > 0][:5]  # Top 5 most relevant
    
    def _find_education_intelligently(self) -> List:
        """Find education information using intelligent strategies."""
        strategies = [
            lambda: self.current_page.css(".education li, .education p, .education div"),
            lambda: self.current_page.css(".is-style-no-bullets li"),
            lambda: self.current_page.xpath("//li[contains(text(), 'University') or contains(text(), 'College') or contains(text(), 'School')]"),
            lambda: self.current_page.css("*").filter(lambda x: self._contains_education_keywords(x))
        ]
        
        for strategy in strategies:
            try:
                elements = strategy()
                if elements:
                    return elements[:10]  # Limit to reasonable number
            except Exception:
                continue
        return []
    
    def _contains_education_keywords(self, element) -> bool:
        """Check if element contains education-related keywords."""
        if not hasattr(element, 'text') or not element.text:
            return False
            
        text = element.text.lower()
        keywords = ['university', 'college', 'school', 'degree', 'bachelor', 'master', 'phd', 'law school']
        return any(keyword in text for keyword in keywords)
    
    def _find_position_intelligently(self) -> List:
        """Find position/title information using intelligent strategies."""
        strategies = [
            lambda: self.current_page.css(".title, .position, .role, .designation"),
            lambda: self.current_page.xpath("//span[contains(@class, 'title') or contains(@class, 'position')]"),
            lambda: self.current_page.css("*").filter(lambda x: self._contains_position_keywords(x))
        ]
        
        for strategy in strategies:
            try:
                elements = strategy()
                if elements:
                    return elements[:5]
            except Exception:
                continue
        return []
    
    def _contains_position_keywords(self, element) -> bool:
        """Check if element contains position-related keywords."""
        if not hasattr(element, 'text') or not element.text:
            return False
            
        text = element.text.lower()
        keywords = ['partner', 'associate', 'counsel', 'director', 'manager', 'attorney', 'lawyer']
        return any(keyword in text for keyword in keywords)
    
    def _find_contact_intelligently(self, label: str) -> List:
        """Find contact information using intelligent strategies."""
        if 'email' in label:
            strategies = [
                lambda: self.current_page.css("a[href^='mailto:']"),
                lambda: self.current_page.css(".email, .contact-email"),
                lambda: self.current_page.xpath("//*[contains(@href, '@') or contains(text(), '@')]"),
            ]
        elif 'phone' in label:
            strategies = [
                lambda: self.current_page.css("a[href^='tel:']"),
                lambda: self.current_page.css(".phone, .contact-phone"),
                lambda: self.current_page.xpath("//*[contains(@href, 'tel:') or contains(text(), '+') or contains(text(), '(')]"),
            ]
        else:
            return []
            
        for strategy in strategies:
            try:
                elements = strategy()
                if elements:
                    return elements[:3]
            except Exception:
                continue
        return []
    
    def _find_generic_text_patterns(self, element: ElementSelector) -> List:
        """Find elements using generic text pattern matching."""
        # Extract potential keywords from original selector
        keywords = self._extract_keywords_from_selector(element.selector)
        
        if keywords:
            for keyword in keywords:
                try:
                    elements = self.current_page.xpath(f"//*[contains(text(), '{keyword}')]") 
                    if elements:
                        return elements[:5]
                except Exception:
                    continue
        
        return []
    
    def _extract_keywords_from_selector(self, selector: str) -> List[str]:
        """Extract meaningful keywords from a selector."""
        import re
        
        keywords = []
        
        # Extract from contains() functions
        contains_matches = re.findall(r"contains\([^,]+,\s*['\"]([^'\"]+)['\"]\)", selector)
        keywords.extend(contains_matches)
        
        # Extract class names
        class_matches = re.findall(r"@class\s*=\s*['\"]([^'\"]+)['\"]", selector)
        keywords.extend(class_matches)
        
        # Extract ID values
        id_matches = re.findall(r"@id\s*=\s*['\"]([^'\"]+)['\"]", selector)
        keywords.extend(id_matches)
        
        return [k for k in keywords if len(k) > 2]  # Filter out very short keywords
    
    def _try_structure_based_selection(self, element: ElementSelector) -> List:
        """Try to find elements based on structural patterns."""
        structure_xpaths = self._generate_structure_xpaths(element)
        
        for xpath in structure_xpaths:
            try:
                elements = self.current_page.xpath(xpath)
                if elements:
                    return elements
            except Exception:
                continue
        return []
    
    def _try_original_selector(self, element: ElementSelector) -> List:
        """Fallback to original selector without AutoMatch."""
        try:
            if element.selector_type == 'css':
                return self.current_page.css(element.selector)
            elif element.selector_type == 'xpath':
                return self.current_page.xpath(element.selector)
        except Exception:
            pass
        return []
    
    def _try_fuzzy_matching(self, element: ElementSelector) -> List:
        """Try fuzzy matching with selector variations."""
        try:
            original_selector = element.selector
            variations = self._generate_selector_variations(original_selector)
            
            for variation in variations:
                try:
                    if element.selector_type == 'xpath':
                        elements = self.current_page.xpath(variation, auto_match=True)
                    else:
                        elements = self.current_page.css(variation, auto_match=True)
                    
                    if elements:
                        logger.debug(f"Fuzzy matching successful with: {variation}")
                        return elements
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Fuzzy matching failed: {e}")
            
        return []
    
    def _generate_selector_variations(self, selector: str) -> List[str]:
        """Generate variations of a selector for fuzzy matching."""
        variations = []
        
        try:
            # For XPath selectors with specific text content
            if 'contains(text(),' in selector:
                import re
                # Extract the text being searched for
                text_matches = re.findall(r"contains\(text\(\),\s*['\"]([^'\"]+)['\"]\)", selector)
                
                for text in text_matches:
                    # Create more flexible variations
                    if ' - ' in text:  # Handle "Country - Bar" patterns
                        parts = text.split(' - ')
                        if len(parts) == 2:
                            # Try variations like "Country Bar", "Bar", etc.
                            variations.extend([
                                selector.replace(text, parts[1]),  # Just "Bar"
                                selector.replace(text, f"{parts[0]} {parts[1]}"),  # "Country Bar"
                                selector.replace(text, parts[1].replace('Bar', 'bar')),  # lowercase
                                f"//*[contains(text(), '{parts[1]}')]",  # Simple xpath for just the credential type
                            ])
                    
                    # Try partial matches
                    words = text.split()
                    for word in words:
                        if len(word) > 3:  # Skip short words
                            variations.append(f"//*[contains(text(), '{word}')]")
                    
                    # Try case variations
                    variations.extend([
                        selector.replace(text, text.lower()),
                        selector.replace(text, text.upper()),
                        selector.replace(text, text.title())
                    ])
            
            # For structural selectors, try making them more flexible
            if 'xpath:' in selector:
                base_selector = selector.replace('xpath:', '')
                # Try removing position-specific parts
                variations.extend([
                    base_selector.replace('[1]', ''),
                    base_selector.replace('[2]', ''),
                    base_selector.replace('//*', '//'),
                    f"({base_selector})[1]",  # Wrap in parentheses and get first
                ])
                
        except Exception as e:
            logger.debug(f"Error generating selector variations: {e}")
            
        return list(set(variations))  # Remove duplicates
    
    def _generate_semantic_xpaths(self, element: ElementSelector) -> List[str]:
        """
        Generate semantic XPaths based on element label and context.
        
        Args:
            element: ElementSelector configuration
            
        Returns:
            List of semantic XPath expressions
        """
        xpaths = []
        label = element.label.lower()
        
        # Common patterns based on label
        if 'name' in label:
            xpaths.extend([
                "//h1[contains(@class, 'name')]",
                "//h2[contains(@class, 'name')]", 
                "//span[contains(@class, 'name')]",
                "//*[@id[contains(., 'name')]]",
                "//strong[position()=1]",
                "//*[contains(@class, 'person-name') or contains(@class, 'lawyer-name')]"
            ])
        elif 'email' in label:
            xpaths.extend([
                "//a[contains(@href, 'mailto:')]",
                "//*[contains(@class, 'email')]",
                "//*[contains(text(), '@') and contains(text(), '.')]"
            ])
        elif 'phone' in label:
            xpaths.extend([
                "//a[contains(@href, 'tel:')]",
                "//*[contains(@class, 'phone')]",
                "//*[contains(text(), '(') and contains(text(), ')')]"
            ])
        elif 'title' in label or 'position' in label:
            xpaths.extend([
                "//*[contains(@class, 'title')]",
                "//*[contains(@class, 'position')]",
                "//*[contains(@class, 'job-title')]"
            ])
        elif 'link' in label or 'url' in label:
            xpaths.extend([
                "//a[@href]",
                "//*[@href]"
            ])
        
        return xpaths
    
    def _generate_structure_xpaths(self, element: ElementSelector) -> List[str]:
        """
        Generate structure-based XPaths.
        
        Args:
            element: ElementSelector configuration
            
        Returns:
            List of structure-based XPath expressions
        """
        xpaths = []
        
        # Convert CSS to XPath if needed
        if element.selector_type == 'css':
            xpath_equiv = self._css_to_xpath(element.selector)
            if xpath_equiv:
                xpaths.append(xpath_equiv)
        
        # Generate hierarchical patterns
        if element.selector_type == 'css' and '>' in element.selector:
            parts = element.selector.split('>')
            if len(parts) >= 2:
                # Try more flexible hierarchical patterns
                parent_part = parts[-2].strip()
                child_part = parts[-1].strip()
                xpaths.extend([
                    f"//*[contains(@class, '{parent_part.replace('.', '')}')]//*[contains(@class, '{child_part.replace('.', '')}')]",
                    f"//{parent_part.replace('.', '')}//{child_part.replace('.', '')}"
                ])
        
        return xpaths
    
    def _css_to_xpath(self, css_selector: str) -> str:
        """
        Convert simple CSS selectors to XPath.
        
        Args:
            css_selector: CSS selector string
            
        Returns:
            Equivalent XPath expression
        """
        # Basic CSS to XPath conversion
        import re
        
        xpath = css_selector
        
        # Convert class selectors
        xpath = re.sub(r'\.([a-zA-Z0-9_-]+)', r"[contains(@class, '\1')]", xpath)
        
        # Convert ID selectors
        xpath = re.sub(r'#([a-zA-Z0-9_-]+)', r"[@id='\1']", xpath)
        
        # Convert descendant combinators
        xpath = xpath.replace(' ', '//')
        
        # Convert child combinators
        xpath = xpath.replace('>', '/')
        
        # Add root if not present
        if not xpath.startswith('//') and not xpath.startswith('/'):
            xpath = '//' + xpath
        
        return xpath
    
    def _extract_single_element(self, element, element_config: ElementSelector) -> Any:
        """Extract data from a single element based on its type."""
        try:
            if element_config.element_type == 'text':
                return element.text.strip() if hasattr(element, 'text') else str(element).strip()
            
            elif element_config.element_type == 'html':
                return str(element) if hasattr(element, '__str__') else element.get_attribute('outerHTML')
            
            elif element_config.element_type == 'link':
                if hasattr(element, 'attrib'):
                    return element.attrib.get('href', '')
                else:
                    return element.get_attribute('href') or ''
            
            elif element_config.element_type == 'attribute':
                attr_name = element_config.attribute_name or 'value'
                if hasattr(element, 'attrib'):
                    return element.attrib.get(attr_name, '')
                else:
                    return element.get_attribute(attr_name) or ''
            
            else:
                # Default to text
                return element.text.strip() if hasattr(element, 'text') else str(element).strip()
                
        except Exception as e:
            logger.warning(f"Error extracting single element: {e}")
            return None
    
    def _extract_container_data(self, element_config: ElementSelector) -> List[Dict[str, Any]]:
        """
        Extract data from container elements using AutoMatch and find_similar.
        
        Args:
            element_config: ElementSelector with container configuration
            
        Returns:
            List of dictionaries containing extracted data from each container
        """
        containers = []
        
        try:
            logger.info(f"Extracting container data with selector: {element_config.selector}")
            
            # Check if this is a subpage container that should extract data from individual pages
            if self._is_subpage_container(element_config):
                return self._extract_subpage_container_data_from_main_containers(element_config)
            
            # Smart container detection for directory pages
            container_elements = []
            
            # If this looks like a directory template, try directory-specific container detection
            if self._looks_like_directory_template():
                logger.info("Directory template detected - using smart container detection")
                container_elements = self._find_directory_containers(element_config)
                if container_elements:
                    logger.info(f"Smart directory detection found {len(container_elements)} lawyer profile containers")
            
            # Fallback to original selector approach
            if not container_elements:
                try:
                    container_elements = self.current_page.css(element_config.selector, auto_match=True)
                    if container_elements:
                        logger.info(f"AutoMatch found {len(container_elements)} elements with selector: {element_config.selector}")
                except Exception as automatch_error:
                    logger.debug(f"AutoMatch failed: {automatch_error}")
            
            # If AutoMatch didn't work, try regular selection
            if not container_elements:
                try:
                    container_elements = self.current_page.css(element_config.selector)
                    if container_elements:
                        logger.info(f"Regular CSS found {len(container_elements)} elements with selector: {element_config.selector}")
                except Exception as css_error:
                    logger.debug(f"Regular CSS selection failed: {css_error}")
            
            # Try without dots for class selectors (handle dynamic classes)
            if not container_elements and '.' in element_config.selector:
                try:
                    # Handle cases like ".people.loading" -> "[class*='people'][class*='loading']"
                    classes = element_config.selector.replace('.', '').split()
                    if len(classes) > 1:
                        class_selector = ''.join([f'[class*="{cls}"]' for cls in classes])
                        container_elements = self.current_page.css(class_selector)
                        if container_elements:
                            logger.info(f"Class fallback found {len(container_elements)} elements with: {class_selector}")
                except Exception as class_error:
                    logger.debug(f"Class fallback failed: {class_error}")
                
            # CRITICAL: If use_find_similar is True, find all similar containers
            if hasattr(element_config, 'use_find_similar') and element_config.use_find_similar and container_elements:
                logger.info("Using find_similar to locate all matching containers")
                try:
                    # Use Scrapling's find_similar method to find all similar containers
                    similar_containers = container_elements[0].find_similar()
                    if similar_containers:
                        container_elements = similar_containers
                        logger.info(f"find_similar found {len(container_elements)} similar containers")
                except Exception as find_similar_error:
                    logger.warning(f"find_similar failed: {find_similar_error}")
                    # Continue with the original elements
                
            # If no elements found with direct selector, try alternative approaches
            if not container_elements:
                logger.warning(f"No elements found with selector: {element_config.selector}")
                
                # Convert nth-child selectors to generic ones for finding all similar elements
                generic_selector = self._make_selector_generic(element_config.selector)
                if generic_selector != element_config.selector:
                    logger.info(f"Trying generic selector: {generic_selector}")
                    try:
                        container_elements = self.current_page.css(generic_selector, auto_match=True)
                        if container_elements:
                            logger.info(f"Generic selector found {len(container_elements)} elements")
                    except Exception:
                        container_elements = self.current_page.css(generic_selector)
                
                # Try AutoMatch with pattern-based selectors
                if not container_elements:
                    pattern_selectors = self._generate_pattern_selectors(element_config.selector)
                    for pattern_sel in pattern_selectors:
                        try:
                            container_elements = self.current_page.css(pattern_sel, auto_match=True)
                            if container_elements:
                                logger.info(f"AutoMatch pattern found {len(container_elements)} elements with: {pattern_sel}")
                                break
                        except Exception:
                            continue
                
                # Fallback to manual alternative selectors
                if not container_elements:
                    # Try without dots in case selector has class issues
                    if element_config.selector.startswith('.'):
                        alt_selector = element_config.selector[1:]  # Remove leading dot
                        logger.info(f"Trying alternative selector: {alt_selector}")
                        container_elements = self.current_page.css(f'[class*="{alt_selector}"]')
                    
                    # If still no elements, try xpath
                    if not container_elements:
                        try:
                            xpath_selector = f"//*[contains(@class, '{element_config.selector.replace('.', '').replace(' ', '')}')]"
                            logger.info(f"Trying XPath selector: {xpath_selector}")
                            container_elements = self.current_page.xpath(xpath_selector)
                        except Exception as xpath_error:
                            logger.warning(f"XPath selection failed: {xpath_error}")
            
            if not container_elements:
                logger.warning(f"No container elements found after trying multiple selectors for: {element_config.selector}")
                return []
            
            logger.info(f"Found {len(container_elements)} container elements")
            
            # Extract data from each container
            for i, container in enumerate(container_elements):
                container_data = {}
                
                try:
                    # Extract sub-elements if defined
                    if hasattr(element_config, 'sub_elements') and element_config.sub_elements:
                        profile_link = None  # Track profile link for subpage navigation
                        
                        # Check if we need to extract profile links for subpage navigation
                        needs_profile_link = self._template_needs_subpage_data()
                        
                        for sub_element in element_config.sub_elements:
                            try:
                                # Handle both dict and object sub-elements
                                if isinstance(sub_element, dict):
                                    sub_label = sub_element.get('label')
                                    sub_selector = sub_element.get('selector')
                                    sub_type = sub_element.get('element_type', 'text')
                                    sub_required = sub_element.get('is_required', True)
                                else:
                                    sub_label = sub_element.label
                                    sub_selector = sub_element.selector
                                    sub_type = sub_element.element_type
                                    sub_required = getattr(sub_element, 'is_required', True)
                                
                                logger.debug(f"Extracting sub-element {sub_label} with selector: {sub_selector}")
                                
                                # Enhance generic selectors with smart mapping
                                if isinstance(sub_element, dict):
                                    enhanced_selector = self._map_generic_selector(sub_element, "directory")
                                    if enhanced_selector != sub_selector:
                                        logger.info(f"Enhanced selector for {sub_label}: '{sub_selector}' → '{enhanced_selector}'")
                                        sub_selector = enhanced_selector
                                
                                # Handle special case for empty selector (extract from container itself)
                                if not sub_selector:
                                    # Extract directly from the container element
                                    if sub_type == 'text':
                                        text_content = container.text if hasattr(container, 'text') else str(container)
                                        container_data[sub_label] = text_content.strip() if text_content else ''
                                    elif sub_type == 'link':
                                        href = ''
                                        if hasattr(container, 'get_attribute'):
                                            href = container.get_attribute('href') or ''
                                        elif hasattr(container, 'attrib'):
                                            href = container.attrib.get('href', '')
                                        full_url = self.current_page.urljoin(href) if href else ''
                                        container_data[sub_label] = full_url
                                        
                                        # Store link for potential subpage navigation
                                        if full_url and (hasattr(element_config, 'follow_links') and element_config.follow_links):
                                            container_data['_profile_link'] = full_url
                                    elif sub_type == 'attribute':
                                        attr_name = sub_element.get('attribute_name', 'value') if isinstance(sub_element, dict) else getattr(sub_element, 'attribute_name', 'value')
                                        attr_value = ''
                                        if hasattr(container, 'get_attribute'):
                                            attr_value = container.get_attribute(attr_name) or ''
                                        elif hasattr(container, 'attrib'):
                                            attr_value = container.attrib.get(attr_name, '')
                                        container_data[sub_label] = attr_value
                                    continue
                                
                                # Find sub-element within this container
                                sub_elements = []
                                if sub_selector:
                                    # Try multiple selectors if comma-separated
                                    selectors_to_try = [s.strip() for s in sub_selector.split(',') if s.strip()]
                                    
                                    for selector_attempt in selectors_to_try:
                                        try:
                                            # Handle XPath selectors
                                            if selector_attempt.startswith('xpath:'):
                                                xpath_expr = selector_attempt[6:]  # Remove 'xpath:' prefix
                                                logger.debug(f"Using XPath selector: {xpath_expr}")
                                                sub_elements = container.xpath(xpath_expr)
                                            else:
                                                # Handle CSS selectors
                                                sub_elements = container.css(selector_attempt)
                                            
                                            if sub_elements:
                                                logger.debug(f"Successfully found {len(sub_elements)} elements with selector: {selector_attempt}")
                                                break
                                                
                                        except Exception as selector_error:
                                            logger.debug(f"Selector '{selector_attempt}' failed for {sub_label}: {selector_error}")
                                            continue
                                    
                                    # If no enhanced selectors worked, try original approach
                                    if not sub_elements:
                                        try:
                                            original_selector = sub_element.get('selector') if isinstance(sub_element, dict) else sub_element.selector
                                            if original_selector and original_selector != sub_selector:
                                                if original_selector.startswith('xpath:'):
                                                    xpath_expr = original_selector[6:]
                                                    sub_elements = container.xpath(xpath_expr)
                                                else:
                                                    sub_elements = container.css(original_selector)
                                                if sub_elements:
                                                    logger.debug(f"Original selector worked: {original_selector}")
                                        except Exception:
                                            pass
                                    
                                    # Final fallback to enhanced XPath patterns
                                    if not sub_elements and any(keyword in sub_label.lower() for keyword in ['name', 'email', 'phone', 'title', 'position']):
                                        fallback_xpaths = self._generate_fallback_xpaths(sub_label, sub_type)
                                        for fallback_xpath in fallback_xpaths:
                                            try:
                                                sub_elements = container.xpath(fallback_xpath)
                                                if sub_elements:
                                                    logger.info(f"Fallback XPath worked for {sub_label}: {fallback_xpath}")
                                                    break
                                            except Exception:
                                                continue
                                
                                if sub_elements:
                                    try:
                                        if sub_type == 'text':
                                            text_content = sub_elements[0].text if hasattr(sub_elements[0], 'text') else str(sub_elements[0])
                                            container_data[sub_label] = text_content.strip() if text_content else ''
                                        elif sub_type == 'link':
                                            href = ''
                                            if hasattr(sub_elements[0], 'get_attribute'):
                                                href = sub_elements[0].get_attribute('href') or ''
                                            elif hasattr(sub_elements[0], 'attrib'):
                                                href = sub_elements[0].attrib.get('href', '')
                                            full_url = self.current_page.urljoin(href) if href else ''
                                            container_data[sub_label] = full_url
                                            
                                            # Store profile link for subpage navigation
                                            if full_url and any(keyword in sub_label.lower() for keyword in ['profile', 'link', 'url', 'page']):
                                                profile_link = full_url
                                                container_data['_profile_link'] = full_url
                                                logger.debug(f"Found profile link for container {i}: {full_url}")
                                            
                                            # Store link for potential subpage navigation (legacy support)
                                            elif full_url and (hasattr(element_config, 'follow_links') and element_config.follow_links):
                                                if not profile_link:  # Only set if we haven't found a specific profile link
                                                    profile_link = full_url
                                                    container_data['_profile_link'] = full_url
                                        elif sub_type == 'attribute':
                                            attr_name = sub_element.get('attribute_name', 'value') if isinstance(sub_element, dict) else getattr(sub_element, 'attribute_name', 'value')
                                            attr_value = ''
                                            if hasattr(sub_elements[0], 'get_attribute'):
                                                attr_value = sub_elements[0].get_attribute(attr_name) or ''
                                            elif hasattr(sub_elements[0], 'attrib'):
                                                attr_value = sub_elements[0].attrib.get(attr_name, '')
                                            container_data[sub_label] = attr_value
                                        elif sub_type == 'html':
                                            container_data[sub_label] = str(sub_elements[0])
                                        else:
                                            # Default to text
                                            text_content = sub_elements[0].text if hasattr(sub_elements[0], 'text') else str(sub_elements[0])
                                            container_data[sub_label] = text_content.strip() if text_content else ''
                                        
                                        logger.debug(f"Extracted {sub_label}: {container_data[sub_label]}")
                                    except Exception as extract_error:
                                        logger.warning(f"Error extracting value for {sub_label}: {extract_error}")
                                        container_data[sub_label] = None
                                else:
                                    if sub_required:
                                        logger.warning(f"Required sub-element not found: {sub_label} with selector {sub_selector} in container {i}")
                                    container_data[sub_label] = None
                                    
                            except Exception as e:
                                sub_label = sub_element.get('label') if isinstance(sub_element, dict) else getattr(sub_element, 'label', 'unknown')
                                logger.warning(f"Error processing sub-element {sub_label} from container {i}: {e}")
                                container_data[sub_label] = None
                        
                        # Auto-extract profile link if needed and not already found
                        if needs_profile_link and not profile_link:
                            try:
                                # Try to find any link within the container that points to a lawyer page
                                lawyer_links = container.css("a[href*='/lawyer/']")
                                if not lawyer_links:
                                    lawyer_links = container.css("a")  # Fallback to any link
                                
                                for link in lawyer_links:
                                    href = ''
                                    if hasattr(link, 'get_attribute'):
                                        href = link.get_attribute('href') or ''
                                    elif hasattr(link, 'attrib'):
                                        href = link.attrib.get('href', '')
                                    
                                    if href and ('/lawyer/' in href or href.startswith('/')):
                                        full_url = self.current_page.urljoin(href) if href else ''
                                        if full_url and '/lawyer/' in full_url:
                                            profile_link = full_url
                                            container_data['_profile_link'] = full_url
                                            logger.debug(f"Auto-extracted profile link for container {i}: {full_url}")
                                            break
                            except Exception as link_error:
                                logger.debug(f"Could not auto-extract profile link for container {i}: {link_error}")
                    
                    # If no sub-elements defined, extract the container's text
                    if not container_data or all(v is None for v in container_data.values()):
                        try:
                            text_content = container.text if hasattr(container, 'text') else str(container)
                            container_data['text'] = text_content.strip() if text_content else ''
                        except Exception as text_error:
                            logger.warning(f"Error extracting text from container {i}: {text_error}")
                            container_data['text'] = ''
                    
                    # Add container index for reference
                    container_data['_container_index'] = i
                    containers.append(container_data)
                    
                except Exception as container_error:
                    logger.warning(f"Error processing container {i}: {container_error}")
                    # Add empty container to maintain index consistency
                    containers.append({'_container_index': i, '_error': str(container_error)})
            
            logger.info(f"Successfully extracted data from {len(containers)} containers")
            return containers
            
        except Exception as e:
            logger.error(f"Error extracting container data: {e}")
            return []
    
    def _generate_pattern_selectors(self, original_selector: str) -> List[str]:
        """
        Generate alternative selectors for AutoMatch to try.
        
        Args:
            original_selector: The original CSS selector
            
        Returns:
            List of alternative selectors to try
        """
        patterns = []
        
        # If it's a class selector, try variations
        if original_selector.startswith('.'):
            class_name = original_selector[1:]
            patterns.extend([
                f'[class*="{class_name}"]',
                f'div.{class_name}',
                f'*[class~="{class_name}"]',
                f'div[class*="{class_name}"]',
                # Try partial class matches
                f'[class*="{class_name.split("-")[0] if "-" in class_name else class_name[:5]}"]'
            ])
        
        # If it's an ID selector
        elif original_selector.startswith('#'):
            id_name = original_selector[1:]
            patterns.extend([
                f'[id*="{id_name}"]',
                f'div#{id_name}',
                f'*[id~="{id_name}"]'
            ])
        
        # Tag-based patterns
        elif original_selector.isalpha():
            patterns.extend([
                f'{original_selector}[class]',
                f'{original_selector}[id]',
                f'div {original_selector}',
                f'main {original_selector}'
            ])
        
        # Complex selector patterns
        else:
            # Try breaking down complex selectors
            parts = original_selector.split()
            if len(parts) > 1:
                patterns.extend([
                    parts[-1],  # Last part only
                    ' '.join(parts[-2:]) if len(parts) >= 2 else parts[-1],  # Last two parts
                    f'[class*="{parts[-1].replace(".", "").replace("#", "")}"]'
                ])
        
        return patterns
    
    def _make_selector_generic(self, selector: str) -> str:
        """
        Convert specific nth-child selectors to generic ones to find all similar elements.
        
        Args:
            selector: Original CSS selector
            
        Returns:
            Generic selector without nth-child restrictions
        """
        import re
        
        # Remove nth-child() selectors to make it generic
        generic_selector = re.sub(r':nth-child\(\d+\)', '', selector)
        
        # Remove > combinators at the end if they become orphaned
        generic_selector = re.sub(r'\s*>\s*$', '', generic_selector)
        
        # Clean up multiple spaces
        generic_selector = re.sub(r'\s+', ' ', generic_selector).strip()
        
        # If selector becomes too generic, try to keep some structure
        if len(generic_selector.split()) < 2 and '>' in selector:
            # Keep the last two parts
            parts = selector.split('>')
            if len(parts) >= 2:
                # Keep the last element but make it generic
                last_part = parts[-1].strip()
                second_last = parts[-2].strip()
                last_part_generic = re.sub(r':nth-child\(\d+\)', '', last_part).strip()
                generic_selector = f"{second_last} {last_part_generic}".strip()
        
        return generic_selector if generic_selector else selector
    
    def _extract_subpage_data(self, element_config: ElementSelector, main_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Navigate to sub-pages and extract additional data.
        
        Args:
            element_config: ElementSelector with subpage configuration
            main_data: Main page data containing profile links
            
        Returns:
            Enhanced data with subpage information
        """
        if not hasattr(element_config, 'follow_links') or not element_config.follow_links:
            return main_data
        
        if not hasattr(element_config, 'subpage_elements') or not element_config.subpage_elements:
            return main_data
        
        enhanced_data = main_data.copy()
        
        # Process each container item that has a profile link
        container_label = element_config.label
        container_data = enhanced_data.get(container_label, [])
        
        for item in container_data:
            if not isinstance(item, dict):
                continue
                
            # Look for profile link (check _profile_link first, then other fields)
            profile_link = item.get('_profile_link')
            if not profile_link:
                for key, value in item.items():
                    if ('link' in key.lower() or 'url' in key.lower() or 'href' in key.lower()) and isinstance(value, str) and value.startswith('http'):
                        profile_link = value
                        break
                        
            if not profile_link:
                continue
                
            try:
                logger.info(f"Navigating to subpage: {profile_link}")
                
                # Fetch the subpage
                subpage = self._fetch_page(profile_link)
                if not subpage:
                    logger.warning(f"Failed to fetch subpage: {profile_link}")
                    continue
                
                # Extract subpage data
                subpage_data = {}
                for sub_element in element_config.subpage_elements:
                    try:
                        if isinstance(sub_element, dict):
                            sub_label = sub_element.get('label')
                            sub_selector = sub_element.get('selector')
                            sub_type = sub_element.get('element_type', 'text')
                        else:
                            sub_label = sub_element.label
                            sub_selector = sub_element.selector
                            sub_type = sub_element.element_type
                        
                        # Use AutoMatch for subpage elements too
                        sub_elements = []
                        try:
                            sub_elements = subpage.css(sub_selector, auto_match=True)
                        except Exception:
                            sub_elements = subpage.css(sub_selector)
                        
                        if sub_elements:
                            if sub_type == 'text':
                                text_content = sub_elements[0].text if hasattr(sub_elements[0], 'text') else str(sub_elements[0])
                                subpage_data[sub_label] = text_content.strip() if text_content else ''
                            elif sub_type == 'link':
                                href = ''
                                if hasattr(sub_elements[0], 'get_attribute'):
                                    href = sub_elements[0].get_attribute('href') or ''
                                elif hasattr(sub_elements[0], 'attrib'):
                                    href = sub_elements[0].attrib.get('href', '')
                                subpage_data[sub_label] = subpage.urljoin(href) if href else ''
                            elif sub_type == 'attribute':
                                attr_name = sub_element.get('attribute_name', 'value') if isinstance(sub_element, dict) else getattr(sub_element, 'attribute_name', 'value')
                                attr_value = ''
                                if hasattr(sub_elements[0], 'get_attribute'):
                                    attr_value = sub_elements[0].get_attribute(attr_name) or ''
                                elif hasattr(sub_elements[0], 'attrib'):
                                    attr_value = sub_elements[0].attrib.get(attr_name, '')
                                subpage_data[sub_label] = attr_value
                            elif sub_type == 'html':
                                subpage_data[sub_label] = str(sub_elements[0])
                            else:
                                text_content = sub_elements[0].text if hasattr(sub_elements[0], 'text') else str(sub_elements[0])
                                subpage_data[sub_label] = text_content.strip() if text_content else ''
                        else:
                            logger.debug(f"Subpage element not found: {sub_label} with selector {sub_selector}")
                            subpage_data[sub_label] = None
                            
                    except Exception as e:
                        logger.warning(f"Error extracting subpage element {sub_label}: {e}")
                        subpage_data[sub_label] = None
                
                # Merge subpage data into main item
                item.update(subpage_data)
                logger.info(f"Enhanced data for {item.get('name', 'Unknown')} with {len(subpage_data)} subpage fields")
                
                # Add small delay between subpage requests to be respectful
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing subpage {profile_link}: {e}")
                continue
        
        return enhanced_data
    
    def _process_container_subpages(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process containers with follow_links enabled for automatic subpage navigation.
        
        Args:
            scraped_data: Main page scraped data
            
        Returns:
            Enhanced data with subpage information from containers
        """
        enhanced_data = scraped_data.copy()
        
        # Check each element configuration for container subpage extraction
        for element in self.template.elements:
            if (hasattr(element, 'is_container') and element.is_container and 
                hasattr(element, 'follow_links') and element.follow_links):
                
                if hasattr(element, 'subpage_elements') and element.subpage_elements:
                    logger.info(f"Processing container subpage extraction for element: {element.label}")
                    
                    # Get the container data
                    container_data = enhanced_data.get(element.label, [])
                    if not isinstance(container_data, list):
                        continue
                    
                    # Process each container item for subpage data
                    for item in container_data:
                        if not isinstance(item, dict):
                            continue
                            
                        # Look for a profile link in the item (check _profile_link first, then other fields)
                        profile_link = item.get('_profile_link')
                        if not profile_link:
                            for key, value in item.items():
                                if ('link' in key.lower() or 'url' in key.lower() or 'href' in key.lower()) and isinstance(value, str) and value.startswith('http'):
                                    profile_link = value
                                    break
                        
                        if not profile_link:
                            continue
                            
                        try:
                            logger.info(f"Navigating to container subpage: {profile_link}")
                            
                            # Fetch the subpage
                            subpage = self._fetch_page(profile_link)
                            if not subpage:
                                logger.warning(f"Failed to fetch container subpage: {profile_link}")
                                continue
                            
                            # Extract subpage data
                            subpage_data = {}
                            for sub_element in element.subpage_elements:
                                try:
                                    if isinstance(sub_element, dict):
                                        sub_label = sub_element.get('label')
                                        sub_selector = sub_element.get('selector')
                                        sub_type = sub_element.get('element_type', 'text')
                                    else:
                                        sub_label = sub_element.label
                                        sub_selector = sub_element.selector
                                        sub_type = sub_element.element_type
                                    
                                    # Use AutoMatch for subpage elements too
                                    sub_elements = []
                                    try:
                                        sub_elements = subpage.css(sub_selector, auto_match=True)
                                    except Exception:
                                        sub_elements = subpage.css(sub_selector)
                                    
                                    if sub_elements:
                                        if sub_type == 'text':
                                            text_content = sub_elements[0].text if hasattr(sub_elements[0], 'text') else str(sub_elements[0])
                                            subpage_data[sub_label] = text_content.strip() if text_content else ''
                                        elif sub_type == 'link':
                                            href = ''
                                            if hasattr(sub_elements[0], 'get_attribute'):
                                                href = sub_elements[0].get_attribute('href') or ''
                                            elif hasattr(sub_elements[0], 'attrib'):
                                                href = sub_elements[0].attrib.get('href', '')
                                            subpage_data[sub_label] = subpage.urljoin(href) if href else ''
                                        elif sub_type == 'attribute':
                                            attr_name = sub_element.get('attribute_name', 'value') if isinstance(sub_element, dict) else getattr(sub_element, 'attribute_name', 'value')
                                            attr_value = ''
                                            if hasattr(sub_elements[0], 'get_attribute'):
                                                attr_value = sub_elements[0].get_attribute(attr_name) or ''
                                            elif hasattr(sub_elements[0], 'attrib'):
                                                attr_value = sub_elements[0].attrib.get(attr_name, '')
                                            subpage_data[sub_label] = attr_value
                                        elif sub_type == 'html':
                                            subpage_data[sub_label] = str(sub_elements[0])
                                        else:
                                            text_content = sub_elements[0].text if hasattr(sub_elements[0], 'text') else str(sub_elements[0])
                                            subpage_data[sub_label] = text_content.strip() if text_content else ''
                                    else:
                                        logger.debug(f"Container subpage element not found: {sub_label} with selector {sub_selector}")
                                        subpage_data[sub_label] = None
                                        
                                except Exception as e:
                                    logger.warning(f"Error extracting container subpage element {sub_label}: {e}")
                                    subpage_data[sub_label] = None
                            
                            # Merge subpage data into main item
                            item.update(subpage_data)
                            logger.info(f"Enhanced container item with {len(subpage_data)} subpage fields")
                            
                            # Add small delay between subpage requests to be respectful
                            time.sleep(1)
                            
                        except Exception as e:
                            logger.error(f"Error processing container subpage {profile_link}: {e}")
                            continue
        
        return enhanced_data
    
    def _handle_action_subpage_navigation(self, action: NavigationAction, main_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle action-based subpage navigation for containers.
        
        Args:
            action: NavigationAction with subpage navigation enabled
            main_data: Main page data containing containers
            
        Returns:
            Enhanced data with subpage information from action navigation
        """
        enhanced_data = {}
        
        try:
            # Find containers in main data that might have profile links
            for element in self.template.elements:
                if (hasattr(element, 'is_container') and element.is_container and 
                    element.label in main_data):
                    
                    container_data = main_data.get(element.label, [])
                    if not isinstance(container_data, list):
                        continue
                    
                    enhanced_container_data = []
                    
                    # Process each container item for subpage navigation
                    for item in container_data:
                        if not isinstance(item, dict):
                            enhanced_container_data.append(item)
                            continue
                        
                        # Look for a profile link in the item using the action's target pattern
                        profile_link = None
                        for key, value in item.items():
                            if (isinstance(value, str) and value.startswith('http') and 
                                action.target_url in value):
                                profile_link = value
                                break
                        
                        # If no direct match, try to construct the URL pattern
                        if not profile_link and action.target_url:
                            # Try to find a pattern that matches the action URL
                            for key, value in item.items():
                                if ('link' in key.lower() or 'url' in key.lower() or 'href' in key.lower()):
                                    if isinstance(value, str) and value.startswith('http'):
                                        profile_link = value
                                        break
                        
                        if profile_link:
                            try:
                                logger.info(f"Navigating to action subpage: {profile_link}")
                                
                                # Fetch the subpage
                                subpage = self._fetch_page(profile_link)
                                if not subpage:
                                    logger.warning(f"Failed to fetch action subpage: {profile_link}")
                                    enhanced_container_data.append(item)
                                    continue
                                
                                # Extract additional data from subpage using same template elements
                                subpage_data = {}
                                
                                # Re-run template extraction on subpage
                                for sub_element in self.template.elements:
                                    if not (hasattr(sub_element, 'is_container') and sub_element.is_container):
                                        try:
                                            sub_value = self._extract_element_data(sub_element)
                                            if sub_value is not None:
                                                subpage_data[f"subpage_{sub_element.label}"] = sub_value
                                        except Exception as e:
                                            logger.warning(f"Error extracting subpage element {sub_element.label}: {e}")
                                
                                # Merge subpage data into main item
                                enhanced_item = item.copy()
                                enhanced_item.update(subpage_data)
                                enhanced_item['_subpage_url'] = profile_link
                                enhanced_container_data.append(enhanced_item)
                                
                                logger.info(f"Enhanced container item with {len(subpage_data)} subpage fields")
                                
                                # Add small delay between subpage requests to be respectful
                                time.sleep(1)
                                
                            except Exception as e:
                                logger.error(f"Error processing action subpage {profile_link}: {e}")
                                enhanced_container_data.append(item)
                        else:
                            enhanced_container_data.append(item)
                    
                    enhanced_data[element.label] = enhanced_container_data
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error in action subpage navigation: {e}")
            return {}
    
    def _merge_directory_with_subpage_data(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge directory container data with subpage container data into the expected format.
        Expected format: [{"name": "...", "position": "...", "subinfo": {"education": "...", "creds": "..."}}]
        
        Args:
            scraped_data: Data with separate main and subpage containers
            
        Returns:
            Merged data in the expected format
        """
        try:
            # Check if we have both main and subpage data to merge
            main_data = scraped_data.get('main', [])
            subpage_data = scraped_data.get('subpage', []) or scraped_data.get('sublink', []) or scraped_data.get('sublink_container', []) or scraped_data.get('subcon', [])
            
            if not main_data:
                logger.info("No main directory data to merge")
                return scraped_data
            
            logger.info(f"Merging {len(main_data)} main entries with {len(subpage_data)} subpage entries")
            
            merged_results = []
            
            # Process each main entry
            for i, main_entry in enumerate(main_data):
                if not isinstance(main_entry, dict):
                    continue
                
                # Start with all existing data from main entry (preserves intelligent sublink data)
                merged_entry = main_entry.copy()
                
                # Ensure standard fields are properly set
                if 'profile_link' not in merged_entry or not merged_entry['profile_link']:
                    merged_entry['profile_link'] = main_entry.get('_profile_link') or main_entry.get('email', '').replace('mailto:', 'https://www.gibsondunn.com/lawyer/') if main_entry.get('email') else None
                
                # Find corresponding subpage data by container index
                container_index = main_entry.get('_container_index')
                corresponding_subpage = None
                
                if container_index is not None and subpage_data:
                    for subpage_entry in subpage_data:
                        if (isinstance(subpage_entry, dict) and 
                            subpage_entry.get('_container_index') == container_index):
                            corresponding_subpage = subpage_entry
                            break
                
                # Add subinfo section with education and credentials
                subinfo = {}
                if corresponding_subpage:
                    education = corresponding_subpage.get('education')
                    creds = corresponding_subpage.get('creds')
                    
                    if education:
                        subinfo['education'] = education
                    if creds:
                        subinfo['credentials'] = creds
                
                # Only add subinfo if it has data
                if subinfo:
                    merged_entry['subinfo'] = subinfo
                
                merged_results.append(merged_entry)
            
            # Return the merged data in a clean format
            result = {'lawyers': merged_results}
            
            # Preserve any actions_executed data
            if 'actions_executed' in scraped_data:
                result['actions_executed'] = scraped_data['actions_executed']
            
            logger.info(f"Successfully merged data into {len(merged_results)} unified lawyer entries")
            return result
            
        except Exception as e:
            logger.error(f"Error merging directory and subpage data: {e}")
            return scraped_data
    
    def _process_subpage_extractions(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process subpage extractions for elements that have follow_links enabled.
        
        Args:
            scraped_data: Main page scraped data
            
        Returns:
            Enhanced data with subpage information
        """
        enhanced_data = scraped_data.copy()
        
        # Check each element configuration for subpage extraction
        for element in self.template.elements:
            if hasattr(element, 'follow_links') and element.follow_links:
                if hasattr(element, 'subpage_elements') and element.subpage_elements:
                    logger.info(f"Processing subpage extraction for element: {element.label}")
                    enhanced_data = self._extract_subpage_data(element, enhanced_data)
        
        return enhanced_data
    
    def _extract_multiple_elements(self, elements, element_config: ElementSelector) -> List[Any]:
        """Extract data from multiple elements."""
        results = []
        
        for element in elements:
            try:
                value = self._extract_single_element(element, element_config)
                if value is not None:
                    results.append(value)
            except Exception as e:
                logger.warning(f"Error extracting from multiple element: {e}")
                continue
        
        return results
    
    def _execute_actions(self) -> Dict[str, Any]:
        """
        Execute navigation actions defined in the template.
        
        Returns:
            Dictionary containing action execution results
        """
        action_results = {}
        
        for action in self.template.actions:
            try:
                logger.info(f"Executing action: {action.label}")
                
                result = self._execute_single_action(action)
                action_results[action.label] = result
                
                # Wait after action if specified
                if action.wait_after > 0:
                    logger.debug(f"Waiting {action.wait_after} seconds after action")
                    time.sleep(action.wait_after)
                
            except Exception as e:
                error_msg = f"Failed to execute action {action.label}: {str(e)}"
                logger.error(error_msg)
                action_results[action.label] = {'success': False, 'error': error_msg}
        
        return action_results
    
    def _execute_single_action(self, action: NavigationAction) -> Dict[str, Any]:
        """
        Execute a single navigation action with actual browser interaction.
        
        Args:
            action: NavigationAction to execute
            
        Returns:
            Dictionary containing execution result
        """
        if not self.current_page:
            raise Exception("No page available for action execution")
        
        try:
            # Find the action element using AutoMatch for better reliability
            action_elements = []
            
            # If action selector is generic and we need profile links, enhance it
            if action.selector == 'a' and self._template_needs_subpage_data():
                logger.info("Generic action selector detected - enhancing for profile links")
                enhanced_selectors = [
                    "a[href*='/lawyer/']",
                    "a[href*='/attorney/']", 
                    ".people.loading a",
                    "a"  # Fallback to original
                ]
                
                for enhanced_selector in enhanced_selectors:
                    try:
                        action_elements = self.current_page.css(enhanced_selector)
                        if action_elements and len(action_elements) <= 10:  # Reasonable number
                            logger.info(f"Enhanced action selector found {len(action_elements)} elements: {enhanced_selector}")
                            break
                    except Exception:
                        continue
            else:
                try:
                    action_elements = self.current_page.css(action.selector, auto_match=True)
                except Exception:
                    action_elements = self.current_page.css(action.selector)
            
            if not action_elements:
                raise Exception(f"Action element not found: {action.selector}")
            
            if len(action_elements) > 20:
                logger.warning(f"Action selector '{action.selector}' matched {len(action_elements)} elements - using first one")
                action_elements = action_elements[:1]
            
            action_element = action_elements[0]
            
            # Execute the action based on type
            if action.action_type == 'click':
                logger.info(f"Executing click on: {action.selector}")
                
                # Try to get the target URL before clicking
                target_url = None
                if hasattr(action_element, 'get_attribute'):
                    target_url = action_element.get_attribute('href')
                elif hasattr(action_element, 'attrib'):
                    target_url = action_element.attrib.get('href')
                
                # Use page_action for reliable clicking
                def click_element(page):
                    try:
                        element_locator = page.locator(action.selector)
                        if element_locator.count() == 0:
                            logger.warning(f"Action element not found: {action.selector}")
                            return page
                        
                        # Scroll to element if needed
                        element_locator.scroll_into_view_if_needed()
                        
                        # Click the element
                        element_locator.click()
                        logger.info(f"Successfully clicked: {action.selector}")
                        
                        # Wait for any navigation or content changes
                        if target_url:
                            # If it's a link, wait for navigation
                            page.wait_for_load_state('networkidle', timeout=10000)
                        else:
                            # Wait a bit for dynamic content
                            page.wait_for_timeout(action.wait_after * 1000)
                        
                        return page
                        
                    except Exception as page_action_error:
                        logger.warning(f"Page action click failed: {page_action_error}")
                        return page
                
                try:
                    # Use page_action for clicking
                    fetch_options = {
                        'headless': self.template.headless,
                        'network_idle': True,
                        'timeout': self.template.wait_timeout * 1000,
                        'page_action': click_element
                    }
                    
                    # Get current URL or use target URL if it's a link
                    current_url = self.current_page.url
                    
                    # Re-fetch the page with the click action
                    updated_page = self.fetcher.fetch(current_url, **fetch_options)
                    
                    if updated_page and updated_page.status == 200:
                        self.current_page = updated_page
                        result = {'success': True, 'action': 'click_page_action', 'selector': action.selector, 'navigated_to': target_url}
                    else:
                        # Fallback to manual navigation if it's a link
                        if target_url:
                            full_url = self.current_page.urljoin(target_url)
                            logger.info(f"Fallback: navigating to link target: {full_url}")
                            self.current_page = self._fetch_page(full_url)
                            result = {'success': True, 'action': 'fallback_navigate', 'selector': action.selector, 'navigated_to': full_url}
                        else:
                            raise Exception("Page action failed and no target URL for fallback")
                
                except Exception as click_error:
                    logger.warning(f"Click action failed: {click_error}")
                    # Fallback to manual navigation if it's a link
                    if target_url:
                        full_url = self.current_page.urljoin(target_url)
                        logger.info(f"Final fallback: navigating to link target: {full_url}")
                        self.current_page = self._fetch_page(full_url)
                        result = {'success': True, 'action': 'fallback_navigate', 'selector': action.selector, 'navigated_to': full_url}
                    else:
                        raise click_error
                
            elif action.action_type == 'scroll':
                logger.info(f"Executing scroll to: {action.selector}")
                try:
                    if hasattr(self.current_page, 'browser') and hasattr(self.current_page.browser, 'page'):
                        playwright_page = self.current_page.browser.page
                        playwright_page.locator(action.selector).scroll_into_view_if_needed()
                        result = {'success': True, 'action': 'scroll', 'selector': action.selector}
                    else:
                        result = {'success': True, 'action': 'scroll_simulated', 'selector': action.selector}
                except Exception:
                    result = {'success': True, 'action': 'scroll_simulated', 'selector': action.selector}
                
            elif action.action_type == 'hover':
                logger.info(f"Executing hover on: {action.selector}")
                try:
                    if hasattr(self.current_page, 'browser') and hasattr(self.current_page.browser, 'page'):
                        playwright_page = self.current_page.browser.page
                        playwright_page.hover(action.selector)
                        result = {'success': True, 'action': 'hover', 'selector': action.selector}
                    else:
                        result = {'success': True, 'action': 'hover_simulated', 'selector': action.selector}
                except Exception:
                    result = {'success': True, 'action': 'hover_simulated', 'selector': action.selector}
                
            elif action.action_type == 'wait':
                logger.info(f"Waiting {action.wait_after} seconds at: {action.selector}")
                time.sleep(action.wait_after)
                result = {'success': True, 'action': 'wait', 'duration': action.wait_after}
                
            else:
                raise Exception(f"Unsupported action type: {action.action_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_page_title(self) -> str:
        """Get the title of the current page."""
        try:
            if self.current_page:
                title_elements = self.current_page.css('title')
                if title_elements:
                    return title_elements[0].text.strip()
            return ""
        except:
            return ""
    
    def _cleanup(self) -> None:
        """Clean up resources after scraping."""
        try:
            # Scrapling handles cleanup automatically
            logger.info("Scraping session cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    def _generate_fallback_xpaths(self, label: str, element_type: str) -> List[str]:
        """
        Generate smart XPath fallbacks based on label and element type.
        Enhanced for Gibson Dunn and legal directory pages.
        
        Args:
            label: The semantic label (e.g., 'name', 'email', 'phone')
            element_type: The expected element type ('text', 'link', etc.)
            
        Returns:
            List of XPath expressions to try as fallbacks
        """
        fallback_xpaths = []
        
        label_lower = label.lower()
        
        # Enhanced email detection for Gibson Dunn
        if any(keyword in label_lower for keyword in ['email', 'emaik', 'mail']):
            fallback_xpaths.extend([
                ".//a[contains(@href, 'mailto:')]",
                ".//*[contains(text(), '@gibsondunn.com')]",
                ".//*[contains(text(), '@') and contains(text(), '.com')]",
                ".//a[contains(text(), '@')]",
                ".//*[@class and contains(@class, 'email')]",
                ".//*[contains(text(), '@') and contains(text(), '.')]"
            ])
        # Enhanced phone detection
        elif 'phone' in label_lower:
            fallback_xpaths.extend([
                ".//a[contains(@href, 'tel:')]",
                ".//*[contains(text(), '+1') or contains(text(), '(') or contains(text(), ')')]",
                ".//*[contains(text(), '.') and contains(text(), '.') and string-length(text()) > 10 and string-length(text()) < 20]",
                ".//*[@class and contains(@class, 'phone')]"
            ])
        # Enhanced name detection for lawyer profiles
        elif 'name' in label_lower:
            fallback_xpaths.extend([
                ".//h1[not(contains(@class, 'site-title'))]",
                ".//h2[not(contains(@class, 'widget-title'))]",
                ".//strong[position()=1 and string-length(normalize-space(text())) > 5]",
                ".//*[@class and (contains(@class, 'name') or contains(@class, 'lawyer') or contains(@class, 'person'))]",
                ".//strong[string-length(normalize-space(text())) > 5 and string-length(normalize-space(text())) < 50]",
                ".//*[contains(@class, 'entry-title') or contains(@class, 'page-title')]//text()[normalize-space()]",
                ".//h1//text()[normalize-space() and string-length(.) > 3]"
            ])
        # Enhanced title/position detection for legal professionals
        elif any(keyword in label_lower for keyword in ['title', 'position', 'job']):
            fallback_xpaths.extend([
                ".//*[contains(text(), 'Partner') or contains(text(), 'Associate') or contains(text(), 'Counsel') or contains(text(), 'Senior')]",
                ".//*[@class and (contains(@class, 'title') or contains(@class, 'position') or contains(@class, 'role'))]",
                ".//span[contains(text(), 'Partner') or contains(text(), 'Associate') or contains(text(), 'Of Counsel')]",
                ".//*[contains(text(), 'Practice') and contains(text(), 'Chair')]",
                ".//p[contains(text(), 'Partner') or contains(text(), 'Associate')]"
            ])
        # Enhanced practice area/sector detection
        elif any(keyword in label_lower for keyword in ['practice', 'sector', 'area']):
            fallback_xpaths.extend([
                ".//*[contains(text(), 'Finance') or contains(text(), 'Corporate') or contains(text(), 'Litigation')]",
                ".//*[contains(text(), 'Law') or contains(text(), 'Practice') or contains(text(), 'Legal')]",
                ".//*[@class and (contains(@class, 'practice') or contains(@class, 'capability'))]",
                ".//a[contains(@href, '/practice/') or contains(@href, '/capabilities/')]",
                ".//*[contains(text(), 'M&A') or contains(text(), 'Securities') or contains(text(), 'Real Estate')]"
            ])
        # Enhanced education detection
        elif 'education' in label_lower:
            fallback_xpaths.extend([
                ".//*[contains(text(), 'University') or contains(text(), 'College') or contains(text(), 'School') or contains(text(), 'Law School')]",
                ".//*[contains(text(), 'J.D.') or contains(text(), 'LL.M.') or contains(text(), 'B.A.') or contains(text(), 'B.S.') or contains(text(), 'MBA')]",
                ".//li[contains(text(), 'University') or contains(text(), 'College')]",
                ".//*[contains(text(), 'Harvard') or contains(text(), 'Yale') or contains(text(), 'Stanford')]",
                ".//ul[@class='is-style-no-bullets']//li"
            ])
        # Enhanced credentials detection
        elif any(keyword in label_lower for keyword in ['cred', 'admission', 'bar']):
            fallback_xpaths.extend([
                ".//*[contains(text(), 'Bar') or contains(text(), 'Admission') or contains(text(), 'Admitted')]",
                ".//*[contains(text(), 'California') or contains(text(), 'New York') or contains(text(), 'State')]",
                ".//li[contains(text(), 'Bar') or contains(text(), 'Court')]",
                ".//ul[@class='is-style-no-bullets']//li[contains(text(), 'Admitted') or contains(text(), 'Bar')]"
            ])
        
        # Gibson Dunn specific structure fallbacks
        if not fallback_xpaths:
            # Try Gibson Dunn common patterns
            fallback_xpaths.extend([
                ".//*[@class and contains(@class, 'wp-block')]//text()[normalize-space()]",
                ".//div[contains(@class, 'entry-content')]//text()[normalize-space()]",
                ".//main//p//text()[normalize-space()]",
                ".//article//text()[normalize-space()]"
            ])
        
        # Generic fallbacks based on element type
        if element_type == 'link':
            fallback_xpaths.extend([
                ".//a[@href and @href != '#'][1]",
                ".//a[normalize-space(text()) and not(contains(@href, 'javascript'))]",
                ".//a[contains(@href, 'http') or starts-with(@href, '/')]"
            ])
        elif element_type == 'text':
            fallback_xpaths.extend([
                ".//*[text() and normalize-space(text()) and string-length(normalize-space(text())) > 2][1]",
                ".//text()[normalize-space() and string-length(normalize-space(.)) > 2][1]",
                ".//*[normalize-space(text())][1]"
            ])
        
        return fallback_xpaths
    
    def _extract_subpage_data(self, profile_url: str, subpage_elements: List) -> Dict[str, Any]:
        """
        Navigate to a profile subpage and extract additional data.
        
        Args:
            profile_url: URL of the profile page to visit
            subpage_elements: List of elements to extract from the subpage
            
        Returns:
            Dictionary containing extracted subpage data
        """
        subpage_data = {}
        original_url = self.current_page.url if self.current_page else None
        
        try:
            logger.debug(f"Navigating to subpage: {profile_url}")
            
            # Navigate to the profile page
            subpage = self._fetch_page(profile_url)
            if not subpage:
                logger.warning(f"Failed to fetch subpage: {profile_url}")
                return {}
            
            # Store original page reference
            original_page = self.current_page
            self.current_page = subpage
            
            # Extract data from subpage using the defined elements
            for sub_element in subpage_elements:
                try:
                    # Handle both dict and object sub-elements
                    if isinstance(sub_element, dict):
                        sub_label = sub_element.get('label')
                        sub_selector = sub_element.get('selector')
                        sub_type = sub_element.get('element_type', 'text')
                        sub_required = sub_element.get('is_required', False)
                        sub_multiple = sub_element.get('is_multiple', False)
                    else:
                        sub_label = sub_element.label
                        sub_selector = sub_element.selector
                        sub_type = sub_element.element_type
                        sub_required = getattr(sub_element, 'is_required', False)
                        sub_multiple = getattr(sub_element, 'is_multiple', False)
                    
                    if not sub_selector:
                        continue
                    
                    logger.debug(f"Extracting subpage element: {sub_label} with selector: {sub_selector}")
                    
                    # Find elements on the subpage
                    elements = []
                    try:
                        if sub_selector.startswith('xpath:'):
                            xpath_expr = sub_selector[6:]
                            elements = self.current_page.xpath(xpath_expr)
                        else:
                            elements = self.current_page.css(sub_selector, auto_match=True)
                            if not elements:
                                elements = self.current_page.css(sub_selector)
                    except Exception as selector_error:
                        logger.warning(f"Subpage selector failed for {sub_label}: {selector_error}")
                        
                        # Try fallback XPaths for known patterns
                        if any(keyword in sub_label.lower() for keyword in ['education', 'experience', 'bio', 'practice']):
                            fallback_xpaths = self._generate_fallback_xpaths(sub_label, sub_type)
                            for fallback_xpath in fallback_xpaths:
                                try:
                                    elements = self.current_page.xpath(fallback_xpath)
                                    if elements:
                                        logger.info(f"Subpage fallback XPath worked for {sub_label}: {fallback_xpath}")
                                        break
                                except Exception:
                                    continue
                    
                    if elements:
                        if sub_multiple:
                            # Extract multiple elements
                            extracted_values = []
                            for element in elements[:10]:  # Limit to first 10 to avoid too much data
                                value = self._extract_element_value(element, sub_type)
                                if value and value.strip():
                                    extracted_values.append(value.strip())
                            subpage_data[sub_label] = extracted_values
                        else:
                            # Extract single element
                            value = self._extract_element_value(elements[0], sub_type)
                            subpage_data[sub_label] = value.strip() if value else ''
                        
                        logger.debug(f"Extracted {sub_label} from subpage: {str(subpage_data[sub_label])[:100]}...")
                    
                    elif sub_required:
                        logger.warning(f"Required subpage element not found: {sub_label}")
                        subpage_data[sub_label] = None
                    else:
                        subpage_data[sub_label] = None
                        
                except Exception as element_error:
                    logger.warning(f"Error extracting subpage element {sub_label}: {element_error}")
                    subpage_data[sub_label] = None
            
            logger.info(f"Successfully extracted {len(subpage_data)} elements from subpage")
            
        except Exception as e:
            logger.error(f"Error during subpage extraction: {e}")
        
        finally:
            # Restore original page
            if original_page:
                self.current_page = original_page
                logger.debug(f"Returned to main page: {original_url}")
        
        return subpage_data
    
    def _extract_element_value(self, element, element_type: str) -> str:
        """Extract value from an element based on its type."""
        try:
            if element_type == 'text':
                return element.text if hasattr(element, 'text') else str(element)
            elif element_type == 'link':
                href = ''
                if hasattr(element, 'get_attribute'):
                    href = element.get_attribute('href') or ''
                elif hasattr(element, 'attrib'):
                    href = element.attrib.get('href', '')
                return self.current_page.urljoin(href) if href else ''
            elif element_type == 'attribute':
                # For attribute type, we'd need the attribute name, defaulting to 'value'
                attr_name = 'value'
                if hasattr(element, 'get_attribute'):
                    return element.get_attribute(attr_name) or ''
                elif hasattr(element, 'attrib'):
                    return element.attrib.get(attr_name, '')
            else:
                # Default to text
                return element.text if hasattr(element, 'text') else str(element)
        except Exception as e:
            logger.warning(f"Error extracting element value: {e}")
            return ''
    
    def _handle_filters_and_pagination(self) -> Dict[str, Any]:
        """
        Handle filter iterations and pagination for comprehensive data extraction.
        
        Returns:
            Dictionary containing all extracted data across filters and pages
        """
        all_data = {}
        
        try:
            # Check if template has filters defined
            if hasattr(self.template, 'filters') and self.template.filters:
                logger.info(f"Processing {len(self.template.filters)} filter configurations")
                all_data = self._process_with_filters()
            else:
                # No filters, process with pagination only
                all_data = self._process_with_pagination()
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error in filter/pagination handling: {e}")
            return {}
    
    def _process_with_filters(self) -> Dict[str, Any]:
        """
        Process scraping with filter iterations.
        
        Returns:
            Dictionary containing data from all filter combinations
        """
        all_filter_data = {}
        
        try:
            # Generate all filter combinations
            filter_combinations = self._generate_filter_combinations()
            
            for i, filter_combo in enumerate(filter_combinations):
                logger.info(f"Processing filter combination {i+1}/{len(filter_combinations)}: {filter_combo}")
                
                # Apply filters
                self._apply_filters(filter_combo)
                
                # Wait for content to load
                time.sleep(2)
                
                # Process pagination for this filter combination
                filter_data = self._process_with_pagination()
                
                # Store data with filter context
                filter_key = '_'.join([f"{f['label']}_{f['value']}" for f in filter_combo])
                all_filter_data[filter_key] = filter_data
                
                # Add delay between filter combinations
                time.sleep(1)
            
            return all_filter_data
            
        except Exception as e:
            logger.error(f"Error processing filters: {e}")
            return {}
    
    def _generate_filter_combinations(self) -> List[List[Dict[str, str]]]:
        """
        Generate all possible filter combinations.
        
        Returns:
            List of filter combinations
        """
        import itertools
        
        filter_options = []
        
        for filter_config in self.template.filters:
            if filter_config.filter_values:
                filter_options.append([
                    {'label': filter_config.filter_label, 'selector': filter_config.filter_selector, 'value': value}
                    for value in filter_config.filter_values
                ])
        
        # Generate cartesian product of all filter options
        if filter_options:
            return [list(combo) for combo in itertools.product(*filter_options)]
        else:
            return [[]]
    
    def _apply_filters(self, filter_combo: List[Dict[str, str]]) -> None:
        """
        Apply a combination of filters to the page.
        
        Args:
            filter_combo: List of filter configurations to apply
        """
        for filter_item in filter_combo:
            try:
                # This is a simplified implementation - in practice, you'd need
                # to interact with the actual browser through Playwright
                logger.info(f"Would apply filter: {filter_item['label']} = {filter_item['value']}")
                
                # For Scrapling, we would need to implement actual filter interaction
                # This might require switching to PlaywrightFetcher for interactive capabilities
                
            except Exception as e:
                logger.warning(f"Error applying filter {filter_item['label']}: {e}")
    
    def _process_with_pagination(self) -> Dict[str, Any]:
        """
        Process scraping with pagination support.
        
        Returns:
            Dictionary containing data from all pages
        """
        all_containers_data = {}
        page_number = 1
        
        try:
            while True:
                logger.info(f"Processing page {page_number}")
                
                # Extract data from current page
                page_data = self._extract_data()
                
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
                
                # Handle load more buttons or pagination
                more_content_loaded = False
                if hasattr(self.template, 'pagination') and self.template.pagination:
                    if self.template.pagination.pattern_type == 'load_more':
                        more_content_loaded = self._handle_load_more_pagination()
                    else:
                        more_content_loaded = self._handle_pagination()
                    
                    if not more_content_loaded:
                        break
                else:
                    # No pagination configured, just process current page
                    break
                
                page_number += 1
                
                # Safety check to prevent infinite loops
                if hasattr(self.template.pagination, 'max_pages') and self.template.pagination.max_pages:
                    if page_number > self.template.pagination.max_pages:
                        break
                        
                # Add delay between pagination requests
                if hasattr(self.template.pagination, 'scroll_pause_time'):
                    time.sleep(self.template.pagination.scroll_pause_time)
                else:
                    time.sleep(2)
        
            logger.info(f"Completed pagination processing. Total pages: {page_number}")
            return all_containers_data
            
        except Exception as e:
            logger.error(f"Error in pagination processing: {e}")
            return all_containers_data
    
    def _handle_pagination(self) -> bool:
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
                    # For Scrapling, we can't actually click, but we can detect the pattern
                    logger.info("Next button detected - would navigate to next page")
                    return True
                
            elif pagination.pattern_type == 'infinite_scroll':
                # Handle infinite scroll
                return self._handle_infinite_scroll()
                
            elif pagination.pattern_type == 'load_more':
                return self._handle_load_more_pagination()
            
            return False
            
        except Exception as e:
            logger.warning(f"Error handling pagination: {e}")
            return False
    
    def _handle_infinite_scroll(self) -> bool:
        """
        Handle infinite scroll scenarios.
        
        Returns:
            True if more content available, False otherwise
        """
        try:
            # For Scrapling, we can't actually scroll, but we can implement
            # detection logic for content changes
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
    
    def _handle_load_more_pagination(self) -> bool:
        """
        Handle load more button pagination using Scrapling's page_action.
        
        Returns:
            True if more content was loaded, False if no more content
        """
        try:
            pagination = self.template.pagination
            
            if not pagination.load_more_selector:
                return False
            
            # Ensure we're on the correct page (listing page, not individual profile page)
            if 'lawyer/' in self.current_page.url or '/people/' not in self.current_page.url:
                logger.warning(f"Not on listing page (current: {self.current_page.url}), navigating back to listing page")
                # Navigate back to the main listing page
                listing_page = self._fetch_page(self.template.url)
                if listing_page:
                    self.current_page = listing_page
                else:
                    logger.error("Failed to navigate back to listing page")
                    return False
            
            # Check if load more button exists on current page
            load_more_buttons = self.current_page.css(pagination.load_more_selector)
            if not load_more_buttons:
                logger.info("Load more button not found - end of content")
                return False
            
            logger.info(f"Clicking load more button: {pagination.load_more_selector}")
            
            # Define the page action to click load more button
            def click_load_more(page):
                try:
                    # Ensure we're on the right page
                    if 'lawyer/' in page.url:
                        logger.warning("Attempted to click load more on individual lawyer page - aborting")
                        return page
                    
                    # Check if button exists and is visible
                    button_locator = page.locator(pagination.load_more_selector)
                    if button_locator.count() == 0:
                        logger.info("Load more button not found during action")
                        return page
                    
                    if not button_locator.is_visible():
                        logger.info("Load more button not visible during action")
                        return page
                    
                    # Scroll to button first to ensure it's in viewport
                    button_locator.scroll_into_view_if_needed()
                    
                    # Click the button
                    button_locator.click()
                    logger.info("Load more button clicked successfully")
                    
                    # Wait for new content to load
                    wait_time = pagination.scroll_pause_time if pagination.scroll_pause_time else 3
                    page.wait_for_timeout(wait_time * 1000)  # Convert to milliseconds
                    
                    # Wait for network to be idle (new content loaded)
                    page.wait_for_load_state('networkidle', timeout=10000)
                    
                    return page
                    
                except Exception as action_error:
                    logger.warning(f"Error in page action: {action_error}")
                    return page
            
            # Fetch the listing page with the load more action
            try:
                fetch_options = {
                    'headless': self.template.headless,
                    'network_idle': True,
                    'timeout': self.template.wait_timeout * 1000,
                    'page_action': click_load_more
                }
                
                # Always use the main listing URL, not the current page URL
                listing_url = self.template.url
                updated_page = self.fetcher.fetch(listing_url, **fetch_options)
                
                if updated_page and updated_page.status == 200:
                    self.current_page = updated_page
                    logger.info("Page successfully updated after load more click")
                    return True
                else:
                    logger.warning("Failed to fetch updated page after load more click")
                    return False
                    
            except Exception as fetch_error:
                logger.warning(f"Error fetching page with load more action: {fetch_error}")
                return False
            
        except Exception as e:
            logger.warning(f"Error in load more handling: {e}")
            return False
    
    def _flatten_paginated_data(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Flatten paginated data into a single list.
        
        Args:
            pages_data: List of page data dictionaries
            
        Returns:
            Flattened list of all data items
        """
        flattened = []
        
        for page in pages_data:
            page_data = page.get('data', {})
            
            # Find container data (lists of items)
            for key, value in page_data.items():
                if isinstance(value, list) and value:
                    # If it's a list of dictionaries (container data), extend the flattened list
                    if isinstance(value[0], dict):
                        for item in value:
                            item['_source_page'] = page['page_number']
                            flattened.append(item)
                    else:
                        # Simple list values
                        for item in value:
                            flattened.append({
                                key: item,
                                '_source_page': page['page_number']
                            })
        
        return flattened
    
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
    
    def _process_intelligent_sublinks(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently detect and process sub-links for additional data extraction.
        
        This method:
        1. Detects when profile links are extracted from directory pages
        2. Identifies containers that likely need subpage data (education, credentials)
        3. Automatically follows links to extract additional data
        4. Uses optimized extraction for better performance
        
        Args:
            scraped_data: Main page scraped data
            
        Returns:
            Enhanced data with subpage information
        """
        enhanced_data = scraped_data.copy()
        
        try:
            # Check for containers with profile links that need subpage data
            subpage_containers = self._detect_subpage_containers(enhanced_data)
            
            if not subpage_containers:
                logger.info("No containers detected as needing subpage data")
                return enhanced_data
            
            # Process each container that needs subpage data
            for main_container, subpage_container, profile_urls in subpage_containers:
                logger.info(f"Processing intelligent sublinks: {main_container.label} -> {subpage_container.label} ({len(profile_urls)} URLs)")
                
                # Extract subpage data using the discovered profile URLs
                subpage_data = self._extract_subpage_data_from_urls(profile_urls, subpage_container)
                
                # Merge the subpage data back into main data
                enhanced_data = self._merge_subpage_data_into_main(
                    enhanced_data, main_container.label, subpage_data
                )
                
                # Remove the separate subpage container from results to avoid duplication
                if subpage_container.label in enhanced_data:
                    del enhanced_data[subpage_container.label]
                    
        except Exception as e:
            logger.error(f"Error in intelligent sublink processing: {e}")
            # Continue with original data if sublink processing fails
        
        return enhanced_data
    
    def _should_use_dual_engine_mode(self) -> bool:
        """
        Determine if dual-engine mode should be used for sublink processing.
        
        Dual-engine mode is used when:
        1. Template has sublink containers that failed on main page
        2. Template has actions with target URLs (indicating navigation)
        3. Expected data volume is high (>10 expected profiles)
        
        Returns:
            True if dual-engine mode should be used
        """
        # Check for sublink containers
        has_sublink_containers = any(
            hasattr(elem, 'is_container') and elem.is_container and 
            elem.label.lower() in ['sublink', 'subcon', 'subpage']
            for elem in self.template.elements
        )
        
        # Check for actions with target URLs
        has_action_urls = any(
            hasattr(action, 'target_url') and action.target_url and action.action_type == 'click'
            for action in self.template.actions if hasattr(self.template, 'actions')
        )
        
        # Check if this looks like a large-scale directory scraping operation
        looks_like_large_directory = self._looks_like_directory_template()
        
        should_use_dual = has_sublink_containers or (has_action_urls and looks_like_large_directory)
        
        if should_use_dual:
            logger.info(f"Dual-engine mode enabled: sublink_containers={has_sublink_containers}, action_urls={has_action_urls}, large_directory={looks_like_large_directory}")
        else:
            logger.info("Using single-engine mode for sublink processing")
        
        return should_use_dual
    
    def _process_dual_engine_sublinks(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sublinks using dual-engine architecture for improved performance.
        
        Engine 1 (Directory): Already completed - scraped main directory data
        Engine 2 (Sublinks): Parallel processing of individual profile pages
        
        Args:
            scraped_data: Main page scraped data from Engine 1
            
        Returns:
            Enhanced data with subpage information from Engine 2
        """
        logger.info("Starting dual-engine sublink processing")
        enhanced_data = scraped_data.copy()
        
        try:
            # Step 1: Detect subpage containers and profile URLs (Engine 1 analysis)
            subpage_containers = self._detect_subpage_containers_dual_engine(enhanced_data)
            
            if not subpage_containers:
                logger.info("No containers detected for dual-engine sublink processing")
                return enhanced_data
            
            # Step 2: Extract all profile URLs and prepare for parallel processing
            all_profile_urls = []
            container_mapping = {}
            
            for main_container, subpage_container, profile_urls in subpage_containers:
                all_profile_urls.extend(profile_urls)
                container_mapping[main_container.label] = {
                    'subpage_container': subpage_container,
                    'profile_urls': profile_urls
                }
                logger.info(f"Prepared {len(profile_urls)} URLs for dual-engine processing: {main_container.label} -> {subpage_container.label}")
            
            # Step 3: Launch Engine 2 - Parallel sublink processing
            logger.info(f"Launching Engine 2 for parallel processing of {len(all_profile_urls)} profile pages")
            subpage_results = self._execute_engine_2_parallel_sublinks(
                all_profile_urls, 
                list(container_mapping.values())
            )
            
            # Step 4: Merge results back into main data
            for main_label, mapping in container_mapping.items():
                subpage_container = mapping['subpage_container']
                profile_urls = mapping['profile_urls']
                
                # Filter subpage results for this container
                container_subpage_data = {
                    url: data for url, data in subpage_results.items() 
                    if url in profile_urls
                }
                
                # Merge into main data
                enhanced_data = self._merge_subpage_data_into_main(
                    enhanced_data, main_label, container_subpage_data
                )
                
                # Remove separate subpage container to avoid duplication
                if subpage_container.label in enhanced_data:
                    del enhanced_data[subpage_container.label]
            
            logger.info(f"Dual-engine sublink processing completed successfully")
            
        except Exception as e:
            logger.error(f"Error in dual-engine sublink processing: {e}")
            # Fallback to single-engine mode
            logger.info("Falling back to single-engine sublink processing")
            enhanced_data = self._process_intelligent_sublinks(scraped_data)
        
        return enhanced_data
    
    def _detect_subpage_containers_dual_engine(self, scraped_data: Dict[str, Any]) -> List[tuple]:
        """
        Enhanced subpage container detection for dual-engine mode.
        
        This version also considers action URLs for profile link discovery.
        
        Args:
            scraped_data: The scraped data to analyze
            
        Returns:
            List of tuples (main_container, subpage_container, profile_urls)
        """
        container_pairs = []
        
        logger.info("Analyzing scraped data for dual-engine subpage detection")
        
        # Analyze each container in the scraped data
        containers_with_links = []
        containers_with_failed_selectors = []
        
        for element in self.template.elements:
            if not (hasattr(element, 'is_container') and element.is_container):
                continue
                
            container_data = scraped_data.get(element.label, [])
            if not isinstance(container_data, list) or not container_data:
                continue
            
            logger.debug(f"Analyzing container '{element.label}' with {len(container_data)} items")
            
            # Check if this container has HTTP URLs (potential profile links)
            profile_urls = self._extract_profile_urls_from_container(container_data)
            
            # Enhanced URL extraction: also check action URLs
            if not profile_urls and hasattr(self.template, 'actions'):
                profile_urls = self._extract_urls_from_actions()
            
            if profile_urls:
                containers_with_links.append((element, profile_urls))
                logger.info(f"Container '{element.label}' has {len(profile_urls)} profile URLs")
            
            # Check if this container has selectors that found no meaningful data
            if self._container_has_failed_selectors(element, container_data):
                containers_with_failed_selectors.append(element)
                logger.info(f"Container '{element.label}' has selectors that failed on main page")
        
        # Pair containers with links + containers with failed selectors
        for main_container, profile_urls in containers_with_links:
            for subpage_container in containers_with_failed_selectors:
                if main_container.label != subpage_container.label:  # Don't pair with self
                    container_pairs.append((main_container, subpage_container, profile_urls))
                    logger.info(f"Detected dual-engine subpage pair: {main_container.label} -> {subpage_container.label} ({len(profile_urls)} URLs)")
        
        logger.info(f"Found {len(container_pairs)} container pairs for dual-engine subpage processing")
        return container_pairs
    
    def _extract_urls_from_actions(self) -> List[str]:
        """
        Extract profile URLs from template actions.
        
        Returns:
            List of profile URLs from action target_urls
        """
        urls = []
        
        if not hasattr(self.template, 'actions'):
            return urls
        
        for action in self.template.actions:
            if (hasattr(action, 'target_url') and action.target_url and 
                action.action_type == 'click' and '/lawyer/' in action.target_url):
                urls.append(action.target_url)
                logger.debug(f"Found action URL: {action.target_url}")
        
        return urls
    
    def _execute_engine_2_parallel_sublinks(self, profile_urls: List[str], container_mappings: List[Dict]) -> Dict[str, Dict]:
        """
        Execute Engine 2: Parallel processing of profile pages for sublink data extraction.
        
        Args:
            profile_urls: List of all profile URLs to process
            container_mappings: List of container mapping configurations
            
        Returns:
            Dictionary mapping profile URLs to extracted subpage data
        """
        logger.info(f"Engine 2 starting parallel processing of {len(profile_urls)} profile pages")
        
        # Determine optimal concurrency level (max 5 concurrent requests to be respectful)
        max_workers = min(5, len(profile_urls))
        
        all_subpage_results = {}
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all profile page processing tasks
            future_to_url = {}
            
            for profile_url in profile_urls:
                # Find the appropriate subpage container for this URL
                subpage_container = None
                for mapping in container_mappings:
                    if profile_url in mapping['profile_urls']:
                        subpage_container = mapping['subpage_container']
                        break
                
                if subpage_container:
                    future = executor.submit(
                        self._extract_single_profile_data_engine_2, 
                        profile_url, 
                        subpage_container
                    )
                    future_to_url[future] = profile_url
                else:
                    logger.warning(f"No subpage container found for URL: {profile_url}")
            
            # Collect results as they complete
            completed_count = 0
            for future in as_completed(future_to_url):
                profile_url = future_to_url[future]
                completed_count += 1
                
                try:
                    subpage_data = future.result(timeout=30)  # 30 second timeout per page
                    if subpage_data:
                        all_subpage_results[profile_url] = subpage_data
                        logger.info(f"Engine 2 [{completed_count}/{len(profile_urls)}] extracted data from {profile_url}: {list(subpage_data.keys())}")
                    else:
                        logger.debug(f"Engine 2 [{completed_count}/{len(profile_urls)}] no data from {profile_url}")
                        
                except Exception as e:
                    logger.warning(f"Engine 2 [{completed_count}/{len(profile_urls)}] failed for {profile_url}: {e}")
                    continue
        
        logger.info(f"Engine 2 completed: Successfully extracted data from {len(all_subpage_results)} out of {len(profile_urls)} profile pages")
        return all_subpage_results
    
    def _extract_single_profile_data_engine_2(self, profile_url: str, subpage_container) -> Dict[str, Any]:
        """
        Extract data from a single profile page using Engine 2 (dedicated Scrapling instance).
        
        Args:
            profile_url: URL of the profile page to process
            subpage_container: Container configuration for subpage data extraction
            
        Returns:
            Dictionary containing extracted subpage data
        """
        page_data = {}
        
        try:
            # Create a dedicated fetcher instance for this profile page
            profile_fetcher = PlayWrightFetcher
            
            # Fetch the profile page
            fetch_options = {
                'headless': self.template.headless,
                'network_idle': True,
                'timeout': self.template.wait_timeout * 1000
            }
            
            profile_page = profile_fetcher.fetch(profile_url, **fetch_options)
            
            if not profile_page or profile_page.status != 200:
                logger.warning(f"Engine 2 failed to fetch profile page: {profile_url} (status: {profile_page.status if profile_page else 'None'})")
                return page_data
            
            # Extract subpage data using the subpage container configuration
            if hasattr(subpage_container, 'sub_elements') and subpage_container.sub_elements:
                for sub_element in subpage_container.sub_elements:
                    try:
                        # Get sub-element configuration
                        if hasattr(sub_element, 'label'):
                            sub_label = sub_element.label
                            sub_selector = sub_element.selector
                        else:
                            sub_label = sub_element.get('label', '')
                            sub_selector = sub_element.get('selector', '')
                        
                        if sub_selector:
                            # Use XPath if specified, otherwise CSS
                            if sub_selector.startswith('xpath:'):
                                xpath_selector = sub_selector[6:]  # Remove 'xpath:' prefix
                                elements = profile_page.xpath(xpath_selector)
                            else:
                                elements = profile_page.css(sub_selector)
                            
                            if elements:
                                # Extract text from first matching element
                                extracted_value = elements[0].text.strip() if elements[0].text else None
                                if extracted_value and extracted_value.lower() != 'none':
                                    page_data[sub_label] = extracted_value
                                    logger.debug(f"Engine 2 extracted {sub_label}: {extracted_value[:50]}...")
                            else:
                                logger.debug(f"Engine 2 found no elements for {sub_label} with selector: {sub_selector}")
                                
                    except Exception as e:
                        logger.warning(f"Engine 2 failed to extract {sub_label} from {profile_url}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Engine 2 error processing {profile_url}: {e}")
        
        return page_data
    
    def _detect_subpage_containers(self, scraped_data: Dict[str, Any]) -> List[tuple]:
        """
        Detect containers that need subpage data extraction based on actual scraped data.
        
        This is a robust, generic approach that works across different sites by analyzing
        the actual data structure rather than hardcoding assumptions.
        
        NOTE: This is the original single-engine method. For dual-engine mode,
        use _detect_subpage_containers_dual_engine instead.
        
        Args:
            scraped_data: The scraped data to analyze
            
        Returns:
            List of tuples (main_container, subpage_container, profile_urls) where:
            - main_container: Container element that has profile links in scraped data
            - subpage_container: Container element with selectors that failed on main page
            - profile_urls: List of profile URLs found in main container data
        """
        container_pairs = []
        
        logger.info(f"Analyzing scraped data for intelligent subpage detection")
        
        # Analyze each container in the scraped data
        containers_with_links = []
        containers_with_failed_selectors = []
        
        for element in self.template.elements:
            if not (hasattr(element, 'is_container') and element.is_container):
                continue
                
            container_data = scraped_data.get(element.label, [])
            if not isinstance(container_data, list) or not container_data:
                continue
            
            logger.debug(f"Analyzing container '{element.label}' with {len(container_data)} items")
            
            # Check if this container has HTTP URLs (potential profile links)
            profile_urls = self._extract_profile_urls_from_container(container_data)
            if profile_urls:
                containers_with_links.append((element, profile_urls))
                logger.info(f"Container '{element.label}' has {len(profile_urls)} profile URLs")
            
            # Check if this container has selectors that found no meaningful data
            # (indicating they might work better on subpages)
            if self._container_has_failed_selectors(element, container_data):
                containers_with_failed_selectors.append(element)
                logger.info(f"Container '{element.label}' has selectors that failed on main page")
        
        # Pair containers with links + containers with failed selectors
        for main_container, profile_urls in containers_with_links:
            for subpage_container in containers_with_failed_selectors:
                if main_container.label != subpage_container.label:  # Don't pair with self
                    container_pairs.append((main_container, subpage_container, profile_urls))
                    logger.info(f"Detected subpage pair: {main_container.label} -> {subpage_container.label} ({len(profile_urls)} URLs)")
        
        logger.info(f"Found {len(container_pairs)} container pairs for subpage processing")
        return container_pairs
    
    def _extract_profile_urls_from_container(self, container_data: List[Dict]) -> List[str]:
        """
        Extract HTTP URLs from container data that could be profile links.
        
        Args:
            container_data: List of dictionaries from a container
            
        Returns:
            List of unique HTTP URLs found in the data
        """
        urls = set()
        
        for item in container_data:
            if not isinstance(item, dict):
                continue
                
            for key, value in item.items():
                if isinstance(value, str) and value.startswith('http'):
                    # Filter out obvious non-profile URLs
                    if not any(skip in value.lower() for skip in ['mailto:', 'tel:', 'javascript:', '#']):
                        urls.add(value)
        
        return list(urls)
    
    def _container_has_failed_selectors(self, element, container_data: List[Dict]) -> bool:
        """
        Check if a container has selectors that consistently failed to find meaningful data.
        
        This indicates the selectors might work better on individual subpages.
        
        Args:
            element: Container element configuration
            container_data: Scraped data from this container
            
        Returns:
            True if container has selectors that failed on main page
        """
        if not hasattr(element, 'sub_elements') or not element.sub_elements:
            return False
        
        # If container data is empty, all selectors failed
        if not container_data:
            return True
        
        # Check if most items have empty/None values for most fields
        total_fields = 0
        empty_fields = 0
        
        for item in container_data:
            if not isinstance(item, dict):
                continue
                
            for key, value in item.items():
                if not key.startswith('_'):  # Skip internal fields
                    total_fields += 1
                    if value is None or value == '' or value == 'None':
                        empty_fields += 1
        
        # If more than 70% of fields are empty, consider selectors as failed
        if total_fields > 0:
            failure_rate = empty_fields / total_fields
            logger.debug(f"Container '{element.label}' has {failure_rate:.2%} empty fields")
            return failure_rate > 0.7
        
        return False
    
    def _extract_subpage_data_from_urls(self, profile_urls: List[str], subpage_container) -> Dict[str, Dict]:
        """
        Extract subpage data from a list of profile URLs.
        
        Args:
            profile_urls: List of profile URLs to extract data from
            subpage_container: Container configuration for subpage data
            
        Returns:
            Dictionary mapping profile URLs to extracted subpage data
        """
        subpage_results = {}
        
        if not profile_urls:
            logger.warning("No profile URLs provided for subpage extraction")
            return subpage_results
        
        logger.info(f"Extracting subpage data from {len(profile_urls)} profile pages")
        
        # Process each profile URL
        for i, profile_url in enumerate(profile_urls):
            try:
                logger.debug(f"Processing profile {i+1}/{len(profile_urls)}: {profile_url}")
                
                # Fetch the profile page
                profile_page = self._fetch_page(profile_url)
                if not profile_page:
                    logger.warning(f"Failed to fetch profile page: {profile_url}")
                    continue
                
                # Temporarily switch context to profile page
                original_page = self.current_page
                self.current_page = profile_page
                
                # Extract subpage data using the subpage container configuration
                page_data = {}
                if hasattr(subpage_container, 'sub_elements') and subpage_container.sub_elements:
                    for sub_element in subpage_container.sub_elements:
                        try:
                            # Extract using the sub-element selector on the profile page
                            sub_label = getattr(sub_element, 'label', '') if hasattr(sub_element, 'label') else sub_element.get('label', '')
                            sub_selector = getattr(sub_element, 'selector', '') if hasattr(sub_element, 'selector') else sub_element.get('selector', '')
                            
                            if sub_selector:
                                # Use XPath if specified, otherwise CSS
                                if sub_selector.startswith('xpath:'):
                                    xpath_selector = sub_selector[6:]  # Remove 'xpath:' prefix
                                    elements = profile_page.xpath(xpath_selector)
                                else:
                                    elements = profile_page.css(sub_selector)
                                
                                logger.debug(f"Selector '{sub_selector}' found {len(elements)} elements on {profile_url}")
                                
                                if elements:
                                    # Extract text from first matching element
                                    extracted_value = elements[0].text.strip() if elements[0].text else None
                                    if extracted_value and extracted_value.lower() != 'none':
                                        page_data[sub_label] = extracted_value
                                        logger.info(f"Extracted {sub_label}: {extracted_value[:50]}...")
                                    else:
                                        logger.debug(f"Element found but no meaningful text content for {sub_label}: '{extracted_value}'")
                                else:
                                    logger.debug(f"No elements found for {sub_label} with selector: {sub_selector}")
                                
                        except Exception as e:
                            logger.warning(f"Failed to extract {sub_label} from {profile_url}: {e}")
                            continue
                
                # Store the extracted data
                if page_data:
                    subpage_results[profile_url] = page_data
                    logger.info(f"Successfully extracted {len(page_data)} fields from {profile_url}: {list(page_data.keys())}")
                else:
                    logger.debug(f"No meaningful data extracted from {profile_url}")
                
                # Restore original page context
                self.current_page = original_page
                
                # Add delay between requests to be respectful
                if i < len(profile_urls) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error processing profile URL {profile_url}: {e}")
                continue
        
        logger.info(f"Successfully extracted subpage data from {len(subpage_results)} profile pages")
        logger.info(f"Subpage results keys: {list(subpage_results.keys())[:3]}...")  # Show first 3 URLs
        logger.info(f"Sample subpage data: {list(subpage_results.values())[:1] if subpage_results else 'None'}")
        return subpage_results
    
    def _extract_subpage_data_optimized(self, main_data: List[Dict], subpage_container) -> Dict[str, Dict]:
        """
        Extract subpage data using optimized approach to avoid repeated directory loading.
        
        Args:
            main_data: List of main container items with profile links
            subpage_container: Container configuration for subpage data
            
        Returns:
            Dictionary mapping profile URLs to extracted subpage data
        """
        subpage_results = {}
        
        # Extract profile URLs from main data
        profile_urls = []
        for item in main_data:
            # Look for profile link fields
            for key, value in item.items():
                if ('profile' in key.lower() or 'link' in key.lower()) and isinstance(value, str) and value.startswith('http'):
                    profile_urls.append(value)
                    break
        
        if not profile_urls:
            logger.warning("No profile URLs found in main data")
            return subpage_results
        
        logger.info(f"Extracting subpage data from {len(profile_urls)} profile pages")
        
        # Process each profile URL
        for i, profile_url in enumerate(profile_urls):
            try:
                logger.debug(f"Processing profile {i+1}/{len(profile_urls)}: {profile_url}")
                
                # Fetch the profile page
                profile_page = self._fetch_page(profile_url)
                if not profile_page:
                    logger.warning(f"Failed to fetch profile page: {profile_url}")
                    continue
                
                # Temporarily switch context to profile page
                original_page = self.current_page
                self.current_page = profile_page
                
                # Extract subpage data using the subpage container configuration
                page_data = {}
                if hasattr(subpage_container, 'sub_elements') and subpage_container.sub_elements:
                    for sub_element in subpage_container.sub_elements:
                        try:
                            # Extract using the sub-element selector on the profile page
                            sub_label = getattr(sub_element, 'label', '') if hasattr(sub_element, 'label') else sub_element.get('label', '')
                            sub_selector = getattr(sub_element, 'selector', '') if hasattr(sub_element, 'selector') else sub_element.get('selector', '')
                            
                            if sub_selector:
                                # Use XPath if specified, otherwise CSS
                                if sub_selector.startswith('xpath:'):
                                    xpath_selector = sub_selector[6:]  # Remove 'xpath:' prefix
                                    elements = profile_page.xpath(xpath_selector)
                                else:
                                    elements = profile_page.css(sub_selector)
                                
                                logger.debug(f"Selector '{sub_selector}' found {len(elements)} elements on {profile_url}")
                                
                                if elements:
                                    # Extract text from first matching element
                                    extracted_value = elements[0].text.strip() if elements[0].text else None
                                    if extracted_value and extracted_value.lower() != 'none':
                                        page_data[sub_label] = extracted_value
                                        logger.info(f"Extracted {sub_label}: {extracted_value[:50]}...")
                                    else:
                                        logger.debug(f"Element found but no meaningful text content for {sub_label}: '{extracted_value}'")
                                else:
                                    logger.debug(f"No elements found for {sub_label} with selector: {sub_selector}")
                                
                        except Exception as e:
                            logger.warning(f"Failed to extract {sub_label} from {profile_url}: {e}")
                            continue
                
                # Store the extracted data
                if page_data:
                    subpage_results[profile_url] = page_data
                    logger.info(f"Successfully extracted {len(page_data)} fields from {profile_url}: {list(page_data.keys())}")
                else:
                    logger.debug(f"No meaningful data extracted from {profile_url}")
                
                # Restore original page context
                self.current_page = original_page
                
                # Add delay between requests to be respectful
                if i < len(profile_urls) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error processing profile URL {profile_url}: {e}")
                continue
        
        logger.info(f"Successfully extracted subpage data from {len(subpage_results)} profile pages")
        logger.info(f"Subpage results keys: {list(subpage_results.keys())[:3]}...")  # Show first 3 URLs
        logger.info(f"Sample subpage data: {list(subpage_results.values())[:1] if subpage_results else 'None'}")
        return subpage_results
    
    def _merge_subpage_data_into_main(self, enhanced_data: Dict, main_label: str, subpage_data: Dict) -> Dict:
        """
        Merge subpage data back into main container data.
        
        Args:
            enhanced_data: Current enhanced data
            main_label: Label of the main container
            subpage_data: Dictionary mapping profile URLs to extracted data
            
        Returns:
            Enhanced data with subpage information merged in
        """
        if main_label not in enhanced_data:
            return enhanced_data
        
        main_items = enhanced_data[main_label]
        if not isinstance(main_items, list):
            return enhanced_data
        
        # Merge subpage data into corresponding main items
        merge_count = 0
        for item in main_items:
            # Find the profile URL for this item
            profile_url = None
            for key, value in item.items():
                if ('profile' in key.lower() or 'link' in key.lower()) and isinstance(value, str) and value.startswith('http'):
                    profile_url = value
                    break
            
            # If we have subpage data for this profile URL, merge it
            if profile_url and profile_url in subpage_data:
                item.update(subpage_data[profile_url])
                merge_count += 1
                logger.info(f"Merged subpage data for: {profile_url} - {list(subpage_data[profile_url].keys())}")
        
        logger.info(f"Merged subpage data into {merge_count} out of {len(main_items)} main items")
        return enhanced_data


class BatchScraplingRunner:
    """
    Handles batch processing of multiple URLs using a single template.
    """
    
    def __init__(self, template: ScrapingTemplate):
        self.template = template
    
    def execute_batch(self, urls: List[str]) -> List[ScrapingResult]:
        """
        Execute scraping for multiple URLs using the same template.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of ScrapingResult objects
        """
        results = []
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")
                
                # Create a copy of the template with the new URL
                url_template = self.template.model_copy()
                url_template.url = url
                
                # Execute scraping
                runner = ScraplingRunner(url_template)
                result = runner.execute_scraping()
                results.append(result)
                
                # Add delay between requests to be respectful
                if i < len(urls) - 1:  # Don't wait after the last URL
                    time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to process URL {url}: {e}")
                
                # Create a failure result
                error_result = ScrapingResult(
                    template_name=self.template.name,
                    url=url,
                    success=False,
                    errors=[str(e)]
                )
                results.append(error_result)
        
        return results