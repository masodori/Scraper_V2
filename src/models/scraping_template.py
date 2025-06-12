#!/usr/bin/env python3
"""
Data models for scraping templates and validation.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import json


class SubElement(BaseModel):
    """Represents a sub-element within a container for composite extraction."""
    
    label: str = Field(..., description="Label for the sub-element")
    selector: str = Field(..., description="Relative selector within the container")
    element_type: str = Field(default="text", description="Type of data to extract")
    attribute_name: Optional[str] = Field(None, description="Attribute name if element_type is 'attribute'")
    is_required: bool = Field(default=True, description="Whether this sub-element is required")


class ElementSelector(BaseModel):
    """Represents a single element selector with its label and metadata."""
    
    label: str = Field(..., description="User-defined label for the element")
    selector: str = Field(..., description="CSS selector or XPath for the element")
    selector_type: str = Field(default="css", description="Type of selector (css or xpath)")
    element_type: str = Field(default="text", description="Type of data to extract (text, attribute, html, container, composite)")
    attribute_name: Optional[str] = Field(None, description="Attribute name if element_type is 'attribute'")
    is_multiple: bool = Field(default=False, description="Whether this selector matches multiple elements")
    is_required: bool = Field(default=True, description="Whether this element is required for successful scraping")
    
    # Container/Composite element support
    is_container: bool = Field(default=False, description="Whether this is a repeating container element")
    use_find_similar: bool = Field(default=False, description="Use Scrapling's find_similar() method")
    sub_elements: List[SubElement] = Field(default_factory=list, description="Sub-elements to extract from each container")
    
    # Subpage following
    follow_links: bool = Field(default=False, description="Follow links found in this element")
    subpage_elements: List['ElementSelector'] = Field(default_factory=list, description="Elements to extract from linked subpages")
    
    @field_validator('selector_type')
    @classmethod
    def validate_selector_type(cls, v):
        if v not in ['css', 'xpath']:
            raise ValueError('selector_type must be either "css" or "xpath"')
        return v
    
    @field_validator('element_type')
    @classmethod
    def validate_element_type(cls, v):
        if v not in ['text', 'attribute', 'html', 'link', 'container', 'composite']:
            raise ValueError('element_type must be one of: text, attribute, html, link, container, composite')
        return v


class CookieData(BaseModel):
    """Represents cookie information for the scraping session."""
    
    name: str
    value: str
    domain: Optional[str] = None
    path: Optional[str] = "/"
    secure: bool = False
    httpOnly: bool = False
    sameSite: Optional[str] = None


class FilterConfiguration(BaseModel):
    """Configuration for filter-based content loading."""
    
    filter_label: str = Field(..., description="Label for the filter")
    filter_selector: str = Field(..., description="Selector for the filter element")
    filter_values: List[str] = Field(default_factory=list, description="Values to select for this filter")
    filter_type: str = Field(default="select", description="Type of filter (select, checkbox, button)")
    wait_after_change: float = Field(default=2.0, description="Wait time after changing filter")


class PaginationPattern(BaseModel):
    """Configuration for pagination and infinite scroll patterns."""
    
    pattern_type: str = Field(..., description="Type of pagination (button, infinite_scroll, numbered)")
    next_selector: Optional[str] = Field(None, description="Selector for next button")
    load_more_selector: Optional[str] = Field(None, description="Selector for load more button")
    page_selector: Optional[str] = Field(None, description="Selector for page number links")
    scroll_pause_time: float = Field(default=2.0, description="Time to pause during infinite scroll")
    max_pages: Optional[int] = Field(None, description="Maximum pages to scrape (None for unlimited)")
    end_condition_selector: Optional[str] = Field(None, description="Selector that indicates end of content")


class NavigationAction(BaseModel):
    """Represents navigation or interaction actions (e.g., next page button)."""
    
    label: str = Field(..., description="Action label (e.g., 'next_page', 'load_more')")
    selector: str = Field(..., description="Selector for the action element")
    action_type: str = Field(default="click", description="Type of action (click, scroll, etc.)")
    wait_after: float = Field(default=2.0, description="Seconds to wait after performing action")
    target_url: Optional[str] = Field(None, description="Target URL if this is a navigation action")
    
    # Advanced action options
    repeat_until_missing: bool = Field(default=False, description="Repeat action until element is missing")
    repeat_until_no_change: bool = Field(default=False, description="Repeat until page content doesn't change")
    max_repeats: Optional[int] = Field(None, description="Maximum number of times to repeat action")
    
    @field_validator('action_type')
    @classmethod
    def validate_action_type(cls, v):
        if v not in ['click', 'scroll', 'hover', 'wait', 'infinite_scroll']:
            raise ValueError('action_type must be one of: click, scroll, hover, wait, infinite_scroll')
        return v


class ScrapingTemplate(BaseModel):
    """Main scraping template containing all configuration for automated scraping."""
    
    # Metadata
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    version: str = Field(default="1.0", description="Template version")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    # Target configuration
    url: str = Field(..., description="Target URL for scraping")
    user_agent: Optional[str] = Field(None, description="Custom user agent string")
    
    # Browser and session configuration
    headless: bool = Field(default=True, description="Whether to run browser in headless mode")
    wait_timeout: float = Field(default=30.0, description="Default wait timeout in seconds")
    page_load_timeout: float = Field(default=60.0, description="Page load timeout in seconds")
    
    # Cookies and authentication
    cookies: List[CookieData] = Field(default_factory=list, description="Cookies to set for the session")
    
    # Element selectors for data extraction
    elements: List[ElementSelector] = Field(default_factory=list, description="Elements to scrape")
    
    # Navigation and interaction actions
    actions: List[NavigationAction] = Field(default_factory=list, description="Navigation and interaction actions")
    
    # Advanced scraping patterns
    filters: List[FilterConfiguration] = Field(default_factory=list, description="Filter configurations for dynamic content")
    pagination: Optional[PaginationPattern] = Field(None, description="Pagination pattern configuration")
    
    # Multi-page scraping
    enable_subpage_scraping: bool = Field(default=False, description="Enable following links to subpages")
    subpage_url_pattern: Optional[str] = Field(None, description="Regex pattern for valid subpage URLs")
    max_subpages: Optional[int] = Field(None, description="Maximum number of subpages to visit")
    
    # Anti-detection settings
    stealth_mode: bool = Field(default=True, description="Enable stealth mode to avoid detection")
    random_delays: bool = Field(default=True, description="Add random delays between actions")
    
    # Output configuration
    output_format: str = Field(default="json", description="Default output format")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        from urllib.parse import urlparse
        result = urlparse(v)
        if not all([result.scheme, result.netloc]):
            raise ValueError('Invalid URL format')
        return v
    
    @field_validator('output_format')
    @classmethod
    def validate_output_format(cls, v):
        if v not in ['json', 'csv', 'excel']:
            raise ValueError('output_format must be one of: json, csv, excel')
        return v
    
    def to_json(self, indent: int = 2) -> str:
        """Export template to JSON string."""
        return self.model_dump_json(indent=indent)
    
    def save_to_file(self, filepath: str) -> None:
        """Save template to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'ScrapingTemplate':
        """Load template from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
    
    def get_element_by_label(self, label: str) -> Optional[ElementSelector]:
        """Get element selector by label."""
        for element in self.elements:
            if element.label == label:
                return element
        return None
    
    def get_action_by_label(self, label: str) -> Optional[NavigationAction]:
        """Get action by label."""
        for action in self.actions:
            if action.label == label:
                return action
        return None


class ScrapingResult(BaseModel):
    """Represents the result of a scraping operation."""
    
    template_name: str
    url: str
    scraped_at: datetime = Field(default_factory=datetime.now)
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_json(self, indent: int = 2) -> str:
        """Export result to JSON string."""
        return self.model_dump_json(indent=indent)
    
    def save_to_file(self, filepath: str) -> None:
        """Save result to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())


# Update forward references for recursive models
ElementSelector.model_rebuild()