#!/usr/bin/env python3
"""
Subpage processing for automated scraping with navigation and data extraction.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from ..context import ScrapingContext

logger = logging.getLogger(__name__)


class SubpageProcessor:
    """
    Handles all subpage processing functionality including navigation, 
    data extraction, and merging operations.
    """
    
    def __init__(self, context: ScrapingContext, fetcher_instance=None, sublink_engine=None):
        """
        Initialize the SubpageProcessor.
        
        Args:
            context: ScrapingContext instance
            fetcher_instance: Main browser instance (optional)
            sublink_engine: Dedicated sublink browser engine (optional)
        """
        self.context = context
        self.template = context.template
        self.current_page = context.current_page
        self.fetcher = context.fetcher
        self.fetcher_instance = fetcher_instance
        self.sublink_engine = sublink_engine
        self.sublink_queue = []
        self.processed_sublinks = []
        self.sublink_context = None
        self.sublink_page = None
    
    def process_subpage_extractions(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
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
                    enhanced_data = self.extract_subpage_data(element, enhanced_data)
        
        return enhanced_data
    
    def extract_subpage_container_data(self, profile_url: str, element_config) -> Dict[str, Any]:
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
            subpage = self.fetch_page(profile_url)
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
                        sub_element_dict = {
                            'label': sub_label,
                            'selector': sub_selector,
                            'element_type': sub_type
                        } if not isinstance(sub_element, dict) else sub_element
                        
                        enhanced_selector = self.map_generic_selector(sub_element_dict, "profile")
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
                                # Multiple text elements - extract as list, skip empty/None values
                                text_values = []
                                for elem in elements:
                                    text_content = elem.text if hasattr(elem, 'text') else str(elem)
                                    if text_content and text_content.strip() and text_content.strip().lower() != 'none':
                                        text_values.append(text_content.strip())
                                # Only set if we have actual values
                                if text_values:
                                    subpage_data[sub_label] = text_values
                                else:
                                    logger.debug(f"No valid text content found for {sub_label}")
                            elif elements:
                                # Single element or first element
                                text_content = elements[0].text if hasattr(elements[0], 'text') else str(elements[0])
                                if text_content and text_content.strip() and text_content.strip().lower() != 'none':
                                    subpage_data[sub_label] = text_content.strip()
                                else:
                                    logger.debug(f"No valid text content found for {sub_label}")
                        else:
                            logger.debug(f"No elements found for subpage {sub_label} with selector {sub_selector}")
                            
                    except Exception as e:
                        logger.warning(f"Error extracting subpage element {sub_label}: {e}")
            
            logger.info(f"Successfully extracted {len(subpage_data)} elements from subpage")
            
        except Exception as e:
            logger.error(f"Error during subpage container extraction: {e}")
        
        finally:
            # Restore original page context
            if original_page:
                self.current_page = original_page
        
        return subpage_data
    
    def extract_subpage_container_data_from_main_containers(self, element_config) -> List[Dict[str, Any]]:
        """
        Extract subpage container data by using profile links from main containers.
        
        Args:
            element_config: Subpage container configuration
            
        Returns:
            List of dictionaries containing extracted subpage data
        """
        containers = []
        
        try:
            logger.info(f"Subpage container '{element_config.label}' detected - extracting from individual pages")
            
            # Find main containers that should have profile links
            main_container_elements = self.get_main_container_elements_for_subpage()
            
            if not main_container_elements:
                logger.warning("No main containers found for subpage extraction")
                return []
            
            logger.info(f"Found {len(main_container_elements)} main containers for subpage extraction")
            
            # Process each main container to extract profile links and then subpage data
            for i, container in enumerate(main_container_elements):
                try:
                    # Find profile link in this container
                    profile_link = None
                    
                    # Try to find any link within the container that points to a profile page
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
                    
                    # Extract subpage data from the individual profile page
                    logger.info(f"Extracting subpage data from: {profile_link}")
                    subpage_data = self.extract_subpage_container_data(profile_link, element_config)
                    
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
    
    def extract_subpage_container_data_incremental(self, element_config, existing_count: int) -> List[Dict[str, Any]]:
        """
        Extract subpage container data incrementally, processing only containers beyond the existing count.
        
        Args:
            element_config: The element configuration for the subpage container
            existing_count: Number of containers already processed
            
        Returns:
            List of newly extracted container data
        """
        try:
            # First, get all main containers
            main_container_elements = self.get_main_container_elements_for_subpage()
            
            if not main_container_elements:
                logger.warning("No main containers found for incremental subpage extraction")
                return []
            
            total_containers = len(main_container_elements)
            logger.debug(f"Incremental subpage extraction: found {total_containers} total containers, already processed {existing_count}")
            
            if existing_count >= total_containers:
                logger.debug("All containers already processed - no new data")
                return []
            
            # Process only NEW containers (starting from existing_count index)
            new_containers = []
            for i in range(existing_count, total_containers):
                container = main_container_elements[i]
                
                try:
                    # Find profile link in this container
                    profile_link = None
                    
                    # Try to find any link within the container that points to a profile page
                    lawyer_links = container.css("a[href*='/lawyer/']")
                    if not lawyer_links:
                        lawyer_links = container.css("a")  # Fallback to any link
                    
                    if lawyer_links:
                        # Safe href extraction using multiple methods
                        profile_link = ''
                        element = lawyer_links[0]
                        if hasattr(element, 'get_attribute'):
                            profile_link = element.get_attribute('href') or ''
                        elif hasattr(element, 'attrib'):
                            profile_link = element.attrib.get('href', '')
                        
                        if profile_link and not profile_link.startswith('http'):
                            profile_link = urljoin(self.template.url, profile_link)
                    
                    if not profile_link:
                        logger.warning(f"No profile link found for container {i}")
                        new_containers.append({'_container_index': i, '_error': 'No profile link found'})
                        continue
                    
                    logger.debug(f"Found profile link for subpage container {i}: {profile_link}")
                    
                    # Extract subpage data from the individual profile page
                    logger.info(f"Extracting subpage data from: {profile_link}")
                    subpage_data = self.extract_subpage_container_data(profile_link, element_config)
                    
                    if subpage_data:
                        subpage_data['_profile_link'] = profile_link
                        subpage_data['_container_index'] = i
                        new_containers.append(subpage_data)
                        logger.debug(f"Successfully extracted subpage data for container {i}: {list(subpage_data.keys())}")
                    else:
                        logger.warning(f"Failed to extract subpage data for container {i}")
                        new_containers.append({'_container_index': i, '_profile_link': profile_link, '_error': 'Extraction failed'})
                        
                except Exception as e:
                    logger.warning(f"Error processing container {i}: {e}")
                    new_containers.append({'_container_index': i, '_error': str(e)})
            
            logger.info(f"Successfully processed {len(new_containers)} new subpage containers")
            return new_containers
            
        except Exception as e:
            logger.error(f"Error in incremental subpage container extraction: {e}")
            return []
    
    def process_container_subpages(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
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
                            
                        # Look for a profile link in the item
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
                            subpage = self.fetch_page(profile_link)
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
                                    
                                    # Find elements on subpage
                                    sub_elements = []
                                    try:
                                        sub_elements = subpage.css(sub_selector)
                                    except Exception:
                                        sub_elements = subpage.css(sub_selector)
                                    
                                    if sub_elements:
                                        value = self.extract_element_value(sub_elements[0], sub_type)
                                        subpage_data[sub_label] = value
                                    else:
                                        logger.debug(f"Container subpage element not found: {sub_label} with selector {sub_selector}")
                                        subpage_data[sub_label] = None
                                        
                                except Exception as e:
                                    logger.warning(f"Error extracting container subpage element {sub_label}: {e}")
                                    subpage_data[sub_label] = None
                            
                            # Merge subpage data into main item
                            item.update(subpage_data)
                            logger.info(f"Enhanced container item with {len(subpage_data)} subpage fields")
                            
                            # Add small delay between subpage requests
                            time.sleep(1)
                            
                        except Exception as e:
                            logger.error(f"Error processing container subpage {profile_link}: {e}")
                            continue
        
        return enhanced_data
    
    def extract_subpage_data(self, element_config, main_data: Dict[str, Any]) -> Dict[str, Any]:
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
                
            # Look for profile link
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
                subpage = self.fetch_page(profile_link)
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
                        
                        # Find elements on subpage
                        sub_elements = []
                        try:
                            sub_elements = subpage.css(sub_selector)
                        except Exception:
                            sub_elements = subpage.css(sub_selector)
                        
                        if sub_elements:
                            value = self.extract_element_value(sub_elements[0], sub_type)
                            subpage_data[sub_label] = value
                        else:
                            logger.debug(f"Subpage element not found: {sub_label} with selector {sub_selector}")
                            subpage_data[sub_label] = None
                            
                    except Exception as e:
                        logger.warning(f"Error extracting subpage element {sub_label}: {e}")
                        subpage_data[sub_label] = None
                
                # Merge subpage data into main item
                item.update(subpage_data)
                logger.info(f"Enhanced data for {item.get('name', 'Unknown')} with {len(subpage_data)} subpage fields")
                
                # Add small delay between subpage requests
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing subpage {profile_link}: {e}")
                continue
        
        return enhanced_data
    
    def extract_subpage_data_alt(self, profile_url: str, subpage_elements: List) -> Dict[str, Any]:
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
            subpage = self.fetch_page(profile_url)
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
                            elements = self.current_page.css(sub_selector)
                    except Exception as selector_error:
                        logger.warning(f"Subpage selector failed for {sub_label}: {selector_error}")
                        
                        # Try fallback XPaths for known patterns
                        if any(keyword in sub_label.lower() for keyword in ['education', 'experience', 'bio', 'practice']):
                            fallback_xpaths = self.generate_fallback_xpaths(sub_label, sub_type)
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
                            for element in elements[:10]:  # Limit to first 10
                                value = self.extract_element_value(element, sub_type)
                                if value and value.strip():
                                    extracted_values.append(value.strip())
                            subpage_data[sub_label] = extracted_values
                        else:
                            # Extract single element
                            value = self.extract_element_value(elements[0], sub_type)
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
    
    def merge_directory_with_subpage_data(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge directory container data with subpage container data.
        
        Args:
            scraped_data: Data with separate main and subpage containers
            
        Returns:
            Merged data in the expected format
        """
        try:
            # Check if we have both main and subpage data to merge
            main_data = scraped_data.get('main', [])
            subpage_data = scraped_data.get('subpage', []) or scraped_data.get('sublink', []) or scraped_data.get('sublink_container', [])
            
            if not main_data:
                logger.info("No main directory data to merge")
                return scraped_data
            
            logger.info(f"Merging {len(main_data)} main entries with {len(subpage_data)} subpage entries")
            
            merged_results = []
            
            # Process each main entry
            for i, main_entry in enumerate(main_data):
                if not isinstance(main_entry, dict):
                    continue
                
                # Create base entry with main data
                merged_entry = {
                    'name': main_entry.get('name'),
                    'position': main_entry.get('position'),
                    'sector': main_entry.get('sector'),
                    'email': main_entry.get('email'),
                    'profile_link': main_entry.get('_profile_link')
                }
                
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
            
            logger.info(f"Successfully merged data into {len(merged_results)} unified entries")
            return result
            
        except Exception as e:
            logger.error(f"Error merging directory and subpage data: {e}")
            return scraped_data
    
    def populate_sublink_queue(self) -> None:
        """Populate the sublink queue by extracting profile links from main containers."""
        try:
            print("\n🔗 POPULATING SUBLINK QUEUE")
            print("="*40)
            
            # Get main containers from the current page
            main_container_elements = self.get_main_container_elements_for_subpage()
            
            if not main_container_elements:
                print("❌ No main containers found for sublink extraction")
                return
            
            print(f"📋 Found {len(main_container_elements)} main containers")
            
            # Extract profile links from each container
            for i, container in enumerate(main_container_elements):
                try:
                    # Find profile link in this container
                    lawyer_links = container.css("a[href*='/lawyer/']")
                    if not lawyer_links:
                        lawyer_links = container.css("a")  # Fallback to any link
                    
                    if lawyer_links:
                        # Safe href extraction
                        profile_link = ''
                        element = lawyer_links[0]
                        if hasattr(element, 'get_attribute'):
                            profile_link = element.get_attribute('href') or ''
                        elif hasattr(element, 'attrib'):
                            profile_link = element.attrib.get('href', '')
                        
                        if profile_link and not profile_link.startswith('http'):
                            profile_link = urljoin(self.template.url, profile_link)
                        
                        if profile_link and profile_link not in [item['url'] for item in self.sublink_queue]:
                            self.sublink_queue.append({
                                'url': profile_link,
                                'container_index': i,
                                'status': 'pending',
                                'data': None,
                                'error': None
                            })
                            
                except Exception as e:
                    logger.warning(f"Error extracting link from container {i}: {e}")
            
            print(f"✅ Populated queue with {len(self.sublink_queue)} sublinks")
            for i, item in enumerate(self.sublink_queue[:5]):  # Show first 5
                print(f"   {i+1}. {item['url']}")
            if len(self.sublink_queue) > 5:
                print(f"   ... and {len(self.sublink_queue) - 5} more")
            print("="*40)
            
        except Exception as e:
            logger.error(f"Error populating sublink queue: {e}")
    
    def process_sublink_queue_async(self) -> Dict[str, Any]:
        """Process sublinks asynchronously using the dedicated sublink browser engine."""
        try:
            if not self.sublink_engine or not self.sublink_queue:
                logger.warning("No sublink engine or empty queue - skipping async processing")
                return {}
            
            print(f"\n🚀 ASYNC SUBLINK PROCESSING ({len(self.sublink_queue)} items)")
            print("="*50)
            
            # Get subpage containers that need data from sublinks
            subpage_containers = [elem for elem in self.template.elements if self.is_subpage_container(elem)]
            
            if not subpage_containers:
                print("❌ No subpage containers found - skipping sublink processing")
                return {}
            
            all_subpage_data = {}
            
            # Initialize progress tracking
            total_sublinks = len(self.sublink_queue)
            processed_count = 0
            
            # Process each sublink one by one
            for queue_item in self.sublink_queue:
                try:
                    processed_count += 1
                    print(f"🔄 Processing ({processed_count}/{total_sublinks}): {queue_item['url']}")
                    
                    # Extract subpage data using the dedicated sublink engine
                    subpage_data = self.extract_subpage_data_with_engine(queue_item['url'], subpage_containers)
                    
                    if subpage_data:
                        # Store the extracted data
                        for container_label, data in subpage_data.items():
                            if container_label not in all_subpage_data:
                                all_subpage_data[container_label] = []
                            
                            # Add container index and profile link to the data
                            if isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict):
                                        item['_profile_link'] = queue_item['url']
                                        item['_container_index'] = queue_item['container_index']
                                all_subpage_data[container_label].extend(data)
                            elif isinstance(data, dict):
                                data['_profile_link'] = queue_item['url']
                                data['_container_index'] = queue_item['container_index']
                                all_subpage_data[container_label].append(data)
                        
                        queue_item['status'] = 'completed'
                        queue_item['data'] = subpage_data
                        self.processed_sublinks.append(queue_item)
                        
                        print(f"✅ Completed: {len(subpage_data)} containers extracted")
                    else:
                        queue_item['status'] = 'failed'
                        queue_item['error'] = 'No data extracted'
                        print(f"❌ Failed: No data extracted")
                    
                    # Small delay between requests
                    time.sleep(1)
                    
                except Exception as e:
                    queue_item['status'] = 'error'
                    queue_item['error'] = str(e)
                    logger.warning(f"Error processing sublink {queue_item['url']}: {e}")
                    print(f"❌ Error: {str(e)}")
            
            print(f"🎯 Async processing complete: {len(self.processed_sublinks)}/{total_sublinks} successful")
            print("="*50)
            
            return all_subpage_data
            
        except Exception as e:
            logger.error(f"Error in async sublink processing: {e}")
            return {}
    
    def extract_subpage_data_with_engine(self, url: str, subpage_containers: List) -> Dict[str, Any]:
        """Extract subpage data using the dedicated sublink engine with proper tab reuse."""
        try:
            # Initialize the persistent browser context and page if not already done
            if not hasattr(self, 'sublink_context') or self.sublink_context is None:
                print("🌐 Initializing Engine 2 browser context for tab reuse...")
                
                # Get the browser instance from the sublink engine
                browser = self.sublink_engine.get_browser()
                
                # Create a new context with cookies
                context_options = {
                    'viewport': {'width': 1920, 'height': 1080}
                }
                
                # Add cookies to context if they exist
                if self.template.cookies:
                    formatted_cookies = [{
                        'name': cookie.name,
                        'value': cookie.value,
                        'domain': cookie.domain,
                        'path': cookie.path,
                        'secure': getattr(cookie, 'secure', False),
                        'httpOnly': getattr(cookie, 'httpOnly', False)
                    } for cookie in self.template.cookies]
                    context_options['storage_state'] = {'cookies': formatted_cookies}
                    print(f"🍪 Setting up {len(self.template.cookies)} cookies in browser context")
                
                self.sublink_context = browser.new_context(**context_options)
                self.sublink_page = self.sublink_context.new_page()
                
                print("✅ Engine 2 context and page initialized for true tab reuse")
                
                # Navigate to the first URL
                print(f"🔄 Engine 2 navigating to initial URL: {url}")
                self.sublink_page.goto(url, wait_until='networkidle', timeout=self.template.wait_timeout * 1000)
                print("✅ Initial navigation completed")
                
            else:
                # Reuse existing page - navigate to new URL
                print(f"🔄 Engine 2 reusing existing tab to navigate to: {url}")
                self.sublink_page.goto(url, wait_until='networkidle', timeout=self.template.wait_timeout * 1000)
                print("✅ Tab reuse navigation completed")
            
            if not self.sublink_page or self.sublink_page.status != 200:
                logger.warning(f"Failed to fetch subpage: {url}")
                return {}
            
            # Store original page and switch to subpage temporarily
            original_page = self.current_page
            self.current_page = self.sublink_page
            
            subpage_data = {}
            
            # Extract data for each subpage container
            for container in subpage_containers:
                try:
                    container_data = self.extract_element_data(container)
                    if container_data:
                        subpage_data[container.label] = container_data
                except Exception as e:
                    logger.warning(f"Error extracting {container.label} from subpage: {e}")
            
            # Restore original page
            self.current_page = original_page
            
            return subpage_data
            
        except Exception as e:
            logger.error(f"Error extracting subpage data from {url}: {e}")
            return {}
    
    # Helper methods
    def fetch_page(self, url: str):
        """Fetch a page using the browser instance."""
        # Placeholder - would be implemented using self.fetcher
        return None
    
    def map_generic_selector(self, sub_element: dict, context: str = "directory") -> str:
        """Map generic selectors to meaningful ones based on label and context."""
        # Placeholder - would use SelectorEngine
        return sub_element.get('selector', '')
    
    def get_main_container_elements_for_subpage(self):
        """Get main container elements for subpage extraction."""
        try:
            directory_patterns = [
                ".people.loading",
                ".wp-grid-builder .wpgb-card",
                ".people-list .wp-block-column",
                "[class*='people']",
                ".wpgb-grid-archivePeople > div"
            ]
            
            for pattern in directory_patterns:
                elements = self.current_page.css(pattern)
                if elements:
                    logger.debug(f"Found {len(elements)} directory containers with pattern: {pattern}")
                    return elements
            
            logger.warning("No main container elements found using directory patterns")
            return []
            
        except Exception as e:
            logger.error(f"Error getting main container elements: {e}")
            return []
    
    def is_subpage_container(self, element) -> bool:
        """Check if an element is a subpage container."""
        # Placeholder implementation
        return hasattr(element, 'follow_links') and element.follow_links
    
    def extract_element_data(self, element):
        """Extract data from an element."""
        # Placeholder - would be implemented using DataExtractor
        return None
    
    def extract_element_value(self, element, element_type: str) -> str:
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
                attr_name = 'value'
                if hasattr(element, 'get_attribute'):
                    return element.get_attribute(attr_name) or ''
                elif hasattr(element, 'attrib'):
                    return element.attrib.get(attr_name, '')
            elif element_type == 'html':
                return str(element)
            else:
                return element.text if hasattr(element, 'text') else str(element)
        except Exception as e:
            logger.warning(f"Error extracting element value: {e}")
            return ''
    
    def generate_fallback_xpaths(self, label: str, element_type: str) -> List[str]:
        """Generate fallback XPath selectors for common patterns."""
        return []  # Placeholder implementation