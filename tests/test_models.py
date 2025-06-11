#!/usr/bin/env python3
"""
Test suite for data models and validation.
"""

import pytest
import json
from datetime import datetime
from pathlib import Path
import tempfile

from src.models.scraping_template import (
    ElementSelector, 
    CookieData, 
    NavigationAction, 
    ScrapingTemplate, 
    ScrapingResult
)


class TestElementSelector:
    """Test cases for ElementSelector model."""
    
    def test_valid_element_selector(self):
        """Test creating a valid element selector."""
        selector = ElementSelector(
            label="test_element",
            selector=".test-class",
            selector_type="css",
            element_type="text"
        )
        
        assert selector.label == "test_element"
        assert selector.selector == ".test-class"
        assert selector.selector_type == "css"
        assert selector.element_type == "text"
        assert selector.is_multiple == False
        assert selector.is_required == True
    
    def test_invalid_selector_type(self):
        """Test validation of selector type."""
        with pytest.raises(ValueError):
            ElementSelector(
                label="test",
                selector=".test",
                selector_type="invalid",
                element_type="text"
            )
    
    def test_invalid_element_type(self):
        """Test validation of element type."""
        with pytest.raises(ValueError):
            ElementSelector(
                label="test",
                selector=".test",
                selector_type="css",
                element_type="invalid"
            )


class TestCookieData:
    """Test cases for CookieData model."""
    
    def test_valid_cookie(self):
        """Test creating a valid cookie."""
        cookie = CookieData(
            name="session_id",
            value="abc123",
            domain=".example.com",
            secure=True
        )
        
        assert cookie.name == "session_id"
        assert cookie.value == "abc123"
        assert cookie.domain == ".example.com"
        assert cookie.secure == True
        assert cookie.path == "/"


class TestNavigationAction:
    """Test cases for NavigationAction model."""
    
    def test_valid_action(self):
        """Test creating a valid navigation action."""
        action = NavigationAction(
            label="next_page",
            selector=".next-btn",
            action_type="click",
            wait_after=2.0
        )
        
        assert action.label == "next_page"
        assert action.selector == ".next-btn"
        assert action.action_type == "click"
        assert action.wait_after == 2.0
    
    def test_invalid_action_type(self):
        """Test validation of action type."""
        with pytest.raises(ValueError):
            NavigationAction(
                label="test",
                selector=".test",
                action_type="invalid"
            )


class TestScrapingTemplate:
    """Test cases for ScrapingTemplate model."""
    
    def test_valid_template(self):
        """Test creating a valid scraping template."""
        template = ScrapingTemplate(
            name="test_template",
            url="https://example.com",
            elements=[
                ElementSelector(
                    label="title",
                    selector="h1",
                    element_type="text"
                )
            ]
        )
        
        assert template.name == "test_template"
        assert template.url == "https://example.com"
        assert len(template.elements) == 1
        assert template.elements[0].label == "title"
    
    def test_invalid_url(self):
        """Test validation of URL."""
        with pytest.raises(ValueError):
            ScrapingTemplate(
                name="test",
                url="not-a-url"
            )
    
    def test_template_json_serialization(self):
        """Test JSON serialization of template."""
        template = ScrapingTemplate(
            name="test_template",
            url="https://example.com",
            elements=[
                ElementSelector(
                    label="title",
                    selector="h1",
                    element_type="text"
                )
            ]
        )
        
        json_str = template.to_json()
        assert isinstance(json_str, str)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["name"] == "test_template"
        assert parsed["url"] == "https://example.com"
    
    def test_template_file_operations(self):
        """Test saving and loading template from file."""
        template = ScrapingTemplate(
            name="test_template",
            url="https://example.com",
            elements=[
                ElementSelector(
                    label="title",
                    selector="h1",
                    element_type="text"
                )
            ]
        )
        
        # Test saving to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            template.save_to_file(f.name)
            
            # Test loading from file
            loaded_template = ScrapingTemplate.load_from_file(f.name)
            
            assert loaded_template.name == template.name
            assert loaded_template.url == template.url
            assert len(loaded_template.elements) == len(template.elements)
            assert loaded_template.elements[0].label == template.elements[0].label
            
            # Cleanup
            Path(f.name).unlink()
    
    def test_get_element_by_label(self):
        """Test getting element by label."""
        template = ScrapingTemplate(
            name="test",
            url="https://example.com",
            elements=[
                ElementSelector(label="title", selector="h1", element_type="text"),
                ElementSelector(label="description", selector="p", element_type="text")
            ]
        )
        
        element = template.get_element_by_label("title")
        assert element is not None
        assert element.label == "title"
        assert element.selector == "h1"
        
        # Test non-existent element
        non_existent = template.get_element_by_label("non_existent")
        assert non_existent is None


class TestScrapingResult:
    """Test cases for ScrapingResult model."""
    
    def test_valid_result(self):
        """Test creating a valid scraping result."""
        result = ScrapingResult(
            template_name="test_template",
            url="https://example.com",
            success=True,
            data={"title": "Test Title"},
            metadata={"elements_found": 1}
        )
        
        assert result.template_name == "test_template"
        assert result.url == "https://example.com"
        assert result.success == True
        assert result.data == {"title": "Test Title"}
        assert result.metadata == {"elements_found": 1}
        assert isinstance(result.scraped_at, datetime)
    
    def test_result_json_serialization(self):
        """Test JSON serialization of result."""
        result = ScrapingResult(
            template_name="test_template",
            url="https://example.com",
            success=True,
            data={"title": "Test Title"}
        )
        
        json_str = result.to_json()
        assert isinstance(json_str, str)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["template_name"] == "test_template"
        assert parsed["success"] == True
    
    def test_result_file_operations(self):
        """Test saving result to file."""
        result = ScrapingResult(
            template_name="test_template",
            url="https://example.com",
            success=True,
            data={"title": "Test Title"}
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            result.save_to_file(f.name)
            
            # Verify file was created and contains valid JSON
            with open(f.name, 'r') as read_file:
                data = json.load(read_file)
                assert data["template_name"] == "test_template"
                assert data["success"] == True
            
            # Cleanup
            Path(f.name).unlink()


if __name__ == "__main__":
    pytest.main([__file__])