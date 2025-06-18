#!/usr/bin/env python3
"""
Comprehensive unit tests for DataExtractor module.

Tests for data extraction strategies, container processing, and fallback mechanisms.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from src.core.extractors.data_extractor import DataExtractor
from src.core.context import ScrapingContext
from src.models.scraping_template import (
    ScrapingTemplate, 
    ElementSelector, 
    SubElement
)


class TestDataExtractor:
    """Test cases for DataExtractor functionality."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock ScrapingContext for testing."""
        context = Mock(spec=ScrapingContext)
        context.session_logger = Mock()
        context.current_page = Mock()
        context.template = Mock(spec=ScrapingTemplate)
        context.template.elements = []
        return context

    @pytest.fixture
    def mock_page(self):
        """Create a mock page object."""
        page = Mock()
        page.css = Mock()
        page.xpath = Mock()
        page.urljoin = Mock(side_effect=lambda url: f"https://example.com{url}")
        return page

    @pytest.fixture
    def extractor(self, mock_context, mock_page):
        """Create DataExtractor instance with mock context and page."""
        mock_context.current_page = mock_page
        return DataExtractor(mock_context)

    def test_extract_data_success(self, extractor, mock_context):
        """Test successful data extraction."""
        # Create mock element
        element = Mock(spec=ElementSelector)
        element.label = "test_element"
        element.is_required = False
        element.is_container = False
        
        mock_context.template.elements = [element]
        
        # Mock extract_element_data to return test value
        extractor.extract_element_data = Mock(return_value="test_value")
        extractor.merge_related_containers = Mock(side_effect=lambda x: x)
        
        with patch('src.core.extractors.data_extractor.ProgressTracker') as mock_progress:
            mock_progress_instance = Mock()
            mock_progress.return_value = mock_progress_instance
            
            result = extractor.extract_data()
            
            assert result == {"test_element": "test_value"}
            extractor.extract_element_data.assert_called_once_with(element)

    def test_extract_data_with_required_element_failure(self, extractor, mock_context):
        """Test extraction failure with required element."""
        # Create required element that will fail
        element = Mock(spec=ElementSelector)
        element.label = "required_element"
        element.is_required = True
        element.selector = ".test-selector"  # Add selector attribute
        
        mock_context.template.elements = [element]
        
        # Mock extract_element_data to raise exception
        extractor.extract_element_data = Mock(side_effect=Exception("Element not found"))
        
        with patch('src.core.extractors.data_extractor.ProgressTracker'):
            with pytest.raises(Exception, match="Failed to extract required_element"):
                extractor.extract_data()

    def test_extract_data_with_optional_element_failure(self, extractor, mock_context):
        """Test extraction with optional element failure."""
        # Create optional element that will fail
        element = Mock(spec=ElementSelector)
        element.label = "optional_element"
        element.is_required = False
        
        mock_context.template.elements = [element]
        
        # Mock extract_element_data to raise exception
        extractor.extract_element_data = Mock(side_effect=Exception("Element not found"))
        extractor.merge_related_containers = Mock(side_effect=lambda x: x)
        
        with patch('src.core.extractors.data_extractor.ProgressTracker'):
            result = extractor.extract_data()
            
            assert result == {"optional_element": None}

    def test_extract_element_data_container(self, extractor):
        """Test container element extraction."""
        element = Mock(spec=ElementSelector)
        element.is_container = True
        element.label = "container_element"
        
        # Mock extract_container_data
        extractor.extract_container_data = Mock(return_value=[{"name": "John", "title": "Partner"}])
        
        result = extractor.extract_element_data(element)
        
        assert result == [{"name": "John", "title": "Partner"}]
        extractor.extract_container_data.assert_called_once_with(element)

    def test_extract_element_data_single_element(self, extractor, mock_page):
        """Test single element extraction."""
        element = Mock(spec=ElementSelector)
        element.is_container = False
        element.is_multiple = False
        element.is_required = False
        element.label = "single_element"
        
        # Mock element finding
        mock_found_element = Mock()
        mock_found_element.text = "Test Text"
        
        extractor.find_elements_with_fallback = Mock(return_value=[mock_found_element])
        extractor.extract_single_element = Mock(return_value="Test Text")
        
        result = extractor.extract_element_data(element)
        
        assert result == "Test Text"
        extractor.extract_single_element.assert_called_once_with(mock_found_element, element)

    def test_extract_element_data_multiple_elements(self, extractor):
        """Test multiple elements extraction."""
        element = Mock(spec=ElementSelector)
        element.is_container = False
        element.is_multiple = True
        element.is_required = False
        element.label = "multiple_elements"
        
        # Mock multiple elements finding
        mock_elements = [Mock(), Mock()]
        extractor.find_elements_with_fallback = Mock(return_value=mock_elements)
        extractor.extract_multiple_elements = Mock(return_value=["Text1", "Text2"])
        
        result = extractor.extract_element_data(element)
        
        assert result == ["Text1", "Text2"]
        extractor.extract_multiple_elements.assert_called_once_with(mock_elements, element)

    def test_extract_element_data_no_page(self, extractor):
        """Test extraction failure when no page is available."""
        extractor.context.current_page = None
        extractor.current_page = None
        
        element = Mock(spec=ElementSelector)
        
        with pytest.raises(Exception, match="No page available for data extraction"):
            extractor.extract_element_data(element)

    def test_find_elements_with_fallback_success_first_strategy(self, extractor):
        """Test fallback strategy success on first attempt."""
        element = Mock(spec=ElementSelector)
        element.label = "test_element"  # Add missing label attribute
        mock_elements = [Mock(), Mock()]
        
        extractor.try_automatch_selector = Mock(return_value=mock_elements)
        
        result = extractor.find_elements_with_fallback(element)
        
        assert result == mock_elements
        extractor.try_automatch_selector.assert_called_once_with(element)

    def test_find_elements_with_fallback_success_later_strategy(self, extractor):
        """Test fallback strategy success on later attempt."""
        element = Mock(spec=ElementSelector)
        element.label = "test_element"  # Add missing label attribute
        mock_elements = [Mock()]
        
        # First strategies fail, third succeeds
        extractor.try_automatch_selector = Mock(return_value=[])
        extractor.try_semantic_xpath = Mock(return_value=[])
        extractor.try_content_based_selection = Mock(return_value=mock_elements)
        
        result = extractor.find_elements_with_fallback(element)
        
        assert result == mock_elements
        extractor.try_content_based_selection.assert_called_once_with(element)

    def test_find_elements_with_fallback_all_fail(self, extractor):
        """Test fallback when all strategies fail."""
        element = Mock(spec=ElementSelector)
        element.label = "test_element"  # Add missing label attribute
        
        # All strategies return empty
        extractor.try_automatch_selector = Mock(return_value=[])
        extractor.try_semantic_xpath = Mock(return_value=[])
        extractor.try_content_based_selection = Mock(return_value=[])
        extractor.try_structure_based_selection = Mock(return_value=[])
        extractor.try_original_selector = Mock(return_value=[])
        
        result = extractor.find_elements_with_fallback(element)
        
        assert result == []

    def test_extract_single_element_text(self, extractor):
        """Test single element text extraction."""
        element_config = Mock(spec=ElementSelector)
        element_config.element_type = 'text'
        
        mock_element = Mock()
        mock_element.text = "  Sample Text  "
        
        result = extractor.extract_single_element(mock_element, element_config)
        
        assert result == "Sample Text"

    def test_extract_single_element_link(self, extractor):
        """Test single element link extraction."""
        element_config = Mock(spec=ElementSelector)
        element_config.element_type = 'link'
        
        mock_element = Mock()
        # Mock the attrib path since it's checked first
        mock_element.attrib = {'href': '/profile/123'}
        
        result = extractor.extract_single_element(mock_element, element_config)
        
        assert result == "/profile/123"

    def test_extract_single_element_attribute(self, extractor):
        """Test single element attribute extraction."""
        element_config = Mock(spec=ElementSelector)
        element_config.element_type = 'attribute'
        element_config.attribute_name = 'data-id'
        
        mock_element = Mock()
        # Mock the attrib path since it's checked first
        mock_element.attrib = {'data-id': '123'}
        
        result = extractor.extract_single_element(mock_element, element_config)
        
        assert result == "123"

    def test_extract_single_element_html(self, extractor):
        """Test single element HTML extraction."""
        element_config = Mock(spec=ElementSelector)
        element_config.element_type = 'html'
        
        mock_element = Mock()
        # For HTML type, it checks __str__ first
        mock_element.__str__ = Mock(return_value="<div>Content</div>")
        
        result = extractor.extract_single_element(mock_element, element_config)
        
        assert result == "<div>Content</div>"

    def test_extract_multiple_elements(self, extractor):
        """Test multiple elements extraction."""
        element_config = Mock(spec=ElementSelector)
        element_config.element_type = 'text'
        
        mock_elements = [Mock(), Mock(), Mock()]
        mock_elements[0].text = "Text1"
        mock_elements[1].text = "Text2" 
        mock_elements[2].text = ""  # Empty text should be filtered
        
        extractor.extract_single_element = Mock(side_effect=["Text1", "Text2", None])
        
        result = extractor.extract_multiple_elements(mock_elements, element_config)
        
        assert result == ["Text1", "Text2"]

    def test_extract_container_data_success(self, extractor, mock_page):
        """Test successful container data extraction."""
        # Create container element config
        element_config = Mock(spec=ElementSelector)
        element_config.selector = ".profile-card"
        element_config.sub_elements = [
            {"label": "name", "selector": "h3", "element_type": "text"},
            {"label": "title", "selector": ".position", "element_type": "text"}
        ]
        
        # Mock container elements
        mock_container1 = Mock()
        mock_container2 = Mock()
        mock_page.css.return_value = [mock_container1, mock_container2]
        
        # Mock sub-element finding and extraction
        mock_name_element = Mock()
        mock_title_element = Mock()
        mock_container1.css = Mock(side_effect=[[mock_name_element], [mock_title_element]])
        mock_container2.css = Mock(side_effect=[[mock_name_element], [mock_title_element]])
        
        extractor.extract_element_value = Mock(side_effect=["John Doe", "Partner", "Jane Smith", "Associate"])
        
        result = extractor.extract_container_data(element_config)
        
        expected = [
            {"name": "John Doe", "title": "Partner", "_container_index": 0},
            {"name": "Jane Smith", "title": "Associate", "_container_index": 1}
        ]
        
        assert result == expected

    def test_extract_container_data_no_containers_found(self, extractor, mock_page):
        """Test container extraction when no containers found."""
        element_config = Mock(spec=ElementSelector)
        element_config.selector = ".nonexistent"
        
        mock_page.css.return_value = []
        
        result = extractor.extract_container_data(element_config)
        
        assert result == []

    def test_extract_container_data_sub_element_failure(self, extractor, mock_page):
        """Test container extraction with sub-element failure."""
        element_config = Mock(spec=ElementSelector)
        element_config.selector = ".profile-card"
        element_config.sub_elements = [
            {"label": "name", "selector": "h3", "element_type": "text"}
        ]
        
        mock_container = Mock()
        mock_page.css.return_value = [mock_container]
        
        # Sub-element not found
        mock_container.css.return_value = []
        
        result = extractor.extract_container_data(element_config)
        
        expected = [{"name": None, "_container_index": 0}]
        assert result == expected

    def test_try_automatch_selector_css(self, extractor, mock_page):
        """Test AutoMatch with CSS selector."""
        element = Mock(spec=ElementSelector)
        element.selector = ".test-class"
        element.selector_type = "css"
        
        mock_elements = [Mock(), Mock()]
        mock_page.css.return_value = mock_elements
        
        result = extractor.try_automatch_selector(element)
        
        assert result == mock_elements
        mock_page.css.assert_called_once_with(".test-class")

    def test_try_automatch_selector_xpath(self, extractor, mock_page):
        """Test AutoMatch with XPath selector."""
        element = Mock(spec=ElementSelector)
        element.selector = "//div[@class='test']"
        element.selector_type = "xpath"
        
        mock_elements = [Mock()]
        mock_page.xpath.return_value = mock_elements
        
        result = extractor.try_automatch_selector(element)
        
        assert result == mock_elements
        mock_page.xpath.assert_called_once_with("//div[@class='test']")

    def test_try_automatch_selector_xpath_with_prefix(self, extractor, mock_page):
        """Test AutoMatch with XPath selector having xpath: prefix."""
        element = Mock(spec=ElementSelector)
        element.selector = "xpath://div[@class='test']"
        element.selector_type = "xpath"
        
        mock_elements = [Mock()]
        mock_page.xpath.return_value = mock_elements
        
        result = extractor.try_automatch_selector(element)
        
        assert result == mock_elements
        mock_page.xpath.assert_called_once_with("//div[@class='test']")

    def test_try_automatch_selector_xpath_normalize_space(self, extractor, mock_page):
        """Test AutoMatch with normalize-space XPath function."""
        element = Mock(spec=ElementSelector)
        element.selector = "normalize-space(text())"
        element.selector_type = "css"  # Will be detected as XPath
        
        mock_elements = [Mock()]
        mock_page.xpath.return_value = mock_elements
        
        result = extractor.try_automatch_selector(element)
        
        assert result == mock_elements
        mock_page.xpath.assert_called_once_with("//normalize-space(text())")

    def test_try_automatch_selector_xpath_failure(self, extractor, mock_page):
        """Test AutoMatch XPath selector failure."""
        element = Mock(spec=ElementSelector)
        element.selector = "//invalid[@xpath"
        element.selector_type = "xpath"
        
        mock_page.xpath.side_effect = Exception("Invalid XPath")
        
        result = extractor.try_automatch_selector(element)
        
        assert result == []

    def test_merge_related_containers_basic_merge(self, extractor):
        """Test basic container merging functionality."""
        extracted_data = {
            "main_profiles": [
                {"name": "John Doe", "_container_index": 0, "_profile_link": "/john"},
                {"name": "Jane Smith", "_container_index": 1, "_profile_link": "/jane"}
            ],
            "subpage_education": [
                {"education": "Harvard Law", "_container_index": 0, "_profile_link": "/john"},
                {"education": "Yale Law", "_container_index": 1, "_profile_link": "/jane"}
            ]
        }
        
        result = extractor.merge_related_containers(extracted_data)
        
        # Check that education data was merged into main profiles
        assert "main_profiles" in result
        assert len(result["main_profiles"]) == 2
        assert result["main_profiles"][0]["education"] == "Harvard Law"
        assert result["main_profiles"][1]["education"] == "Yale Law"
        # Subpage container should be excluded from final result
        assert "subpage_education" not in result

    def test_merge_related_containers_no_merge_needed(self, extractor):
        """Test when no merging is needed."""
        extracted_data = {
            "single_values": "test_value",
            "simple_list": ["item1", "item2"]
        }
        
        result = extractor.merge_related_containers(extracted_data)
        
        assert result == extracted_data

    def test_merge_related_containers_no_profile_links(self, extractor):
        """Test container merging when profile links are missing."""
        extracted_data = {
            "profiles": [
                {"name": "John Doe", "_container_index": 0, "_profile_link": None},
                {"name": "Jane Smith", "_container_index": 1, "_profile_link": None}
            ],
            "education": [
                {"education": "Harvard Law", "_container_index": 0, "_profile_link": None},
                {"education": "Yale Law", "_container_index": 1, "_profile_link": None}
            ]
        }
        
        result = extractor.merge_related_containers(extracted_data)
        
        # Should merge by container index - education is added directly to main item
        assert "profiles" in result
        assert result["profiles"][0]["education"] == "Harvard Law"
        assert result["profiles"][1]["education"] == "Yale Law"

    def test_extract_element_value_with_urljoin(self, extractor, mock_page):
        """Test element value extraction with URL joining."""
        mock_element = Mock()
        mock_element.get_attribute = Mock(return_value="/relative/path")
        mock_page.urljoin.return_value = "https://example.com/relative/path"
        
        result = extractor.extract_element_value(mock_element, 'link')
        
        assert result == "https://example.com/relative/path"
        mock_page.urljoin.assert_called_once_with("/relative/path")

    def test_extract_element_value_attribute_with_fallback(self, extractor):
        """Test attribute extraction with different element types."""
        # Test with get_attribute method
        mock_element1 = Mock()
        mock_element1.get_attribute = Mock(return_value="test_value")
        
        result1 = extractor.extract_element_value(mock_element1, 'attribute')
        assert result1 == "test_value"
        
        # Test with attrib property
        mock_element2 = Mock()
        mock_element2.attrib = {'value': 'test_value2'}
        delattr(mock_element2, 'get_attribute')  # Remove get_attribute method
        
        result2 = extractor.extract_element_value(mock_element2, 'attribute')
        assert result2 == "test_value2"

    def test_location_specific_element_handling(self, extractor, mock_context):
        """Test handling of location-specific required elements."""
        # Create location-specific required element
        element = Mock(spec=ElementSelector)
        element.label = "office_location"
        element.is_required = True
        element.selector = "//text()[contains(., 'Riyadh')]"
        
        mock_context.template.elements = [element]
        
        # Mock extract_element_data to raise exception
        extractor.extract_element_data = Mock(side_effect=Exception("Element not found"))
        extractor.merge_related_containers = Mock(side_effect=lambda x: x)
        
        with patch('src.core.extractors.data_extractor.ProgressTracker'):
            result = extractor.extract_data()
            
            # Should not raise exception for location-specific element
            assert result == {"office_location": None}

    def test_fallback_strategies_exception_handling(self, extractor):
        """Test that fallback strategies handle exceptions gracefully."""
        element = Mock(spec=ElementSelector)
        element.label = "test_element"
        
        # All strategies raise exceptions
        extractor.try_automatch_selector = Mock(side_effect=Exception("Strategy 1 failed"))
        extractor.try_semantic_xpath = Mock(side_effect=Exception("Strategy 2 failed"))
        extractor.try_content_based_selection = Mock(side_effect=Exception("Strategy 3 failed"))
        extractor.try_structure_based_selection = Mock(side_effect=Exception("Strategy 4 failed"))
        extractor.try_original_selector = Mock(side_effect=Exception("Strategy 5 failed"))
        
        result = extractor.find_elements_with_fallback(element)
        
        assert result == []

    def test_try_original_selector_fallback(self, extractor, mock_page):
        """Test original selector as final fallback."""
        element = Mock(spec=ElementSelector)
        element.selector = ".final-fallback"
        
        mock_elements = [Mock()]
        mock_page.css.return_value = mock_elements
        
        result = extractor.try_original_selector(element)
        
        assert result == mock_elements
        mock_page.css.assert_called_once_with(".final-fallback")

    def test_try_original_selector_exception(self, extractor, mock_page):
        """Test original selector exception handling."""
        element = Mock(spec=ElementSelector)
        element.selector = ".invalid-selector"
        
        mock_page.css.side_effect = Exception("CSS error")
        
        result = extractor.try_original_selector(element)
        
        assert result == []