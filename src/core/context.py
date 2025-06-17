#!/usr/bin/env python3
"""
Scraping context management for shared state and resources.
"""

import logging
from ..models.scraping_template import ScrapingTemplate


class ScrapingContext:
    """
    Shared context for all scraping components.
    Holds common state and provides unified access to resources.
    """
    
    def __init__(self, template: ScrapingTemplate):
        self.template = template
        self.fetcher = None
        self.current_page = None
        self.session_logger = logging.getLogger(f"scrapling_runner.{template.name}")