#!/usr/bin/env python3
"""
Interactive Web Scraper - Command Line Interface

This module provides a command-line interface for:
- Interactive template creation
- Automated scraping execution
- Template management
"""

import argparse
import sys
import logging
from pathlib import Path

from ..models.scraping_template import ScrapingTemplate
from .main import start_interactive_session, run_scraper, list_templates

logger = logging.getLogger(__name__)


class ScraperCLI:
    """Simple CLI for web scraping operations."""
    
    def __init__(self):
        pass
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for the CLI."""
        parser = argparse.ArgumentParser(
            description='Interactive Web Scraper - Visual template creation + automated scraping',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Create template interactively
  python -m src.core.main interactive https://example.com --output my_template.json
  
  # Run scraping with template
  python -m src.core.main scrape templates/my_template.json --format json
  
  # List all templates
  python -m src.core.main list
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Interactive command
        interactive_parser = subparsers.add_parser(
            'interactive', 
            help='Start interactive session for template creation'
        )
        interactive_parser.add_argument('url', help='URL to scrape')
        interactive_parser.add_argument(
            '--output', '-o', 
            default='template.json',
            help='Output template file (default: template.json)'
        )
        interactive_parser.add_argument(
            '--headless', 
            action='store_true',
            help='Run in headless mode'
        )
        interactive_parser.add_argument(
            '--timeout', 
            type=int, 
            default=30,
            help='Page load timeout in seconds (default: 30)'
        )
        
        # Scrape command
        scrape_parser = subparsers.add_parser(
            'scrape', 
            help='Run automated scraping with template'
        )
        scrape_parser.add_argument('template', help='Template file to use')
        scrape_parser.add_argument(
            '--output', '-o',
            help='Output file (auto-generated if not specified)'
        )
        scrape_parser.add_argument(
            '--format', '-f',
            choices=['json', 'csv', 'excel'],
            default='json',
            help='Output format (default: json)'
        )
        
        # List command
        list_parser = subparsers.add_parser(
            'list',
            help='List available templates'
        )
        list_parser.add_argument(
            '--dir',
            default='templates',
            help='Templates directory (default: templates)'
        )
        
        return parser
    
    def run(self) -> None:
        """Run the CLI with command line arguments."""
        parser = self.create_parser()
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        try:
            if args.command == 'interactive':
                self._run_interactive(args)
            elif args.command == 'scrape':
                self._run_scrape(args)
            elif args.command == 'list':
                self._run_list(args)
        except KeyboardInterrupt:
            print("\n⏹️  Operation cancelled by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    def _run_interactive(self, args) -> None:
        """Run interactive template creation."""
        print(f"🕷️  Starting interactive session for: {args.url}")
        print(f"📝 Output template: {args.output}")
        
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        start_interactive_session(
            url=args.url,
            output_file=args.output,
            headless=args.headless,
            timeout=args.timeout
        )
    
    def _run_scrape(self, args) -> None:
        """Run automated scraping."""
        template_path = Path(args.template)
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {args.template}")
        
        print(f"🤖 Running scraper with template: {args.template}")
        
        # Generate output filename if not provided
        if not args.output:
            timestamp = import_datetime().datetime.now().strftime("%Y%m%d_%H%M%S")
            template_name = template_path.stem
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            args.output = str(output_dir / f"{template_name}_{timestamp}.{args.format}")
        
        print(f"📁 Output file: {args.output}")
        
        # Run scraper
        output_path = run_scraper(
            template_file=args.template,
            output_file=args.output,
            format=args.format
        )
        
        if output_path:
            print(f"✅ Scraping completed successfully!")
            print(f"📁 Output saved to: {output_path}")
        else:
            print(f"❌ Scraping failed - check logs for details")
    
    def _run_list(self, args) -> None:
        """List available templates."""
        templates_dir = Path(args.dir)
        
        if not templates_dir.exists():
            print(f"📁 Templates directory not found: {args.dir}")
            print("💡 Create templates using: python -m src.core.main interactive <url>")
            return
        
        templates = list_templates(args.dir)
        
        if not templates:
            print(f"📁 No templates found in: {args.dir}")
            print("💡 Create templates using: python -m src.core.main interactive <url>")
            return
        
        print(f"📋 Available templates in {args.dir}:")
        for template in templates:
            print(f"  • {template['name']} - {template['url']} ({template['elements']} elements)")


def import_datetime():
    """Import datetime module."""
    import datetime
    return datetime


def main():
    """Main entry point for the CLI."""
    cli = ScraperCLI()
    cli.run()


if __name__ == '__main__':
    main()