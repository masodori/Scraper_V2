#!/usr/bin/env python3
"""
Comprehensive unit tests for TemplateAnalyzer module.

Tests for pattern detection, directory detection, and subpage analysis.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any

from src.core.analyzers.template_analyzer import TemplateAnalyzer
from src.core.context import ScrapingContext
from src.models.scraping_template import (
    ScrapingTemplate, 
    ElementSelector, 
    SubElement,
    NavigationAction
)


class TestTemplateAnalyzer:
    """Test cases for TemplateAnalyzer functionality."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock ScrapingContext for testing."""
        context = Mock(spec=ScrapingContext)
        context.session_logger = Mock()
        context.session_logger.debug = Mock()
        return context
    
    def create_mock_template(self, elements=None, actions=None):
        """Helper method to create properly configured mock template."""
        mock_template = Mock(spec=ScrapingTemplate)
        mock_template.elements = elements or []
        mock_template.actions = actions or []
        return mock_template
    
    def create_mock_element(self, **kwargs):
        """Helper method to create properly configured mock element."""
        element = Mock(spec=ElementSelector)
        # Set default values
        element.is_container = kwargs.get('is_container', False)
        element.is_multiple = kwargs.get('is_multiple', False)
        element.selector = kwargs.get('selector', '.default')
        element.sub_elements = kwargs.get('sub_elements', [])
        element.label = kwargs.get('label', 'default_label')
        return element

    @pytest.fixture
    def analyzer(self, mock_context):
        """Create TemplateAnalyzer instance with mock context."""
        return TemplateAnalyzer(mock_context)

    def test_directory_detection_with_container_elements(self, analyzer, mock_context):
        """Test directory detection when template has container elements."""
        # Create template with container element using helper
        container_element = self.create_mock_element(
            is_container=True, 
            is_multiple=False, 
            selector=".profile-card"
        )
        
        mock_template = self.create_mock_template([container_element])
        mock_context.template = mock_template
        
        result = analyzer.looks_like_directory_template()
        assert result is True

    def test_directory_detection_with_multiple_elements(self, analyzer, mock_context):
        """Test directory detection when template has multiple elements."""
        # Create template with multiple elements using helper
        element = self.create_mock_element(
            is_container=False, 
            is_multiple=True, 
            selector=".person-list"
        )
        
        mock_template = self.create_mock_template([element])
        mock_context.template = mock_template
        
        result = analyzer.looks_like_directory_template()
        assert result is True

    def test_directory_detection_with_people_selectors(self, analyzer, mock_context):
        """Test directory detection with people-related selectors."""
        # Create element with people-related selector
        element = Mock(spec=ElementSelector)
        element.is_container = False
        element.is_multiple = False
        element.selector = ".people-grid"
        
        mock_template = self.create_mock_template([element])
        mock_context.template = mock_template
        
        result = analyzer.looks_like_directory_template()
        assert result is True

    def test_directory_detection_with_profile_links(self, analyzer, mock_context):
        """Test directory detection with profile link sub-elements."""
        # Create container with profile link sub-elements
        sub_element = {"label": "profile_link", "selector": "a"}
        
        container_element = Mock(spec=ElementSelector)
        container_element.is_container = False
        container_element.is_multiple = False
        container_element.selector = ".card"
        container_element.sub_elements = [sub_element]
        
        mock_template = self.create_mock_template([container_element])
        mock_context.template = mock_template
        
        result = analyzer.looks_like_directory_template()
        assert result is True

    def test_directory_detection_with_name_title_pattern(self, analyzer, mock_context):
        """Test directory detection with name/title sub-element patterns."""
        # Create container with name and title sub-elements
        sub_elements = [
            {"label": "name", "selector": "h3"},
            {"label": "title", "selector": ".position"}
        ]
        
        container_element = Mock(spec=ElementSelector)
        container_element.is_container = False
        container_element.is_multiple = False
        container_element.selector = ".profile"
        container_element.sub_elements = sub_elements
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        result = analyzer.looks_like_directory_template()
        assert result is True

    def test_directory_detection_negative_case(self, analyzer, mock_context):
        """Test that non-directory templates return False."""
        # Create simple single element template
        element = Mock(spec=ElementSelector)
        element.is_container = False
        element.is_multiple = False
        element.selector = ".single-item"
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        result = analyzer.looks_like_directory_template()
        assert result is False

    def test_subpage_detection_with_subpage_elements(self, analyzer, mock_context):
        """Test subpage detection when elements have subpage_elements defined."""
        # Create element with subpage_elements
        element = Mock(spec=ElementSelector)
        element.subpage_elements = [{"label": "bio", "selector": ".biography"}]
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        result = analyzer.template_needs_subpage_data()
        assert result is True

    def test_subpage_detection_with_education_elements(self, analyzer, mock_context):
        """Test subpage detection with education/credentials sub-elements."""
        # Create container with education sub-elements
        sub_elements = [
            {"label": "education", "selector": ".edu-info"},
            {"label": "credentials", "selector": ".creds"}
        ]
        
        container_element = Mock(spec=ElementSelector)
        container_element.sub_elements = sub_elements
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        result = analyzer.template_needs_subpage_data()
        assert result is True

    def test_subpage_detection_with_multiple_containers(self, analyzer, mock_context):
        """Test subpage detection with multiple containers."""
        # Create multiple containers
        container1 = Mock(spec=ElementSelector)
        container1.is_container = True
        
        container2 = Mock(spec=ElementSelector)
        container2.is_container = True
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        result = analyzer.template_needs_subpage_data()
        assert result is True

    def test_subpage_detection_negative_case(self, analyzer, mock_context):
        """Test that simple templates don't require subpage data."""
        # Create simple template without subpage indicators
        element = Mock(spec=ElementSelector)
        element.is_container = False
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        result = analyzer.template_needs_subpage_data()
        assert result is False

    def test_is_subpage_container_with_subpage_label(self, analyzer, mock_context):
        """Test subpage container detection with subpage-related labels."""
        element = Mock(spec=ElementSelector)
        element.label = "subpage_data"
        
        result = analyzer.is_subpage_container(element)
        assert result is True
        
        # Verify debug logging was called
        mock_context.session_logger.debug.assert_called()

    def test_is_subpage_container_with_education_subelements(self, analyzer, mock_context):
        """Test subpage container detection with education sub-elements."""
        sub_elements = [
            {"label": "education", "selector": ".school"},
            {"label": "bar_admission", "selector": ".bar-info"}
        ]
        
        element = Mock(spec=ElementSelector)
        element.label = "profile_details"
        element.sub_elements = sub_elements
        
        result = analyzer.is_subpage_container(element)
        assert result is True

    def test_is_subpage_container_with_follow_links(self, analyzer, mock_context):
        """Test subpage container detection with follow_links enabled."""
        element = Mock(spec=ElementSelector)
        element.label = "profile_container"
        element.follow_links = True
        
        result = analyzer.is_subpage_container(element)
        assert result is True

    def test_is_subpage_container_negative_case(self, analyzer, mock_context):
        """Test that regular containers are not detected as subpage containers."""
        element = Mock(spec=ElementSelector)
        element.label = "main_content"
        element.follow_links = False
        element.sub_elements = [{"label": "name", "selector": "h1"}]
        
        result = analyzer.is_subpage_container(element)
        assert result is False

    def test_complex_directory_template_scenario(self, analyzer, mock_context):
        """Test complex scenario with multiple directory indicators."""
        # Create complex template with multiple directory indicators
        sub_elements = [
            {"label": "name", "selector": "h3"},
            {"label": "title", "selector": ".position"},
            {"label": "email", "selector": "a[href*='mailto']"},
            {"label": "profile_link", "selector": "a.profile-link"}
        ]
        
        container_element = Mock(spec=ElementSelector)
        container_element.is_container = True
        container_element.is_multiple = True
        container_element.selector = ".people-grid .lawyer-card"
        container_element.sub_elements = sub_elements
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        result = analyzer.looks_like_directory_template()
        assert result is True

    def test_complex_subpage_template_scenario(self, analyzer, mock_context):
        """Test complex scenario with multiple subpage indicators."""
        # Main container
        main_sub_elements = [
            {"label": "name", "selector": "h3"},
            {"label": "profile_link", "selector": "a"}
        ]
        
        main_container = Mock(spec=ElementSelector)
        main_container.is_container = True
        main_container.sub_elements = main_sub_elements
        
        # Subpage container
        subpage_sub_elements = [
            {"label": "education", "selector": ".education-info"},
            {"label": "credentials", "selector": ".credentials"},
            {"label": "experience", "selector": ".experience"}
        ]
        
        subpage_container = Mock(spec=ElementSelector)
        subpage_container.is_container = True
        subpage_container.sub_elements = subpage_sub_elements
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        result = analyzer.template_needs_subpage_data()
        assert result is True

    def test_analyzer_with_actions(self, analyzer, mock_context):
        """Test analyzer behavior with navigation actions."""
        # Create action with profile navigation
        action = Mock(spec=NavigationAction)
        action.label = "profile_link"
        action.target_url = "/lawyer/john-doe"
        
        mock_template = self.create_mock_template([])
        mock_template.actions = [action]
        mock_context.template = mock_template
        
        result = analyzer.looks_like_directory_template()
        assert result is True

    def test_analyzer_handles_missing_attributes(self, analyzer, mock_context):
        """Test that analyzer handles missing attributes gracefully."""
        # Create element with minimal attributes
        element = Mock(spec=ElementSelector)
        element.selector = ".content"
        # Don't set is_container, is_multiple, or sub_elements
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        # Should not raise exceptions
        result = analyzer.looks_like_directory_template()
        assert isinstance(result, bool)
        
        result = analyzer.template_needs_subpage_data()
        assert isinstance(result, bool)

    def test_analyzer_with_empty_template(self, analyzer, mock_context):
        """Test analyzer with empty template."""
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        result = analyzer.looks_like_directory_template()
        assert result is False
        
        result = analyzer.template_needs_subpage_data()
        assert result is False

    def test_sub_element_type_handling(self, analyzer, mock_context):
        """Test handling of different sub-element types (dict vs objects)."""
        # Mix of dict and object sub-elements
        dict_sub = {"label": "name", "selector": "h3"}
        
        obj_sub = Mock()
        obj_sub.label = "email"
        
        sub_elements = [dict_sub, obj_sub]
        
        container_element = Mock(spec=ElementSelector)
        container_element.sub_elements = sub_elements
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        # Should handle both types without errors
        result = analyzer.looks_like_directory_template()
        assert isinstance(result, bool)

    def test_case_insensitive_keyword_matching(self, analyzer, mock_context):
        """Test that keyword matching is case-insensitive."""
        # Test with uppercase keywords
        sub_elements = [{"label": "NAME", "selector": "h3"}]
        
        container_element = Mock(spec=ElementSelector)
        container_element.sub_elements = sub_elements
        
        mock_template = self.create_mock_template([])
        mock_context.template = mock_template
        
        result = analyzer.looks_like_directory_template()
        assert result is True

    def test_logging_calls(self, analyzer, mock_context):
        """Test that logging is called appropriately."""
        element = Mock(spec=ElementSelector)
        element.label = "test_container"
        element.follow_links = False
        element.sub_elements = []
        
        analyzer.is_subpage_container(element)
        
        # Verify that debug logging was called
        mock_context.session_logger.debug.assert_called_once()
        call_args = mock_context.session_logger.debug.call_args[0][0]
        assert "Subpage container check" in call_args
        assert "test_container" in call_args