#!/usr/bin/env python3
"""
Comprehensive unit tests for SelectorEngine module.

Tests for selector enhancement, mapping, and fallback generation.
"""

import pytest
from unittest.mock import Mock

from src.core.selectors.selector_engine import SelectorEngine
from src.core.context import ScrapingContext


class TestSelectorEngine:
    """Test cases for SelectorEngine functionality."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock ScrapingContext for testing."""
        context = Mock(spec=ScrapingContext)
        context.session_logger = Mock()
        return context

    @pytest.fixture
    def selector_engine(self, mock_context):
        """Create SelectorEngine instance with mock context."""
        return SelectorEngine(mock_context)

    def test_initialization(self, selector_engine, mock_context):
        """Test SelectorEngine initialization."""
        assert selector_engine.context == mock_context

    def test_map_generic_selector_preserve_xpath(self, selector_engine):
        """Test that XPath selectors are preserved unchanged."""
        sub_element = {
            "label": "name", 
            "selector": "xpath://div[@class='name']/text()"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        assert result == "xpath://div[@class='name']/text()"

    def test_map_generic_selector_preserve_specific_css(self, selector_engine):
        """Test that specific CSS selectors are preserved."""
        sub_element = {
            "label": "name",
            "selector": ".profile-card .lawyer-name strong"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        assert result == ".profile-card .lawyer-name strong"

    def test_map_generic_selector_preserve_attribute_selectors(self, selector_engine):
        """Test that attribute selectors are preserved."""
        sub_element = {
            "label": "email",
            "selector": "a[href*='mailto:john@example.com']"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        assert result == "a[href*='mailto:john@example.com']"

    def test_map_generic_selector_name_directory_context(self, selector_engine):
        """Test name selector mapping in directory context."""
        sub_element = {
            "label": "name",
            "selector": "strong"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = "strong, p.name strong, h3, h2, .name, [class*='name'] strong, strong:first-of-type"
        assert result == expected

    def test_map_generic_selector_name_profile_context(self, selector_engine):
        """Test name selector mapping in profile context."""
        sub_element = {
            "label": "lawyer_name",
            "selector": "h1"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "profile")
        
        expected = "h1, h2, .entry-title, .page-title, .lawyer-name, .attorney-name"
        assert result == expected

    def test_map_generic_selector_title_directory_context(self, selector_engine):
        """Test title selector mapping in directory context."""
        sub_element = {
            "label": "title",
            "selector": "span"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".title, .position, .job-title, [class*='title'], [class*='position'], p.title span:first-child, span[class*='position']"
        assert result == expected

    def test_map_generic_selector_position_profile_context(self, selector_engine):
        """Test position selector mapping in profile context."""
        sub_element = {
            "label": "position",
            "selector": "p"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "profile")
        
        expected = ".position, .title, .job-title, h2 + p, h1 + p"
        assert result == expected

    def test_map_generic_selector_job_title_enhancement(self, selector_engine):
        """Test job title selector enhancement."""
        sub_element = {
            "label": "job_title",
            "selector": "div"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".title, .position, .job-title, [class*='title'], [class*='position'], p.title span:first-child, span[class*='position']"
        assert result == expected

    def test_map_generic_selector_email_enhancement(self, selector_engine):
        """Test email selector enhancement."""
        sub_element = {
            "label": "email",
            "selector": "a"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = "a[href^='mailto:'], p.contact-details a[href^='mailto:'], .email, [class*='email'], a[href*='@']"
        assert result == expected

    def test_map_generic_selector_mail_label_variant(self, selector_engine):
        """Test mail label variant enhancement."""
        sub_element = {
            "label": "contact_mail",
            "selector": "span"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = "a[href^='mailto:'], p.contact-details a[href^='mailto:'], .email, [class*='email'], a[href*='@']"
        assert result == expected

    def test_map_generic_selector_phone_enhancement(self, selector_engine):
        """Test phone selector enhancement."""
        sub_element = {
            "label": "phone",
            "selector": "span"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = "a[href^='tel:'], .phone, [class*='phone'], a[href*='tel']"
        assert result == expected

    def test_map_generic_selector_sector_directory_context(self, selector_engine):
        """Test sector selector mapping in directory context."""
        sub_element = {
            "label": "sector",
            "selector": "span"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".practice-area, .sector, [class*='practice'], [class*='sector'], p.contact-details span:not([class*='position']), p.title span:last-child, span[class*='practice']"
        assert result == expected

    def test_map_generic_selector_practice_area_profile_context(self, selector_engine):
        """Test practice area selector mapping in profile context."""
        sub_element = {
            "label": "practice_area",
            "selector": "div"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "profile")
        
        expected = ".practice-area, .capabilities, .focus-areas, a[href*='/practice/']"
        assert result == expected

    def test_map_generic_selector_practice_enhancement(self, selector_engine):
        """Test practice selector enhancement."""
        sub_element = {
            "label": "practice",
            "selector": "li"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".practice-area, .sector, [class*='practice'], [class*='sector'], p.contact-details span:not([class*='position']), p.title span:last-child, span[class*='practice']"
        assert result == expected

    def test_map_generic_selector_area_enhancement(self, selector_engine):
        """Test area selector enhancement."""
        sub_element = {
            "label": "focus_area",
            "selector": "span"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".practice-area, .sector, [class*='practice'], [class*='sector'], p.contact-details span:not([class*='position']), p.title span:last-child, span[class*='practice']"
        assert result == expected

    def test_map_generic_selector_profile_link_enhancement(self, selector_engine):
        """Test profile link selector enhancement."""
        sub_element = {
            "label": "profile_link",
            "selector": "a"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = "a[href*='/lawyer/'], a[href*='/attorney/'], a[href*='/people/'], a[href*='/team/'], a"
        assert result == expected

    def test_map_generic_selector_link_enhancement(self, selector_engine):
        """Test link selector enhancement."""
        sub_element = {
            "label": "link",
            "selector": "a"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = "a[href*='/lawyer/'], a[href*='/attorney/'], a[href*='/people/'], a[href*='/team/'], a"
        assert result == expected

    def test_map_generic_selector_url_enhancement(self, selector_engine):
        """Test URL selector enhancement."""
        sub_element = {
            "label": "profile_url",
            "selector": "a"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = "a[href*='/lawyer/'], a[href*='/attorney/'], a[href*='/people/'], a[href*='/team/'], a"
        assert result == expected

    def test_map_generic_selector_email_in_link_label(self, selector_engine):
        """Test email detection in link-related labels."""
        sub_element = {
            "label": "email_link",
            "selector": "a"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        # Should match email first in the chain since "email" is in the label
        expected = "a[href^='mailto:'], p.contact-details a[href^='mailto:'], .email, [class*='email'], a[href*='@']"
        assert result == expected

    def test_map_generic_selector_education_first_child(self, selector_engine):
        """Test education selector for first education item."""
        sub_element = {
            "label": "education",
            "selector": "li"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".education li:first-child, .education li:first-of-type, ul[class*='education'] li:first-child"
        assert result == expected

    def test_map_generic_selector_education2_nth_child(self, selector_engine):
        """Test education2 selector for subsequent education items."""
        sub_element = {
            "label": "education2",
            "selector": "li"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".education li:nth-of-type(n+2), ul[class*='education'] li:nth-of-type(n+2)"
        assert result == expected

    def test_map_generic_selector_credentials_first_child(self, selector_engine):
        """Test credentials selector for first credential item."""
        sub_element = {
            "label": "credentials",
            "selector": "li"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".admissions li:first-child, .bar li:first-child, .credentials li:first-child"
        assert result == expected

    def test_map_generic_selector_creds2_nth_child(self, selector_engine):
        """Test creds2 selector for subsequent credential items."""
        sub_element = {
            "label": "creds2",
            "selector": "li"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".admissions li:nth-of-type(n+2), .bar li:nth-of-type(n+2), .credentials li:nth-of-type(n+2)"
        assert result == expected

    def test_map_generic_selector_admission_enhancement(self, selector_engine):
        """Test admission selector enhancement."""
        sub_element = {
            "label": "bar_admission",
            "selector": "li"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".admissions li:first-child, .bar li:first-child, .credentials li:first-child"
        assert result == expected

    def test_map_generic_selector_bar_enhancement(self, selector_engine):
        """Test bar selector enhancement."""
        sub_element = {
            "label": "bar_info",
            "selector": "span"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = ".admissions li:first-child, .bar li:first-child, .credentials li:first-child"
        assert result == expected

    def test_map_generic_selector_fallback_to_original(self, selector_engine):
        """Test fallback to original selector for unrecognized labels."""
        sub_element = {
            "label": "custom_field",
            "selector": ".custom-selector"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        assert result == ".custom-selector"

    def test_map_generic_selector_empty_label(self, selector_engine):
        """Test handling of empty label."""
        sub_element = {
            "label": "",
            "selector": ".some-selector"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        assert result == ".some-selector"

    def test_map_generic_selector_missing_label(self, selector_engine):
        """Test handling of missing label."""
        sub_element = {
            "selector": ".some-selector"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        assert result == ".some-selector"

    def test_map_generic_selector_missing_selector(self, selector_engine):
        """Test handling of missing selector."""
        sub_element = {
            "label": "name"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        # Even without selector, should enhance based on label
        expected = "strong, p.name strong, h3, h2, .name, [class*='name'] strong, strong:first-of-type"
        assert result == expected

    def test_map_generic_selector_case_insensitive_matching(self, selector_engine):
        """Test that label matching is case-insensitive."""
        sub_element = {
            "label": "NAME",
            "selector": "span"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = "strong, p.name strong, h3, h2, .name, [class*='name'] strong, strong:first-of-type"
        assert result == expected

    def test_map_generic_selector_mixed_case_label(self, selector_engine):
        """Test handling of mixed case labels."""
        sub_element = {
            "label": "Email_Address",
            "selector": "a"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        expected = "a[href^='mailto:'], p.contact-details a[href^='mailto:'], .email, [class*='email'], a[href*='@']"
        assert result == expected

    def test_map_generic_selector_multiple_keyword_match(self, selector_engine):
        """Test selector with multiple matching keywords."""
        sub_element = {
            "label": "job_title_position",  # Matches both 'title' and 'position'
            "selector": "div"
        }
        
        result = selector_engine.map_generic_selector(sub_element, "directory")
        
        # Should match the first applicable keyword ('title')
        expected = ".title, .position, .job-title, [class*='title'], [class*='position'], p.title span:first-child, span[class*='position']"
        assert result == expected

    def test_map_generic_selector_default_context(self, selector_engine):
        """Test selector mapping with default context."""
        sub_element = {
            "label": "name",
            "selector": "strong"
        }
        
        # Test without specifying context (should default to "directory")
        result = selector_engine.map_generic_selector(sub_element)
        
        expected = "strong, p.name strong, h3, h2, .name, [class*='name'] strong, strong:first-of-type"
        assert result == expected