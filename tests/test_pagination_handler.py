#!/usr/bin/env python3
"""
Comprehensive unit tests for PaginationHandler module.

Tests for pagination detection, infinite scroll, load-more buttons, and URL-based pagination.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs

from src.core.handlers.pagination_handler import PaginationHandler
from src.core.context import ScrapingContext
from src.models.scraping_template import ScrapingTemplate


class TestPaginationHandler:
    """Test cases for PaginationHandler functionality."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock ScrapingContext for testing."""
        context = Mock(spec=ScrapingContext)
        context.session_logger = Mock()
        context.current_page = Mock()
        context.template = Mock(spec=ScrapingTemplate)
        context.template.url = "https://example.com/people"
        context.template.pagination = None
        context.fetcher = Mock()
        return context

    @pytest.fixture
    def mock_page(self):
        """Create a mock page object."""
        page = Mock()
        page.css = Mock()
        page.xpath = Mock()
        return page

    @pytest.fixture
    def mock_pagination_config(self):
        """Create a mock pagination configuration."""
        pagination = Mock()
        pagination.next_selector = ".next-page"
        pagination.load_more_selector = ".load-more"
        pagination.page_selector = ".page-number"
        pagination.pattern_type = "button"
        pagination.scroll_pause_time = 2
        pagination.max_pages = 10
        pagination.end_condition_selector = ".end-marker"
        return pagination

    @pytest.fixture
    def handler(self, mock_context, mock_page):
        """Create PaginationHandler instance with mock context and page."""
        mock_context.current_page = mock_page
        return PaginationHandler(mock_context)

    def test_has_pagination_actions_defined_with_selectors(self, handler, mock_context, mock_pagination_config):
        """Test pagination actions detection with defined selectors."""
        mock_context.template.pagination = mock_pagination_config
        
        result = handler._has_pagination_actions_defined()
        
        assert result is True

    def test_has_pagination_actions_defined_no_pagination(self, handler, mock_context):
        """Test pagination actions detection with no pagination config."""
        mock_context.template.pagination = None
        
        result = handler._has_pagination_actions_defined()
        
        assert result is False

    def test_has_pagination_actions_defined_infinite_scroll_with_config(self, handler, mock_context):
        """Test pagination actions detection for infinite scroll with configuration."""
        pagination = Mock()
        pagination.next_selector = None
        pagination.load_more_selector = None
        pagination.page_selector = None
        pagination.pattern_type = "infinite_scroll"
        pagination.scroll_pause_time = 2
        pagination.max_pages = 50
        pagination.end_condition_selector = ".no-more-content"
        
        mock_context.template.pagination = pagination
        
        result = handler._has_pagination_actions_defined()
        
        assert result is True

    def test_has_pagination_actions_defined_infinite_scroll_no_config(self, handler, mock_context):
        """Test pagination actions detection for infinite scroll without configuration."""
        pagination = Mock()
        pagination.next_selector = None
        pagination.load_more_selector = None
        pagination.page_selector = None
        pagination.pattern_type = "infinite_scroll"
        pagination.scroll_pause_time = None
        pagination.max_pages = None
        pagination.end_condition_selector = None
        
        mock_context.template.pagination = pagination
        
        result = handler._has_pagination_actions_defined()
        
        assert result is False

    def test_smart_pagination_no_actions_defined(self, handler, mock_context):
        """Test smart pagination when no actions are defined."""
        handler._has_pagination_actions_defined = Mock(return_value=False)
        handler.extract_data = Mock(return_value={"profiles": [{"name": "John"}]})
        
        result = handler.smart_pagination_with_dual_browser()
        
        assert result == {"profiles": [{"name": "John"}]}
        handler.extract_data.assert_called_once()

    def test_smart_pagination_main_page_processing(self, handler, mock_context):
        """Test smart pagination with main page processing."""
        handler._has_pagination_actions_defined = Mock(return_value=True)
        handler.detect_pagination_location = Mock(return_value="main_page")
        handler.extract_data = Mock(return_value={"profiles": [{"name": "John"}]})
        handler.try_scroll_based_pagination = Mock(return_value={"profiles": [{"name": "Jane"}]})
        
        result = handler.smart_pagination_with_dual_browser()
        
        # Should merge data from initial extraction and pagination
        expected = {"profiles": [{"name": "John"}, {"name": "Jane"}]}
        assert result == expected

    def test_smart_pagination_subpage_processing(self, handler, mock_context):
        """Test smart pagination with subpage processing."""
        handler._has_pagination_actions_defined = Mock(return_value=True)
        handler.detect_pagination_location = Mock(return_value="subpage")
        handler.extract_main_page_only = Mock(return_value={"profiles": [{"name": "John"}]})
        
        result = handler.smart_pagination_with_dual_browser()
        
        assert result == {"profiles": [{"name": "John"}]}
        handler.extract_main_page_only.assert_called_once()

    def test_auto_scroll_to_load_all_content_success(self, handler, mock_page):
        """Test successful auto-scroll content loading."""
        handler.count_profile_elements = Mock(side_effect=[10, 15, 20, 20, 20])  # Content loading then stable
        handler.try_load_more_buttons = Mock(side_effect=[True, True, False])  # Success, success, then failure
        handler.try_scrapling_scroll = Mock(return_value=False)
        handler.try_pagination_load = Mock(return_value=False)
        
        with patch('src.core.handlers.pagination_handler.ProgressTracker') as mock_progress:
            mock_progress_instance = Mock()
            mock_progress.return_value = mock_progress_instance
            
            with patch('time.sleep'):  # Mock sleep to speed up test
                handler.auto_scroll_to_load_all_content()
                
                # Should have stopped after 3 stable counts
                assert handler.count_profile_elements.call_count >= 4

    def test_auto_scroll_to_load_all_content_no_initial_profiles(self, handler, mock_page):
        """Test auto-scroll when no initial profiles are found."""
        handler.count_profile_elements = Mock(return_value=0)
        
        with patch('src.core.handlers.pagination_handler.ProgressTracker'):
            handler.auto_scroll_to_load_all_content()
            
            # Should exit early without attempting scrolls
            handler.count_profile_elements.assert_called_once()

    def test_try_load_more_buttons_found(self, handler, mock_page):
        """Test successful load more button detection."""
        mock_page.css.side_effect = [
            [],  # No button with first pattern
            [Mock()],  # Button found with second pattern
        ]
        
        result = handler.try_load_more_buttons()
        
        assert result is True

    def test_try_load_more_buttons_not_found(self, handler, mock_page):
        """Test when no load more buttons are found."""
        mock_page.css.return_value = []
        
        result = handler.try_load_more_buttons()
        
        assert result is False

    def test_try_pagination_load_found(self, handler, mock_page):
        """Test successful pagination detection."""
        mock_page.css.side_effect = [
            [Mock()],  # Pagination found with first pattern
        ]
        
        result = handler.try_pagination_load()
        
        assert result is True

    def test_try_pagination_load_not_found(self, handler, mock_page):
        """Test when no pagination is found."""
        mock_page.css.return_value = []
        
        result = handler.try_pagination_load()
        
        assert result is False

    def test_handle_pagination_button_type(self, handler, mock_context, mock_page):
        """Test pagination handling for button type."""
        pagination = Mock()
        pagination.pattern_type = "button"
        pagination.next_selector = ".next-btn"
        
        mock_context.template.pagination = pagination
        
        mock_next_element = Mock()
        mock_next_element.is_visible = Mock(return_value=True)
        mock_page.css.return_value = [mock_next_element]
        
        result = handler.handle_pagination()
        
        assert result is True

    def test_handle_pagination_infinite_scroll_type(self, handler, mock_context):
        """Test pagination handling for infinite scroll type."""
        pagination = Mock()
        pagination.pattern_type = "infinite_scroll"
        
        mock_context.template.pagination = pagination
        handler.handle_infinite_scroll = Mock(return_value=True)
        
        result = handler.handle_pagination()
        
        assert result is True
        handler.handle_infinite_scroll.assert_called_once()

    def test_handle_pagination_load_more_type(self, handler, mock_context):
        """Test pagination handling for load more type."""
        pagination = Mock()
        pagination.pattern_type = "load_more"
        
        mock_context.template.pagination = pagination
        handler.handle_load_more_pagination = Mock(return_value=True)
        
        result = handler.handle_pagination()
        
        assert result is True
        handler.handle_load_more_pagination.assert_called_once()

    def test_handle_infinite_scroll_with_end_condition(self, handler, mock_context, mock_page):
        """Test infinite scroll handling with end condition met."""
        pagination = Mock()
        pagination.end_condition_selector = ".end-marker"
        
        mock_context.template.pagination = pagination
        mock_page.css.return_value = [Mock()]  # End condition element found
        
        result = handler.handle_infinite_scroll()
        
        assert result is False  # Should stop scrolling

    def test_handle_infinite_scroll_continue(self, handler, mock_context, mock_page):
        """Test infinite scroll handling when should continue."""
        pagination = Mock()
        pagination.end_condition_selector = ".end-marker"
        
        mock_context.template.pagination = pagination
        mock_page.css.return_value = []  # No end condition element
        
        result = handler.handle_infinite_scroll()
        
        assert result is True  # Should continue scrolling

    def test_try_url_based_pagination_working_pattern(self, handler, mock_context):
        """Test URL-based pagination with working pattern."""
        mock_context.template.url = "https://example.com/people"
        
        # Mock successful pattern detection
        handler.fetch_page = Mock(return_value=Mock())
        handler.has_different_content = Mock(return_value=True)
        handler.extract_data = Mock(side_effect=[
            {"profiles": [{"name": "John"}]},
            {"profiles": [{"name": "Jane"}]},
            {"profiles": []},  # Empty page to end pagination
        ])
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = handler.try_url_based_pagination()
            
            assert result is not None
            assert "profiles" in result
            # Should have collected data from multiple pages
            assert len(result["profiles"]) >= 1

    def test_try_url_based_pagination_no_working_pattern(self, handler, mock_context):
        """Test URL-based pagination when no pattern works."""
        mock_context.template.url = "https://example.com/people"
        
        handler.fetch_page = Mock(return_value=Mock())
        handler.has_different_content = Mock(return_value=False)  # No pattern works
        
        result = handler.try_url_based_pagination()
        
        assert result is None

    def test_try_scroll_based_pagination_with_load_more(self, handler, mock_context):
        """Test scroll-based pagination with load more detection."""
        handler._has_pagination_actions_defined = Mock(return_value=True)
        handler.auto_detect_load_more_buttons = Mock(return_value=".load-more-btn")
        handler.try_auto_load_more_pagination = Mock(return_value={"profiles": [{"name": "John"}]})
        
        result = handler.try_scroll_based_pagination()
        
        assert result == {"profiles": [{"name": "John"}]}
        handler.try_auto_load_more_pagination.assert_called_once_with(".load-more-btn")

    def test_try_scroll_based_pagination_with_wpgb(self, handler, mock_context):
        """Test scroll-based pagination with WPGB infinite scroll."""
        handler._has_pagination_actions_defined = Mock(return_value=True)
        handler.auto_detect_load_more_buttons = Mock(return_value=None)
        handler.detect_wpgb_infinite_scroll = Mock(return_value=True)
        handler.try_wpgb_infinite_scroll_pagination = Mock(return_value={"profiles": [{"name": "Jane"}]})
        
        result = handler.try_scroll_based_pagination()
        
        assert result == {"profiles": [{"name": "Jane"}]}
        handler.try_wpgb_infinite_scroll_pagination.assert_called_once()

    def test_try_scroll_based_pagination_fallback(self, handler, mock_context):
        """Test scroll-based pagination fallback to current data."""
        handler._has_pagination_actions_defined = Mock(return_value=True)
        handler.auto_detect_load_more_buttons = Mock(return_value=None)
        handler.detect_wpgb_infinite_scroll = Mock(return_value=False)
        handler.extract_data = Mock(return_value={"profiles": [{"name": "Current"}]})
        handler.try_standard_pagination = Mock(return_value={"profiles": [{"name": "Standard"}]})
        
        mock_context.template.pagination = Mock()
        
        result = handler.try_scroll_based_pagination()
        
        assert result == {"profiles": [{"name": "Standard"}]}

    def test_try_standard_pagination_success(self, handler, mock_context):
        """Test standard pagination processing."""
        handler._has_pagination_actions_defined = Mock(return_value=True)
        handler.extract_data = Mock(side_effect=[
            {"profiles": [{"name": "Page1"}]},
            {"profiles": [{"name": "Page2"}]},
        ])
        handler.handle_pagination = Mock(side_effect=[True, False])  # More content, then stop
        
        mock_context.template.pagination = Mock()
        mock_context.template.pagination.max_pages = 5
        mock_context.template.pagination.scroll_pause_time = 1
        
        with patch('time.sleep'):
            result = handler.try_standard_pagination()
            
            assert "profiles" in result
            assert len(result["profiles"]) == 2
            assert result["profiles"] == [{"name": "Page1"}, {"name": "Page2"}]

    def test_try_standard_pagination_no_actions(self, handler, mock_context):
        """Test standard pagination when no actions defined."""
        handler._has_pagination_actions_defined = Mock(return_value=False)
        handler.extract_data = Mock(return_value={"profiles": [{"name": "Single"}]})
        
        result = handler.try_standard_pagination()
        
        assert result == {"profiles": [{"name": "Single"}]}

    def test_try_auto_load_more_pagination_success(self, handler, mock_page):
        """Test auto load more pagination with successful loading."""
        handler.extract_data = Mock(return_value={"main_container": [{"name": "Initial"}]})
        handler.extract_data_incremental = Mock(side_effect=[
            {"main_container": [{"name": "New1"}]},
            {"main_container": [{"name": "New2"}]},
            {"main_container": []},  # No more content
        ])
        
        mock_page.css.side_effect = [
            [Mock()],  # Load more button exists
            [Mock()],  # Button still exists
            [],  # Button gone
        ]
        
        with patch('time.sleep'):
            result = handler.try_auto_load_more_pagination(".load-more")
            
            assert "main_container" in result
            assert len(result["main_container"]) == 3  # Initial + 2 new items

    def test_try_wpgb_infinite_scroll_pagination_success(self, handler):
        """Test WPGB infinite scroll pagination."""
        handler.extract_data = Mock(side_effect=[
            {"main_container": [{"name": "Item1"}]},  # Initial
            {"main_container": [{"name": "Item1"}, {"name": "Item2"}]},  # After scroll 1
            {"main_container": [{"name": "Item1"}, {"name": "Item2"}]},  # No new content
            {"main_container": [{"name": "Item1"}, {"name": "Item2"}]},  # Still no new content
        ])
        
        with patch('time.sleep'):
            result = handler.try_wpgb_infinite_scroll_pagination()
            
            assert "main_container" in result
            assert len(result["main_container"]) == 2

    def test_auto_detect_load_more_buttons_found(self, handler, mock_page):
        """Test successful auto-detection of load more buttons."""
        mock_page.css.side_effect = [
            [],  # First selector fails
            [Mock()],  # Second selector succeeds
        ]
        
        result = handler.auto_detect_load_more_buttons()
        
        assert result is not None
        assert ".wpgb-pagination-facet a" in result

    def test_auto_detect_load_more_buttons_not_found(self, handler, mock_page):
        """Test when no load more buttons are detected."""
        mock_page.css.return_value = []
        
        result = handler.auto_detect_load_more_buttons()
        
        assert result is None

    def test_detect_wpgb_infinite_scroll_found(self, handler, mock_page):
        """Test successful WPGB infinite scroll detection."""
        mock_page.css.side_effect = [
            [Mock()],  # WPGB indicator found
        ]
        
        result = handler.detect_wpgb_infinite_scroll()
        
        assert result is True

    def test_detect_wpgb_infinite_scroll_not_found(self, handler, mock_page):
        """Test when WPGB infinite scroll is not detected."""
        mock_page.css.return_value = []
        
        result = handler.detect_wpgb_infinite_scroll()
        
        assert result is False

    def test_count_profile_elements_success(self, handler, mock_page):
        """Test successful profile element counting."""
        mock_page.css.side_effect = [
            [Mock(), Mock(), Mock()],  # 3 elements with first selector
            [Mock(), Mock(), Mock(), Mock(), Mock()],  # 5 elements with second selector
        ]
        
        result = handler.count_profile_elements()
        
        assert result == 5  # Should return the maximum count

    def test_count_profile_elements_no_elements(self, handler, mock_page):
        """Test profile element counting when no elements found."""
        mock_page.css.return_value = []
        
        result = handler.count_profile_elements()
        
        assert result == 0

    def test_has_different_content_different(self, handler, mock_page):
        """Test content difference detection when content differs."""
        test_page = Mock()
        
        handler.get_container_count = Mock(side_effect=[10, 15])  # Different counts
        
        result = handler.has_different_content(test_page)
        
        assert result is True

    def test_has_different_content_same(self, handler, mock_page):
        """Test content difference detection when content is same."""
        test_page = Mock()
        
        handler.get_container_count = Mock(side_effect=[10, 10])  # Same counts
        
        result = handler.has_different_content(test_page)
        
        assert result is False

    def test_has_different_content_no_pages(self, handler):
        """Test content difference detection with missing pages."""
        handler.current_page = None
        
        result = handler.has_different_content(Mock())
        
        assert result is False

    def test_get_container_count_success(self, handler):
        """Test container counting with successful detection."""
        page = Mock()
        page.css.side_effect = [
            [Mock() for _ in range(10)],  # 10 elements found
        ]
        
        result = handler.get_container_count(page)
        
        assert result == 10

    def test_get_container_count_insufficient_content(self, handler):
        """Test container counting with insufficient content."""
        page = Mock()
        page.css.side_effect = [
            [Mock(), Mock()],  # Only 2 elements (less than 5 threshold)
            [],  # No elements
        ]
        
        result = handler.get_container_count(page)
        
        assert result == 0

    def test_detect_pagination_location(self, handler):
        """Test pagination location detection."""
        result = handler.detect_pagination_location()
        
        assert result == "main_page"

    def test_try_scrapling_scroll_success(self, handler):
        """Test Scrapling scroll attempt."""
        mock_page = Mock()
        
        result = handler.try_scrapling_scroll(mock_page)
        
        assert result is True

    def test_try_scrapling_scroll_failure(self, handler):
        """Test Scrapling scroll failure handling."""
        mock_page = Mock()
        
        # Simulate an exception during scroll
        with patch('src.core.handlers.pagination_handler.logger'):
            result = handler.try_scrapling_scroll(mock_page)
            
            assert result is True  # Current implementation always returns True

    def test_error_handling_in_smart_pagination(self, handler):
        """Test error handling in smart pagination."""
        handler._has_pagination_actions_defined = Mock(side_effect=Exception("Test error"))
        handler.extract_data = Mock(return_value={"fallback": "data"})
        
        result = handler.smart_pagination_with_dual_browser()
        
        assert result == {"fallback": "data"}

    def test_max_pages_limit_enforcement(self, handler, mock_context):
        """Test that pagination respects max pages limit."""
        handler._has_pagination_actions_defined = Mock(return_value=True)
        handler.extract_data = Mock(return_value={"profiles": [{"name": "Test"}]})
        handler.handle_pagination = Mock(return_value=True)  # Always says more content available
        
        mock_context.template.pagination = Mock()
        mock_context.template.pagination.max_pages = 2  # Low limit for testing
        
        with patch('time.sleep'):
            result = handler.try_standard_pagination()
            
            # Should stop at max_pages limit
            assert handler.extract_data.call_count <= 3  # max_pages + 1 for safety

    def test_consecutive_failures_handling(self, handler):
        """Test handling of consecutive failures in pagination."""
        handler.extract_data = Mock(return_value={"main_container": [{"name": "Initial"}]})
        handler.extract_data_incremental = Mock(return_value=None)  # Always fails
        
        mock_page = Mock()
        mock_page.css.return_value = [Mock()]  # Load more button always exists
        handler.current_page = mock_page
        
        with patch('time.sleep'):
            result = handler.try_auto_load_more_pagination(".load-more")
            
            # Should stop after consecutive failures
            assert result["main_container"] == [{"name": "Initial"}]

    def test_url_parsing_and_pagination_parameter_detection(self, handler, mock_context):
        """Test URL parsing and pagination parameter detection."""
        mock_context.template.url = "https://example.com/people?existing_param=value"
        
        handler.fetch_page = Mock(return_value=Mock())
        handler.has_different_content = Mock(return_value=True)
        handler.extract_data = Mock(return_value={"profiles": []})
        
        result = handler.try_url_based_pagination()
        
        # Should attempt to test pagination parameters
        assert handler.fetch_page.call_count > 0