#!/usr/bin/env python3
"""
Comprehensive unit tests for ProgressTracker module.

Tests for progress tracking, ETA calculations, and terminal display.
"""

import pytest
import time
from unittest.mock import patch, Mock
from io import StringIO

from src.core.utils.progress import ProgressTracker


class TestProgressTracker:
    """Test cases for ProgressTracker functionality."""

    def test_initialization(self):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker(100, "Test Progress")
        
        assert tracker.total == 100
        assert tracker.current == 0
        assert tracker.description == "Test Progress"
        assert isinstance(tracker.start_time, float)

    def test_initialization_with_defaults(self):
        """Test ProgressTracker initialization with default description."""
        tracker = ProgressTracker(50)
        
        assert tracker.total == 50
        assert tracker.current == 0
        assert tracker.description == "Progress"

    @patch('sys.stdout')
    def test_update_increment_default(self, mock_stdout):
        """Test update method with default increment."""
        tracker = ProgressTracker(10, "Testing")
        
        tracker.update()
        
        assert tracker.current == 1

    @patch('sys.stdout')
    def test_update_custom_increment(self, mock_stdout):
        """Test update method with custom increment."""
        tracker = ProgressTracker(10, "Testing")
        
        tracker.update(5)
        
        assert tracker.current == 5

    @patch('sys.stdout')
    def test_update_with_description_change(self, mock_stdout):
        """Test update method with description change."""
        tracker = ProgressTracker(10, "Testing")
        
        tracker.update(1, "New Description")
        
        assert tracker.current == 1
        assert tracker.description == "New Description"

    @patch('sys.stdout')
    def test_update_multiple_times(self, mock_stdout):
        """Test multiple update calls."""
        tracker = ProgressTracker(10, "Testing")
        
        tracker.update(2)
        tracker.update(3)
        tracker.update(1)
        
        assert tracker.current == 6

    @patch('sys.stdout')
    def test_display_progress_zero_total(self, mock_stdout):
        """Test progress display with zero total."""
        tracker = ProgressTracker(0, "Testing")
        
        tracker._display_progress()
        
        # Should not write anything for zero total
        assert not mock_stdout.write.called

    @patch('sys.stdout')
    def test_display_progress_basic_output(self, mock_stdout):
        """Test basic progress display output."""
        tracker = ProgressTracker(10, "Testing")
        tracker.current = 5
        
        tracker._display_progress()
        
        # Should write progress bar
        mock_stdout.write.assert_called()
        call_args = mock_stdout.write.call_args[0][0]
        assert "Testing:" in call_args
        assert "5/10" in call_args
        assert "50.0%" in call_args

    @patch('sys.stdout')
    def test_display_progress_bar_visualization(self, mock_stdout):
        """Test progress bar visualization."""
        tracker = ProgressTracker(4, "Testing")
        tracker.current = 2  # 50% complete
        
        tracker._display_progress()
        
        call_args = mock_stdout.write.call_args[0][0]
        # Should contain filled and unfilled bar characters
        assert '█' in call_args  # Filled
        assert '░' in call_args  # Unfilled

    @patch('sys.stdout')
    def test_display_progress_eta_calculation(self, mock_stdout):
        """Test ETA calculation in progress display."""
        tracker = ProgressTracker(10, "Testing")
        tracker.current = 5
        
        # Mock elapsed time
        with patch('time.time') as mock_time:
            mock_time.return_value = tracker.start_time + 10  # 10 seconds elapsed
            
            tracker._display_progress()
            
            call_args = mock_stdout.write.call_args[0][0]
            # ETA should be calculated for remaining work
            assert "ETA:" in call_args

    @patch('sys.stdout')
    def test_display_progress_no_eta_for_zero_current(self, mock_stdout):
        """Test no ETA display when current is zero."""
        tracker = ProgressTracker(10, "Testing")
        tracker.current = 0
        
        tracker._display_progress()
        
        call_args = mock_stdout.write.call_args[0][0]
        # Should not show ETA when no progress made
        assert "ETA:" not in call_args

    @patch('sys.stdout')
    def test_display_progress_newline_when_complete(self, mock_stdout):
        """Test newline is printed when progress is complete."""
        tracker = ProgressTracker(5, "Testing")
        tracker.current = 5  # Complete
        
        with patch('builtins.print') as mock_print:
            tracker._display_progress()
            
            # Should print newline when complete
            mock_print.assert_called_once_with()

    @patch('sys.stdout')
    def test_display_progress_no_newline_when_incomplete(self, mock_stdout):
        """Test no newline when progress is incomplete."""
        tracker = ProgressTracker(10, "Testing")
        tracker.current = 5
        
        with patch('builtins.print') as mock_print:
            tracker._display_progress()
            
            # Should not print newline when incomplete
            mock_print.assert_not_called()

    @patch('sys.stdout')
    def test_finish_method(self, mock_stdout):
        """Test finish method functionality."""
        tracker = ProgressTracker(10, "Testing")
        tracker.current = 7
        
        tracker.finish("Completed Successfully")
        
        assert tracker.current == tracker.total
        assert tracker.description == "Completed Successfully"

    @patch('sys.stdout')
    def test_finish_with_default_description(self, mock_stdout):
        """Test finish method with default description."""
        tracker = ProgressTracker(10, "Testing")
        
        tracker.finish()
        
        assert tracker.current == tracker.total
        assert tracker.description == "Complete"

    @patch('sys.stdout')
    def test_percent_calculation_accuracy(self, mock_stdout):
        """Test percentage calculation accuracy."""
        tracker = ProgressTracker(3, "Testing")
        tracker.current = 1
        
        tracker._display_progress()
        
        call_args = mock_stdout.write.call_args[0][0]
        # 1/3 should be 33.3%
        assert "33.3%" in call_args

    @patch('sys.stdout')
    def test_bar_length_calculation(self, mock_stdout):
        """Test progress bar length calculation."""
        tracker = ProgressTracker(40, "Testing")  # Same as bar_length
        tracker.current = 20  # 50%
        
        tracker._display_progress()
        
        call_args = mock_stdout.write.call_args[0][0]
        # Should have equal filled and unfilled parts
        filled_count = call_args.count('█')
        unfilled_count = call_args.count('░')
        assert filled_count == 20
        assert unfilled_count == 20

    @patch('sys.stdout')
    def test_stdout_flush_called(self, mock_stdout):
        """Test that stdout.flush() is called."""
        tracker = ProgressTracker(10, "Testing")
        tracker.current = 5
        
        tracker._display_progress()
        
        mock_stdout.flush.assert_called_once()

    def test_time_tracking(self):
        """Test that start time is properly tracked."""
        with patch('time.time') as mock_time:
            mock_time.return_value = 1234567890.0
            
            tracker = ProgressTracker(10, "Testing")
            
            assert tracker.start_time == 1234567890.0

    @patch('sys.stdout')
    def test_eta_formatting_seconds(self, mock_stdout):
        """Test ETA formatting for seconds."""
        tracker = ProgressTracker(10, "Testing")
        tracker.current = 5
        
        # Mock 10 seconds elapsed, expect 10 more seconds
        with patch('time.time') as mock_time:
            mock_time.return_value = tracker.start_time + 10
            
            tracker._display_progress()
            
            call_args = mock_stdout.write.call_args[0][0]
            assert "ETA: 10s" in call_args

    @patch('sys.stdout')
    def test_eta_short_time_no_display(self, mock_stdout):
        """Test ETA not displayed for very short remaining times."""
        tracker = ProgressTracker(10, "Testing")
        tracker.current = 9
        
        # Mock very short remaining time
        with patch('time.time') as mock_time:
            mock_time.return_value = tracker.start_time + 0.1
            
            tracker._display_progress()
            
            call_args = mock_stdout.write.call_args[0][0]
            # Should not show ETA for very short times
            assert "ETA:" not in call_args

    @patch('sys.stdout')
    def test_carriage_return_in_output(self, mock_stdout):
        """Test that carriage return is used to overwrite line."""
        tracker = ProgressTracker(10, "Testing")
        tracker.current = 5
        
        tracker._display_progress()
        
        call_args = mock_stdout.write.call_args[0][0]
        # Should start with carriage return to overwrite previous line
        assert call_args.startswith('\r')

    @patch('sys.stdout')
    def test_progress_beyond_total(self, mock_stdout):
        """Test behavior when progress exceeds total."""
        tracker = ProgressTracker(10, "Testing")
        tracker.current = 15  # Beyond total
        
        with patch('builtins.print'):  # Mock print to avoid newline interference
            tracker._display_progress()
        
        call_args = mock_stdout.write.call_args[0][0]
        # Should handle gracefully
        assert "15/10" in call_args

    @patch('sys.stdout')
    def test_real_time_progress_simulation(self, mock_stdout):
        """Test realistic progress update simulation."""
        tracker = ProgressTracker(5, "Processing Items")
        
        with patch('builtins.print'):  # Mock print to avoid newline interference
            # Simulate processing items
            for i in range(5):
                tracker.update(1, f"Processing item {i+1}")
                
        assert tracker.current == 5
        assert tracker.description == "Processing item 5"
        
        # Should have called display for each update
        assert mock_stdout.write.call_count == 5

    @patch('sys.stdout')
    def test_edge_case_single_item_total(self, mock_stdout):
        """Test edge case with total of 1."""
        tracker = ProgressTracker(1, "Single Item")
        
        with patch('builtins.print'):  # Mock print to avoid newline interference
            tracker.update()
        
        call_args = mock_stdout.write.call_args[0][0]
        assert "1/1" in call_args
        assert "100.0%" in call_args

    @patch('sys.stdout')
    def test_zero_increment_update(self, mock_stdout):
        """Test update with zero increment."""
        tracker = ProgressTracker(10, "Testing")
        initial_current = tracker.current
        
        tracker.update(0, "Status Update")
        
        assert tracker.current == initial_current
        assert tracker.description == "Status Update"