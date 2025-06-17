#!/usr/bin/env python3
"""
Progress tracking utilities for scraping operations.
"""

import time
import sys


class ProgressTracker:
    """
    Terminal progress bar for scraping operations.
    """
    
    def __init__(self, total: int, description: str = "Progress"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        
    def update(self, increment: int = 1, description: str = None):
        """Update progress bar."""
        self.current += increment
        if description:
            self.description = description
        self._display_progress()
    
    def _display_progress(self):
        """Display the progress bar."""
        if self.total == 0:
            return
            
        percent = (self.current / self.total) * 100
        bar_length = 40
        filled_length = int(bar_length * self.current // self.total)
        
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        elapsed = time.time() - self.start_time
        
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f" ETA: {int(eta)}s" if eta > 1 else ""
        else:
            eta_str = ""
        
        # Clear line and print progress
        sys.stdout.write(f'\r{self.description}: |{bar}| {self.current}/{self.total} ({percent:.1f}%){eta_str}')
        sys.stdout.flush()
        
        if self.current >= self.total:
            print()  # New line when complete
    
    def finish(self, description: str = "Complete"):
        """Mark progress as finished."""
        self.current = self.total
        self.description = description
        self._display_progress()