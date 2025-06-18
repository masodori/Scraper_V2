#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for the Interactive Web Scraper test suite.

This module provides common fixtures and test utilities used across all test modules.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

from src.core.context import ScrapingContext
from src.models.scraping_template import (
    ScrapingTemplate, 
    ElementSelector, 
    SubElement,
    NavigationAction,
    PaginationPattern
)


@pytest.fixture
def mock_scrapling_context():
    """Create a mock ScrapingContext for testing."""
    context = Mock(spec=ScrapingContext)
    context.session_logger = Mock()
    context.current_page = Mock()
    context.template = Mock(spec=ScrapingTemplate)
    context.fetcher = Mock()
    context.start_time = 1234567890.0
    context.total_items_processed = 0
    return context


@pytest.fixture
def mock_scrapling_page():
    """Create a mock page object with common methods."""
    page = Mock()
    page.css = Mock(return_value=[])
    page.xpath = Mock(return_value=[])
    page.urljoin = Mock(side_effect=lambda url: f"https://example.com{url}")
    page.url = "https://example.com/test"
    return page


@pytest.fixture
def mock_scrapling_element():
    """Create a mock DOM element with common properties."""
    element = Mock()
    element.text = "Sample Text"
    element.get_attribute = Mock(return_value="test-value")
    element.attrib = {"href": "/test-link", "class": "test-class"}
    return element


@pytest.fixture
def sample_element_selector():
    """Create a sample ElementSelector for testing."""
    return ElementSelector(
        label="test_element",
        selector=".test-selector",
        element_type="text",
        is_required=False,
        is_multiple=False,
        is_container=False
    )


@pytest.fixture
def sample_container_selector():
    """Create a sample container ElementSelector for testing."""
    sub_elements = [
        {"label": "name", "selector": "h3", "element_type": "text"},
        {"label": "title", "selector": ".position", "element_type": "text"},
        {"label": "email", "selector": "a[href*='mailto']", "element_type": "text"},
        {"label": "profile_link", "selector": "a", "element_type": "link"}
    ]
    
    return ElementSelector(
        label="profile_container",
        selector=".profile-card",
        element_type="container",
        is_required=False,
        is_multiple=True,
        is_container=True,
        sub_elements=sub_elements
    )


@pytest.fixture
def sample_pagination_config():
    """Create a sample PaginationPattern for testing."""
    return PaginationPattern(
        pattern_type="button",
        next_selector=".next-page",
        load_more_selector=".load-more",
        page_selector=".page-number",
        scroll_pause_time=2.0,
        max_pages=10,
        end_condition_selector=".end-marker"
    )


@pytest.fixture
def sample_scraping_template(sample_container_selector, sample_pagination_config):
    """Create a sample ScrapingTemplate for testing."""
    return ScrapingTemplate(
        name="test_template",
        url="https://example.com/people",
        elements=[sample_container_selector],
        pagination=sample_pagination_config
    )


@pytest.fixture
def sample_extracted_data():
    """Create sample extracted data for testing."""
    return {
        "main_profiles": [
            {
                "name": "John Doe",
                "title": "Partner",
                "email": "john.doe@example.com",
                "profile_link": "/john-doe",
                "_container_index": 0,
                "_profile_link": "/john-doe"
            },
            {
                "name": "Jane Smith", 
                "title": "Associate",
                "email": "jane.smith@example.com",
                "profile_link": "/jane-smith",
                "_container_index": 1,
                "_profile_link": "/jane-smith"
            }
        ]
    }


@pytest.fixture
def sample_subpage_data():
    """Create sample subpage data for testing."""
    return {
        "education_data": [
            {
                "education": "Harvard Law School",
                "credential": "J.D., 2010",
                "_container_index": 0,
                "_profile_link": "/john-doe"
            },
            {
                "education": "Yale Law School",
                "credential": "J.D., 2012", 
                "_container_index": 1,
                "_profile_link": "/jane-smith"
            }
        ]
    }


@pytest.fixture
def mock_progress_tracker():
    """Create a mock ProgressTracker for testing."""
    tracker = Mock()
    tracker.update = Mock()
    tracker.finish = Mock()
    tracker.get_eta = Mock(return_value="2 minutes")
    tracker.get_progress_percentage = Mock(return_value=50.0)
    return tracker


class MockFetcher:
    """Mock fetcher class for testing scrapling interactions."""
    
    def __init__(self):
        self.current_page = Mock()
        self.session = Mock()
        
    def get(self, url: str):
        """Mock get method."""
        self.current_page.url = url
        return self.current_page
        
    def close(self):
        """Mock close method."""
        pass


@pytest.fixture
def mock_fetcher():
    """Create a mock fetcher instance."""
    return MockFetcher()


def create_mock_elements(count: int, text_prefix: str = "Item") -> List[Mock]:
    """
    Utility function to create a list of mock elements.
    
    Args:
        count: Number of mock elements to create
        text_prefix: Prefix for element text content
        
    Returns:
        List of mock elements
    """
    elements = []
    for i in range(count):
        element = Mock()
        element.text = f"{text_prefix} {i + 1}"
        element.get_attribute = Mock(return_value=f"attr-value-{i + 1}")
        element.attrib = {"id": f"element-{i + 1}"}
        elements.append(element)
    return elements


def create_sample_container_data(num_containers: int = 3) -> List[Dict[str, Any]]:
    """
    Utility function to create sample container data.
    
    Args:
        num_containers: Number of containers to create
        
    Returns:
        List of container data dictionaries
    """
    containers = []
    for i in range(num_containers):
        container = {
            "name": f"Person {i + 1}",
            "title": f"Title {i + 1}",
            "email": f"person{i + 1}@example.com",
            "profile_link": f"/person-{i + 1}",
            "_container_index": i
        }
        containers.append(container)
    return containers


# Make utility functions available as pytest fixtures
@pytest.fixture
def create_mock_elements_factory():
    """Factory fixture for creating mock elements."""
    return create_mock_elements


@pytest.fixture 
def create_sample_container_data_factory():
    """Factory fixture for creating sample container data."""
    return create_sample_container_data


# Test markers for categorizing tests
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "network: marks tests that require network access")