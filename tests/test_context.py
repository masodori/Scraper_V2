#!/usr/bin/env python3
"""
Comprehensive unit tests for ScrapingContext module.

Tests for context initialization, state management, and resource coordination.
"""

import pytest
import logging
from unittest.mock import Mock, patch

from src.core.context import ScrapingContext
from src.models.scraping_template import ScrapingTemplate


class TestScrapingContext:
    """Test cases for ScrapingContext functionality."""

    @pytest.fixture
    def mock_template(self):
        """Create a mock ScrapingTemplate for testing."""
        template = Mock(spec=ScrapingTemplate)
        template.name = "test_template"
        template.url = "https://example.com"
        template.elements = []
        return template

    def test_initialization(self, mock_template):
        """Test ScrapingContext initialization."""
        context = ScrapingContext(mock_template)
        
        assert context.template == mock_template
        assert context.fetcher is None
        assert context.current_page is None
        assert isinstance(context.session_logger, logging.Logger)

    def test_session_logger_naming(self, mock_template):
        """Test that session logger is named correctly."""
        context = ScrapingContext(mock_template)
        
        expected_name = f"scrapling_runner.{mock_template.name}"
        assert context.session_logger.name == expected_name

    def test_session_logger_different_templates(self):
        """Test that different templates get different loggers."""
        template1 = Mock(spec=ScrapingTemplate)
        template1.name = "template_one"
        
        template2 = Mock(spec=ScrapingTemplate)
        template2.name = "template_two"
        
        context1 = ScrapingContext(template1)
        context2 = ScrapingContext(template2)
        
        assert context1.session_logger.name == "scrapling_runner.template_one"
        assert context2.session_logger.name == "scrapling_runner.template_two"
        assert context1.session_logger != context2.session_logger

    def test_fetcher_assignment(self, mock_template):
        """Test fetcher assignment."""
        context = ScrapingContext(mock_template)
        mock_fetcher = Mock()
        
        context.fetcher = mock_fetcher
        
        assert context.fetcher == mock_fetcher

    def test_current_page_assignment(self, mock_template):
        """Test current page assignment."""
        context = ScrapingContext(mock_template)
        mock_page = Mock()
        
        context.current_page = mock_page
        
        assert context.current_page == mock_page

    def test_template_immutability_intention(self, mock_template):
        """Test that template reference is maintained."""
        context = ScrapingContext(mock_template)
        original_template = context.template
        
        # Template should remain the same reference
        assert context.template is original_template

    def test_logger_hierarchy(self, mock_template):
        """Test that logger follows correct hierarchy."""
        context = ScrapingContext(mock_template)
        
        # Logger should be under scrapling_runner hierarchy
        assert context.session_logger.name.startswith("scrapling_runner.")

    def test_context_with_special_characters_in_template_name(self):
        """Test context creation with special characters in template name."""
        template = Mock(spec=ScrapingTemplate)
        template.name = "test-template_with.special@chars"
        
        context = ScrapingContext(template)
        
        expected_name = "scrapling_runner.test-template_with.special@chars"
        assert context.session_logger.name == expected_name

    def test_context_with_empty_template_name(self):
        """Test context creation with empty template name."""
        template = Mock(spec=ScrapingTemplate)
        template.name = ""
        
        context = ScrapingContext(template)
        
        assert context.session_logger.name == "scrapling_runner."

    def test_context_state_independence(self, mock_template):
        """Test that context instances are independent."""
        context1 = ScrapingContext(mock_template)
        context2 = ScrapingContext(mock_template)
        
        mock_fetcher1 = Mock()
        mock_fetcher2 = Mock()
        mock_page1 = Mock()
        mock_page2 = Mock()
        
        context1.fetcher = mock_fetcher1
        context1.current_page = mock_page1
        
        context2.fetcher = mock_fetcher2
        context2.current_page = mock_page2
        
        # Contexts should be independent
        assert context1.fetcher != context2.fetcher
        assert context1.current_page != context2.current_page

    def test_logger_functionality(self, mock_template):
        """Test that logger can actually log messages."""
        context = ScrapingContext(mock_template)
        
        with patch.object(context.session_logger, 'info') as mock_info:
            context.session_logger.info("Test message")
            mock_info.assert_called_once_with("Test message")

    def test_logger_level_inheritance(self, mock_template):
        """Test that logger inherits from root logger configuration."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            context = ScrapingContext(mock_template)
            
            # Should call getLogger with correct name
            mock_get_logger.assert_called_once_with(f"scrapling_runner.{mock_template.name}")
            assert context.session_logger == mock_logger

    def test_context_attribute_access(self, mock_template):
        """Test accessing all context attributes."""
        context = ScrapingContext(mock_template)
        
        # All attributes should be accessible
        assert hasattr(context, 'template')
        assert hasattr(context, 'fetcher')
        assert hasattr(context, 'current_page')
        assert hasattr(context, 'session_logger')

    def test_context_with_none_template(self):
        """Test context creation with None template (edge case)."""
        with pytest.raises(AttributeError):
            # This should fail when trying to access template.name
            ScrapingContext(None)

    def test_context_logger_is_logger_instance(self, mock_template):
        """Test that session_logger is actually a Logger instance."""
        context = ScrapingContext(mock_template)
        
        assert isinstance(context.session_logger, logging.Logger)

    def test_multiple_contexts_same_template(self, mock_template):
        """Test multiple contexts with same template."""
        context1 = ScrapingContext(mock_template)
        context2 = ScrapingContext(mock_template)
        
        # Should have same template but potentially same logger name
        assert context1.template == context2.template
        assert context1.session_logger.name == context2.session_logger.name
        
        # But should be independent instances
        assert context1 is not context2

    def test_context_template_access(self, mock_template):
        """Test accessing template properties through context."""
        context = ScrapingContext(mock_template)
        
        # Should be able to access template properties
        assert context.template.name == mock_template.name
        assert context.template.url == mock_template.url
        assert context.template.elements == mock_template.elements

    def test_context_as_shared_state_container(self, mock_template):
        """Test context as a shared state container for components."""
        context = ScrapingContext(mock_template)
        
        # Add mock fetcher and page
        mock_fetcher = Mock()
        mock_page = Mock()
        
        context.fetcher = mock_fetcher
        context.current_page = mock_page
        
        # Should be accessible as shared state
        assert context.fetcher == mock_fetcher
        assert context.current_page == mock_page
        assert context.template == mock_template

    def test_logger_configuration_persistence(self, mock_template):
        """Test that logger configuration persists."""
        context = ScrapingContext(mock_template)
        original_logger = context.session_logger
        
        # Logger should remain the same instance
        assert context.session_logger is original_logger

    def test_context_resource_coordination_pattern(self, mock_template):
        """Test context use for resource coordination."""
        context = ScrapingContext(mock_template)
        
        # Simulate component coordination through context
        mock_fetcher = Mock()
        mock_page = Mock()
        
        # Component 1 sets up fetcher
        context.fetcher = mock_fetcher
        
        # Component 2 uses fetcher to get page
        context.current_page = mock_page
        
        # Component 3 can access both
        assert context.fetcher == mock_fetcher
        assert context.current_page == mock_page

    def test_context_logging_namespace_isolation(self):
        """Test that different templates have isolated logging namespaces."""
        template_a = Mock(spec=ScrapingTemplate)
        template_a.name = "site_a_scraper"
        
        template_b = Mock(spec=ScrapingTemplate)
        template_b.name = "site_b_scraper"
        
        context_a = ScrapingContext(template_a)
        context_b = ScrapingContext(template_b)
        
        # Should have different logging namespaces
        assert "site_a_scraper" in context_a.session_logger.name
        assert "site_b_scraper" in context_b.session_logger.name
        assert context_a.session_logger.name != context_b.session_logger.name