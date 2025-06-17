#!/usr/bin/env python3
"""
Selector enhancement and fallback generation utilities.
"""

from ..context import ScrapingContext


class SelectorEngine:
    """
    Handles selector enhancement, fallback generation, and CSS/XPath conversion.
    """
    
    def __init__(self, context: ScrapingContext):
        self.context = context
    
    def map_generic_selector(self, sub_element: dict, context: str = "directory") -> str:
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
                return "strong, p.name strong, h3, h2, .name, [class*='name'] strong, strong:first-of-type"
            else:
                return "h1, h2, .entry-title, .page-title, .lawyer-name, .attorney-name"
                
        elif any(keyword in label for keyword in ['title', 'position', 'job']):
            if context == "directory":
                return ".title, .position, .job-title, [class*='title'], [class*='position'], p.title span:first-child, span[class*='position']"
            else:
                return ".position, .title, .job-title, h2 + p, h1 + p"
                
        elif any(keyword in label for keyword in ['email', 'mail']):
            return "a[href^='mailto:'], p.contact-details a[href^='mailto:'], .email, [class*='email'], a[href*='@']"
            
        elif 'phone' in label:
            return "a[href^='tel:'], .phone, [class*='phone'], a[href*='tel']"
            
        elif any(keyword in label for keyword in ['sector', 'practice', 'area']):
            if context == "directory":
                return ".practice-area, .sector, [class*='practice'], [class*='sector'], p.contact-details span:not([class*='position']), p.title span:last-child, span[class*='practice']"
            else:
                return ".practice-area, .capabilities, .focus-areas, a[href*='/practice/']"
                
        elif any(keyword in label for keyword in ['link', 'profile', 'url']) or 'email' in label:
            if 'email' in label:
                return "a[href^='mailto:'], .email, [class*='email'], a[href*='@']"
            else:
                return "a[href*='/lawyer/'], a[href*='/attorney/'], a[href*='/people/'], a[href*='/team/'], a"
            
        elif 'education' in label:
            # More specific selectors for education to avoid duplication
            if 'education2' in label:
                return ".education li:nth-of-type(n+2), ul[class*='education'] li:nth-of-type(n+2)"
            else:
                return ".education li:first-child, .education li:first-of-type, ul[class*='education'] li:first-child"
            
        elif any(keyword in label for keyword in ['cred', 'admission', 'bar']):
            # More specific selectors for credentials to avoid duplication
            if 'creds2' in label:
                return ".admissions li:nth-of-type(n+2), .bar li:nth-of-type(n+2), .credentials li:nth-of-type(n+2)"
            else:
                return ".admissions li:first-child, .bar li:first-child, .credentials li:first-child"
        
        # Default fallback - return original
        return original_selector