#!/usr/bin/env python3
"""
Data extraction engine for processing scraped elements and containers.
"""

import logging
from typing import Dict, List, Any, Optional

from ..context import ScrapingContext
from ..utils.progress import ProgressTracker
from ...models.scraping_template import ElementSelector

logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Handles data extraction from web pages using multiple fallback strategies.
    """
    
    def __init__(self, context: ScrapingContext):
        self.context = context
        self.current_page = context.current_page
    
    def extract_data(self) -> Dict[str, Any]:
        """
        Extract data from the page using template selectors.
        
        Returns:
            Dictionary containing extracted data
        """
        extracted_data = {}
        
        # Initialize progress tracker
        progress = ProgressTracker(len(self.context.template.elements), "Extracting elements")
        
        for idx, element in enumerate(self.context.template.elements):
            try:
                progress.update(0, f"Extracting: {element.label}")
                logger.debug(f"Extracting data for element: {element.label}")
                
                value = self.extract_element_data(element)
                extracted_data[element.label] = value
                
                logger.debug(f"Successfully extracted {element.label}: {str(value)[:100]}...")
                progress.update(1, f"Completed: {element.label}")
                
            except Exception as e:
                error_msg = f"Failed to extract {element.label}: {str(e)}"
                logger.warning(error_msg)
                progress.update(1, f"Failed: {element.label}")
                
                if element.is_required:
                    # Check if this is a location-specific element that might not exist on all profiles
                    is_location_element = (
                        'location' in element.label.lower() or
                        'city' in element.label.lower() or
                        'normalize-space' in element.selector.lower() or
                        any(city in element.selector for city in ['Riyadh', 'Dubai', 'London', 'New York'])
                    )
                    
                    if is_location_element:
                        logger.warning(f"Location-specific required element failed, continuing: {element.label}")
                        extracted_data[element.label] = None
                    else:
                        raise Exception(error_msg)
                else:
                    extracted_data[element.label] = None
        
        progress.finish("Extraction complete")
        
        # Post-process to merge related containers with subpage data
        merged_data = self.merge_related_containers(extracted_data)
        return merged_data
    
    def extract_element_data(self, element: ElementSelector) -> Any:
        """
        Extract data from a single element using multiple fallback strategies.
        
        Args:
            element: ElementSelector defining what to extract
            
        Returns:
            Extracted data (string, list, or None)
        """
        # Always use the latest page from context
        self.current_page = self.context.current_page
        
        if not self.current_page:
            raise Exception("No page available for data extraction")
        
        try:
            # Handle container elements specially
            if hasattr(element, 'is_container') and element.is_container:
                return self.extract_container_data(element)
            
            # Try multiple selection strategies in order of reliability
            found_elements = self.find_elements_with_fallback(element)
            
            if not found_elements:
                if element.is_required:
                    # Check if this is a location-specific element that might not exist on all profiles
                    is_location_element = (
                        'location' in element.label.lower() or
                        'city' in element.label.lower() or
                        'normalize-space' in element.selector.lower() or
                        any(city in element.selector for city in ['Riyadh', 'Dubai', 'London', 'New York'])
                    )
                    
                    if is_location_element:
                        logger.warning(f"Location-specific required element not found, continuing: {element.label}")
                        return None
                    else:
                        raise Exception(f"Required element not found: {element.selector}")
                return None
            
            # Handle multiple elements
            if element.is_multiple:
                return self.extract_multiple_elements(found_elements, element)
            else:
                return self.extract_single_element(found_elements[0], element)
                
        except Exception as e:
            logger.error(f"Error extracting element {element.label}: {e}")
            raise
    
    def find_elements_with_fallback(self, element: ElementSelector) -> List:
        """
        Find elements using multiple strategies for maximum reliability.
        
        Args:
            element: ElementSelector configuration
            
        Returns:
            List of found elements
        """
        strategies = [
            # Strategy 1: AutoMatch with original selector
            lambda: self.try_automatch_selector(element),
            # Strategy 2: Semantic XPath generation
            lambda: self.try_semantic_xpath(element),
            # Strategy 3: Content-based selection
            lambda: self.try_content_based_selection(element),
            # Strategy 4: Structure-based selection
            lambda: self.try_structure_based_selection(element),
            # Strategy 5: Original selector as fallback
            lambda: self.try_original_selector(element)
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
    
    def extract_single_element(self, element, element_config: ElementSelector) -> Any:
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
    
    def extract_multiple_elements(self, elements, element_config: ElementSelector) -> List[Any]:
        """Extract data from multiple elements."""
        results = []
        
        for element in elements:
            try:
                value = self.extract_single_element(element, element_config)
                if value is not None:
                    results.append(value)
            except Exception as e:
                logger.warning(f"Error extracting from multiple element: {e}")
                continue
        
        return results
    
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
    
    def extract_container_data(self, element_config: ElementSelector) -> List[Dict[str, Any]]:
        """
        Extract data from container elements - placeholder for full implementation.
        This method would contain the complex container extraction logic.
        """
        # This is a simplified version - the full implementation would be quite complex
        containers = []
        
        try:
            logger.info(f"Extracting container data with selector: {element_config.selector}")
            
            # Find container elements using original selector
            container_elements = self.current_page.css(element_config.selector)
            
            if not container_elements:
                logger.warning(f"No containers found with selector: {element_config.selector}")
                return []
            
            # Extract data from each container
            for i, container in enumerate(container_elements):
                container_data = {}
                
                # Extract sub-elements if defined
                if hasattr(element_config, 'sub_elements') and element_config.sub_elements:
                    for sub_element in element_config.sub_elements:
                        if isinstance(sub_element, dict):
                            sub_selector = sub_element.get('selector', '')
                            sub_label = sub_element.get('label', '')
                            sub_type = sub_element.get('element_type', 'text')
                            
                            try:
                                # Find sub-element within container
                                sub_elements = container.css(sub_selector)
                                if sub_elements:
                                    value = self.extract_element_value(sub_elements[0], sub_type)
                                    container_data[sub_label] = value
                                else:
                                    container_data[sub_label] = None
                            except Exception as e:
                                logger.warning(f"Error extracting sub-element {sub_label}: {e}")
                                container_data[sub_label] = None
                
                # Add container index for tracking
                container_data['_container_index'] = i
                containers.append(container_data)
            
            logger.info(f"Extracted data from {len(containers)} containers")
            return containers
            
        except Exception as e:
            logger.error(f"Error extracting container data: {e}")
            return []
    
    def merge_related_containers(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge related containers that share the same profile link into nested structures.
        """
        try:
            # Find main containers and subpage containers
            main_containers = {}
            subpage_containers = {}
            other_data = {}
            
            for label, data in extracted_data.items():
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    # Check if this looks like a main container (has basic profile info)
                    sample_item = data[0]
                    has_basic_fields = any(field in sample_item for field in ['name', 'Position', 'title'])
                    has_subpage_fields = any(field in sample_item for field in ['education', 'credential', 'admission', 'bar'])
                    
                    if has_basic_fields and not has_subpage_fields:
                        main_containers[label] = data
                        logger.info(f"Identified '{label}' as main container with {len(data)} items")
                    elif has_subpage_fields or 'subpage' in label.lower() or 'second' in label.lower():
                        subpage_containers[label] = data
                        logger.info(f"Identified '{label}' as subpage container with {len(data)} items")
                    else:
                        other_data[label] = data
                else:
                    other_data[label] = data
            
            # If we have both main and subpage containers, merge them
            if main_containers and subpage_containers:
                logger.info("Merging main and subpage containers...")
                
                for main_label, main_data in main_containers.items():
                    for main_item in main_data:
                        if not isinstance(main_item, dict) or '_profile_link' not in main_item:
                            continue
                            
                        main_profile_link = main_item['_profile_link']
                        main_index = main_item.get('_container_index')
                        
                        # Find matching subpage data
                        for subpage_label, subpage_data in subpage_containers.items():
                            for subpage_item in subpage_data:
                                if not isinstance(subpage_item, dict):
                                    continue
                                    
                                subpage_profile_link = subpage_item.get('_profile_link')
                                subpage_index = subpage_item.get('_container_index')
                                
                                # Match by profile link or container index
                                if (main_profile_link and subpage_profile_link and main_profile_link == subpage_profile_link) or \
                                   (main_index is not None and subpage_index is not None and main_index == subpage_index):
                                    
                                    # Merge subpage data into main item
                                    subpage_info = {k: v for k, v in subpage_item.items() 
                                                  if not k.startswith('_')}
                                    
                                    # Nest subpage data under a clear key
                                    if subpage_info:
                                        if 'education' in subpage_label.lower() or 'credential' in subpage_label.lower():
                                            # Add education/credentials directly to the main profile
                                            for key, value in subpage_info.items():
                                                main_item[key] = value
                                        else:
                                            # For other subpage data, nest under descriptive key
                                            clean_label = subpage_label.replace('container', '').replace('second', '').strip()
                                            main_item[f'{clean_label}_details'] = subpage_info
                                        
                                        logger.debug(f"Merged {subpage_label} data into {main_label} item {main_index}")
                
                # Return merged data (main containers + other data, exclude processed subpage containers)
                merged_result = {**main_containers, **other_data}
                logger.info(f"Successfully merged containers. Final structure: {list(merged_result.keys())}")
                return merged_result
            
            # If no merging needed, return original data
            return extracted_data
            
        except Exception as e:
            logger.warning(f"Error merging containers: {e}")
            return extracted_data
    
    # Fallback strategy methods
    def try_automatch_selector(self, element: ElementSelector) -> List:
        """Try AutoMatch with the original selector."""
        # Auto-detect selector type
        is_xpath = (element.selector_type == 'xpath' or 
                   element.selector.startswith('xpath:') or
                   element.selector.startswith('//') or
                   'normalize-space' in element.selector)
        
        if is_xpath:
            # Handle XPath selectors
            xpath_expr = element.selector[6:] if element.selector.startswith('xpath:') else element.selector
            # Fix common XPath syntax errors
            if 'normalize-space' in xpath_expr and not xpath_expr.startswith('//'):
                xpath_expr = '//' + xpath_expr.lstrip('/')
            
            try:
                return self.current_page.xpath(xpath_expr)
            except Exception as e:
                logger.debug(f"XPath failed: {e}")
                return []
        else:
            return self.current_page.css(element.selector)
    
    def try_semantic_xpath(self, element: ElementSelector) -> List:
        """Try semantic XPath generation based on element label."""
        # Placeholder for semantic XPath generation
        return []
    
    def try_content_based_selection(self, element: ElementSelector) -> List:
        """Try content-based element selection."""
        # Placeholder for content-based selection
        return []
    
    def try_structure_based_selection(self, element: ElementSelector) -> List:
        """Try structure-based element selection."""
        # Placeholder for structure-based selection
        return []
    
    def try_original_selector(self, element: ElementSelector) -> List:
        """Try the original selector as final fallback."""
        try:
            return self.current_page.css(element.selector)
        except Exception:
            return []