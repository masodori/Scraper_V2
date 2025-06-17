#!/usr/bin/env python3
"""
Template analysis utilities for determining scraping strategies.
"""

from ..context import ScrapingContext
from ...models.scraping_template import ElementSelector


class TemplateAnalyzer:
    """
    Analyzes template characteristics and determines scraping strategies.
    """
    
    def __init__(self, context: ScrapingContext):
        self.context = context
    
    def looks_like_directory_template(self) -> bool:
        """
        Determine if template appears to be designed for directory/listing pages.
        Enhanced detection for lawyer directory patterns.
        
        Returns:
            True if template has directory-like characteristics
        """
        directory_indicators = [
            # Container-based extraction suggests multiple items
            any(hasattr(elem, 'is_container') and elem.is_container for elem in self.context.template.elements),
            # Multiple elements suggests listing
            any(elem.is_multiple for elem in self.context.template.elements),
            # Directory-like selectors
            any('people' in elem.selector.lower() or 'list' in elem.selector.lower() 
                or 'grid' in elem.selector.lower() for elem in self.context.template.elements),
            # Profile link extraction suggests directory
            any(hasattr(elem, 'sub_elements') and elem.sub_elements and 
                any('link' in sub.get('label', '').lower() or 'profile' in sub.get('label', '').lower() 
                    or 'email' in sub.get('label', '').lower()
                    for sub in elem.sub_elements if isinstance(sub, dict))
                for elem in self.context.template.elements if hasattr(elem, 'sub_elements')),
            # Actions that navigate to profiles
            any('link' in action.label.lower() and '/lawyer/' in getattr(action, 'target_url', '')
                for action in self.context.template.actions if hasattr(self.context.template, 'actions')),
            # Profile-like sub-element patterns (name, title, email combinations suggest directory)
            any(hasattr(elem, 'sub_elements') and elem.sub_elements and
                len([sub for sub in elem.sub_elements if isinstance(sub, dict) and 
                     any(keyword in sub.get('label', '').lower() 
                         for keyword in ['name', 'title', 'position', 'email', 'phone'])]) >= 2
                for elem in self.context.template.elements if hasattr(elem, 'sub_elements'))
        ]
        
        return any(directory_indicators)
    
    def template_needs_subpage_data(self) -> bool:
        """
        Check if template has elements that require subpage navigation.
        
        Returns:
            True if template has subpage elements or education/credentials elements
        """
        # Check for elements that are typically found on individual profile pages
        subpage_indicators = [
            # Elements with subpage_elements defined
            any(hasattr(elem, 'subpage_elements') and elem.subpage_elements 
                for elem in self.context.template.elements),
            # Education/credentials elements (typically on individual pages)
            any(hasattr(elem, 'sub_elements') and elem.sub_elements and
                any('education' in sub.get('label', '').lower() or 'cred' in sub.get('label', '').lower()
                    for sub in elem.sub_elements if isinstance(sub, dict))
                for elem in self.context.template.elements if hasattr(elem, 'sub_elements')),
            # Multiple containers with different purposes (main + subpage data)
            len([elem for elem in self.context.template.elements if hasattr(elem, 'is_container') and elem.is_container]) >= 2,
            # Actions that navigate to specific pages
            any('link' in action.label.lower() and '/lawyer/' in getattr(action, 'target_url', '')
                for action in self.context.template.actions if hasattr(self.context.template, 'actions'))
        ]
        
        return any(subpage_indicators)
    
    def is_subpage_container(self, element_config: ElementSelector) -> bool:
        """
        Check if a container is meant to extract data from individual subpages.
        
        Args:
            element_config: ElementSelector configuration
            
        Returns:
            True if container should extract data from subpages
        """
        subpage_indicators = [
            # Container label suggests subpage data
            any(keyword in element_config.label.lower() 
                for keyword in ['subpage', 'sublink', 'subcon', 'education', 'credential', 'experience', 'bio', 'profile']),
            # Sub-elements that are typically on individual pages
            hasattr(element_config, 'sub_elements') and element_config.sub_elements and
            any(keyword in sub.get('label', '').lower() if isinstance(sub, dict) else getattr(sub, 'label', '').lower()
                for keyword in ['education', 'credential', 'admission', 'bar', 'experience', 'bio', 'creds']
                for sub in element_config.sub_elements),
            # Template has follow_links enabled for this container
            getattr(element_config, 'follow_links', False)
        ]
        
        is_subpage = any(subpage_indicators)
        self.context.session_logger.debug(f"Subpage container check for '{element_config.label}': {is_subpage} (indicators: {subpage_indicators})")
        return is_subpage