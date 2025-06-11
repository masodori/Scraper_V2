#!/usr/bin/env python3
"""
Entry point for running the Interactive Web Scraper as a module.

This allows the scraper to be run with:
python -m src.core
"""

from .cli import main

if __name__ == "__main__":
    main()