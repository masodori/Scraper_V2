#!/usr/bin/env python3
"""
Test suite for Scrapling integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from pathlib import Path

from src.core.scrapling_runner_refactored import ScraplingRunner
from src.models.scraping_template import (
    ScrapingTemplate, 
    ElementSelector, 
    NavigationAction,
    ScrapingResult
)


class TestScraplingRunner:
    """Test cases for ScraplingRunner."""
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample template for testing."""
        return ScrapingTemplate(
            name="test_template",
            url="https://example.com",
            elements=[
                ElementSelector(
                    label="title",
                    selector="h1",
                    element_type="text",
                    is_required=True
                ),
                ElementSelector(
                    label="description",
                    selector=".description",
                    element_type="text",
                    is_required=False
                )
            ],
            actions=[
                NavigationAction(
                    label="next_page",
                    selector=".next-btn",
                    action_type="click"
                )
            ]
        )
    
    def test_runner_initialization(self, sample_template):
        """Test ScraplingRunner initialization."""
        runner = ScraplingRunner(sample_template)
        
        assert runner.template == sample_template
        assert runner.fetcher is None
        assert runner.current_page is None
    
    @patch('src.core.scrapling_runner.StealthyFetcher')
    def test_initialize_fetcher_stealth_mode(self, mock_fetcher, sample_template):
        """Test fetcher initialization in stealth mode."""
        sample_template.stealth_mode = True
        runner = ScraplingRunner(sample_template)
        
        runner._initialize_fetcher()
        assert runner.fetcher is not None
    
    @patch('src.core.scrapling_runner.PlayWrightFetcher')
    def test_initialize_fetcher_standard_mode(self, mock_fetcher, sample_template):
        """Test fetcher initialization in standard mode."""
        sample_template.stealth_mode = False
        runner = ScraplingRunner(sample_template)
        
        runner._initialize_fetcher()
        assert runner.fetcher is not None
    
    def test_format_cookies_for_scrapling(self, sample_template):
        """Test cookie formatting for Scrapling."""
        from src.models.scraping_template import CookieData
        
        sample_template.cookies = [
            CookieData(
                name="session_id",
                value="abc123",
                domain=".example.com",
                secure=True
            )
        ]
        
        runner = ScraplingRunner(sample_template)
        cookies = runner._format_cookies_for_scrapling()
        
        assert len(cookies) == 1
        assert cookies[0]["name"] == "session_id"
        assert cookies[0]["value"] == "abc123"
        assert cookies[0]["domain"] == ".example.com"
        assert cookies[0]["secure"] == True
    
    def test_extract_single_element_text(self, sample_template):
        """Test extracting text from a single element."""
        runner = ScraplingRunner(sample_template)
        
        # Mock element with text attribute
        mock_element = Mock()
        mock_element.text = "Test Title"
        
        element_config = ElementSelector(
            label="title",
            selector="h1",
            element_type="text"
        )
        
        result = runner._extract_single_element(mock_element, element_config)
        assert result == "Test Title"
    
    def test_extract_single_element_link(self, sample_template):
        """Test extracting link from a single element."""
        runner = ScraplingRunner(sample_template)
        
        # Mock element with attrib
        mock_element = Mock()
        mock_element.attrib = {"href": "https://example.com/link"}
        
        element_config = ElementSelector(
            label="link",
            selector="a",
            element_type="link"
        )
        
        result = runner._extract_single_element(mock_element, element_config)
        assert result == "https://example.com/link"
    
    def test_extract_single_element_attribute(self, sample_template):
        """Test extracting attribute from a single element."""
        runner = ScraplingRunner(sample_template)
        
        # Mock element with attrib
        mock_element = Mock()
        mock_element.attrib = {"data-id": "123"}
        
        element_config = ElementSelector(
            label="data_id",
            selector="[data-id]",
            element_type="attribute",
            attribute_name="data-id"
        )
        
        result = runner._extract_single_element(mock_element, element_config)
        assert result == "123"
    
    def test_extract_multiple_elements(self, sample_template):
        """Test extracting data from multiple elements."""
        runner = ScraplingRunner(sample_template)
        
        # Mock multiple elements
        mock_elements = [
            Mock(text="Title 1"),
            Mock(text="Title 2"),
            Mock(text="Title 3")
        ]
        
        element_config = ElementSelector(
            label="titles",
            selector="h2",
            element_type="text",
            is_multiple=True
        )
        
        result = runner._extract_multiple_elements(mock_elements, element_config)
        assert result == ["Title 1", "Title 2", "Title 3"]
    
    def test_flatten_data_simple(self, sample_template):
        """Test flattening simple data structure."""
        runner = ScraplingRunner(sample_template)
        
        data = {
            "title": "Test Title",
            "description": "Test Description",
            "price": "$19.99"
        }
        
        flattened = runner._flatten_data(data)
        assert flattened == data
    
    def test_flatten_data_with_lists(self, sample_template):
        """Test flattening data with lists."""
        runner = ScraplingRunner(sample_template)
        
        data = {
            "title": "Test Title",
            "tags": ["tag1", "tag2", "tag3"],
            "single_item": ["only_one"]
        }
        
        flattened = runner._flatten_data(data)
        assert flattened["title"] == "Test Title"
        assert flattened["tags_1"] == "tag1"
        assert flattened["tags_2"] == "tag2"
        assert flattened["tags_3"] == "tag3"
        assert flattened["single_item"] == "only_one"
    
    def test_export_json(self, sample_template):
        """Test JSON export functionality."""
        runner = ScraplingRunner(sample_template)
        
        result = ScrapingResult(
            template_name="test",
            url="https://example.com",
            success=True,
            data={"title": "Test Title"}
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            runner._export_json(result, f.name)
            
            # Verify file contents
            with open(f.name, 'r') as read_file:
                data = json.load(read_file)
                assert data["template_name"] == "test"
                assert data["success"] == True
                assert data["data"]["title"] == "Test Title"
            
            # Cleanup
            Path(f.name).unlink()
    
    def test_export_csv(self, sample_template):
        """Test CSV export functionality."""
        runner = ScraplingRunner(sample_template)
        
        result = ScrapingResult(
            template_name="test",
            url="https://example.com",
            success=True,
            data={"title": "Test Title", "price": "$19.99"}
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            runner._export_csv(result, f.name)
            
            # Verify file was created
            assert Path(f.name).exists()
            
            # Check contents
            with open(f.name, 'r') as read_file:
                content = read_file.read()
                assert "title" in content
                assert "Test Title" in content
                assert "price" in content
                assert "$19.99" in content
            
            # Cleanup
            Path(f.name).unlink()


class TestBatchScraplingRunner:
    """Test cases for BatchScraplingRunner."""
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample template for testing."""
        return ScrapingTemplate(
            name="batch_test_template",
            url="https://example.com",
            elements=[
                ElementSelector(
                    label="title",
                    selector="h1",
                    element_type="text"
                )
            ]
        )
    
    def test_batch_runner_initialization(self, sample_template):
        """Test BatchScraplingRunner initialization."""
        batch_runner = BatchScraplingRunner(sample_template)
        
        assert batch_runner.template == sample_template
    
    @patch('src.core.scrapling_runner.ScraplingRunner')
    def test_execute_batch(self, mock_runner_class, sample_template):
        """Test batch execution."""
        # Mock the individual runner
        mock_runner = Mock()
        mock_result = ScrapingResult(
            template_name="test",
            url="https://example1.com",
            success=True,
            data={"title": "Test Title"}
        )
        mock_runner.execute_scraping.return_value = mock_result
        mock_runner_class.return_value = mock_runner
        
        batch_runner = BatchScraplingRunner(sample_template)
        urls = ["https://example1.com", "https://example2.com"]
        
        results = batch_runner.execute_batch(urls)
        
        assert len(results) == 2
        assert all(isinstance(result, ScrapingResult) for result in results)
        
        # Verify runner was called for each URL
        assert mock_runner_class.call_count == 2
        assert mock_runner.execute_scraping.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])