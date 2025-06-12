#!/usr/bin/env python3
"""
Interactive Web Scraper - Command Line Interface

This module provides a command-line interface for:
- Interactive template creation
- Automated scraping execution
- Template management
"""

import argparse
from asyncio import subprocess
import shutil
import sys
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List

from colorama import Fore

from ..models.scraping_template import ScrapingTemplate
from .main import start_interactive_session, run_scraper, list_templates

logger = logging.getLogger(__name__)


class ScraperCLI:
    """Enhanced CLI with setup and configuration capabilities."""
    
    def __init__(self):
        self.config_file = Path.home() / '.scraper_config.json'
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from user's home directory."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading config: {e}")
        
        # Default configuration
        return {
            'default_output_dir': 'output',
            'default_template_dir': 'templates',
            'default_format': 'json',
            'browser_timeout': 30,
            'stealth_mode': True,
            'headless_default': False,
            'log_level': 'INFO'
        }
    
    def _save_config(self) -> None:
        """Save configuration to user's home directory."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"{Fore.GREEN}✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"{Fore.RED}❌ Error saving config: {e}")
    
    def setup_project(self, force: bool = False) -> None:
        """Set up the project environment and install dependencies."""
        print(f"{Fore.CYAN}🚀 Setting up Interactive Web Scraper...")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print(f"{Fore.RED}❌ Python 3.8+ required. Current version: {sys.version}")
            sys.exit(1)
        
        print(f"{Fore.GREEN}✅ Python version: {sys.version.split()[0]}")
        
        # Create necessary directories
        directories = ['templates', 'output', 'logs']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            print(f"{Fore.GREEN}✅ Created directory: {directory}")
        
        # Install Python dependencies
        self._install_dependencies(force)
        
        # Install Playwright browsers
        self._install_playwright_browsers()
        
        # Create default configuration
        self._create_default_config()
        
        print(f"\n{Fore.GREEN}🎉 Setup completed successfully!")
        print(f"{Fore.YELLOW}💡 Next steps:")
        print(f"{Fore.WHITE}  • Run: python -m src.core.cli interactive https://example.com")
        print(f"{Fore.WHITE}  • Check: python -m src.core.cli status")
    
    def _install_dependencies(self, force: bool = False) -> None:
        """Install Python dependencies from requirements.txt."""
        print(f"\n{Fore.BLUE}📦 Installing Python dependencies...")
        
        requirements_file = Path('requirements.txt')
        if not requirements_file.exists():
            print(f"{Fore.RED}❌ requirements.txt not found")
            return
        
        try:
            cmd = [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt']
            if force:
                cmd.append('--force-reinstall')
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"{Fore.GREEN}✅ Dependencies installed successfully")
            else:
                print(f"{Fore.RED}❌ Error installing dependencies:")
                print(f"{Fore.RED}{result.stderr}")
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error installing dependencies: {e}")
    
    def _install_playwright_browsers(self) -> None:
        """Install Playwright browser binaries."""
        print(f"\n{Fore.BLUE}🌐 Installing Playwright browsers...")
        
        try:
            # Check if playwright is installed
            result = subprocess.run([sys.executable, '-c', 'import playwright'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"{Fore.YELLOW}⚠️ Playwright not installed, skipping browser installation")
                return
            
            # Install chromium browser
            cmd = [sys.executable, '-m', 'playwright', 'install', 'chromium']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"{Fore.GREEN}✅ Playwright browsers installed successfully")
            else:
                print(f"{Fore.RED}❌ Error installing Playwright browsers:")
                print(f"{Fore.RED}{result.stderr}")
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error installing Playwright browsers: {e}")
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        print(f"\n{Fore.BLUE}⚙️ Creating default configuration...")
        
        if self.config_file.exists() and not self._confirm("Configuration file exists. Overwrite?"):
            print(f"{Fore.YELLOW}⚠️ Keeping existing configuration")
            return
        
        self._save_config()
    
    def check_status(self) -> None:
        """Check the status of the scraper environment."""
        print(f"{Fore.CYAN}🔍 Interactive Web Scraper Status")
        print(f"{Fore.CYAN}{'='*50}")
        
        # Python version
        print(f"\n{Fore.BLUE}🐍 Python Environment:")
        print(f"{Fore.WHITE}  Version: {sys.version.split()[0]}")
        print(f"{Fore.WHITE}  Executable: {sys.executable}")
        
        # Check dependencies
        print(f"\n{Fore.BLUE}📦 Dependencies:")
        self._check_dependency('playwright', 'Playwright')
        self._check_dependency('scrapling', 'Scrapling')
        self._check_dependency('pandas', 'Pandas')
        self._check_dependency('pydantic', 'Pydantic')
        self._check_dependency('colorama', 'Colorama')
        
        # Check Playwright browsers
        print(f"\n{Fore.BLUE}🌐 Playwright Browsers:")
        self._check_playwright_browsers()
        
        # Check directories
        print(f"\n{Fore.BLUE}📁 Directories:")
        for directory in ['templates', 'output', 'logs']:
            if Path(directory).exists():
                count = len(list(Path(directory).glob('*')))
                print(f"{Fore.GREEN}  ✅ {directory}/ ({count} files)")
            else:
                print(f"{Fore.RED}  ❌ {directory}/ (missing)")
        
        # Configuration
        print(f"\n{Fore.BLUE}⚙️ Configuration:")
        if self.config_file.exists():
            print(f"{Fore.GREEN}  ✅ Config file: {self.config_file}")
            for key, value in self.config.items():
                print(f"{Fore.WHITE}    {key}: {value}")
        else:
            print(f"{Fore.YELLOW}  ⚠️ No configuration file found")
    
    def _check_dependency(self, module_name: str, display_name: str) -> None:
        """Check if a Python dependency is installed."""
        try:
            __import__(module_name)
            # Try to get version if possible
            try:
                mod = __import__(module_name)
                version = getattr(mod, '__version__', 'unknown')
                print(f"{Fore.GREEN}  ✅ {display_name} ({version})")
            except:
                print(f"{Fore.GREEN}  ✅ {display_name}")
        except ImportError:
            print(f"{Fore.RED}  ❌ {display_name} (not installed)")
    
    def _check_playwright_browsers(self) -> None:
        """Check if Playwright browsers are installed."""
        try:
            result = subprocess.run([sys.executable, '-m', 'playwright', '--version'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"{Fore.GREEN}  ✅ Playwright CLI ({version})")
                
                # Check for chromium
                result = subprocess.run([sys.executable, '-c', 
                    'from playwright.sync_api import sync_playwright; '
                    'p = sync_playwright().__enter__(); '
                    'print("chromium" if p.chromium.executable_path else "missing")'],
                    capture_output=True, text=True)
                
                if 'chromium' in result.stdout:
                    print(f"{Fore.GREEN}  ✅ Chromium browser")
                else:
                    print(f"{Fore.RED}  ❌ Chromium browser (run: playwright install chromium)")
            else:
                print(f"{Fore.RED}  ❌ Playwright CLI (not installed)")
                
        except Exception as e:
            print(f"{Fore.RED}  ❌ Playwright check failed: {e}")
    
    def configure(self, key: Optional[str] = None, value: Optional[str] = None) -> None:
        """Configure scraper settings."""
        if key is None:
            # Show current configuration
            print(f"{Fore.CYAN}⚙️ Current Configuration:")
            print(f"{Fore.CYAN}{'='*40}")
            
            for k, v in self.config.items():
                print(f"{Fore.WHITE}  {k}: {Fore.YELLOW}{v}")
            
            print(f"\n{Fore.BLUE}💡 To modify: python -m src.core.cli config <key> <value>")
            return
        
        if value is None:
            # Show specific key
            if key in self.config:
                print(f"{Fore.WHITE}{key}: {Fore.YELLOW}{self.config[key]}")
            else:
                print(f"{Fore.RED}❌ Configuration key '{key}' not found")
            return
        
        # Set configuration value
        old_value = self.config.get(key, 'not set')
        
        # Type conversion for known keys
        if key in ['browser_timeout']:
            try:
                value = float(value)
            except ValueError:
                print(f"{Fore.RED}❌ Invalid number: {value}")
                return
        elif key in ['stealth_mode', 'headless_default']:
            value = value.lower() in ('true', '1', 'yes', 'on')
        
        self.config[key] = value
        self._save_config()
        
        print(f"{Fore.GREEN}✅ Updated {key}: {old_value} → {value}")
    
    def clean(self, what: str = 'all') -> None:
        """Clean up generated files and caches."""
        print(f"{Fore.CYAN}🧹 Cleaning up...")
        
        if what in ['all', 'output']:
            self._clean_directory('output', '*.json *.csv *.xlsx')
        
        if what in ['all', 'logs']:
            self._clean_directory('logs', '*.log')
        
        if what in ['all', 'cache']:
            self._clean_cache()
        
        print(f"{Fore.GREEN}✅ Cleanup completed")
    
    def _clean_directory(self, directory: str, pattern: str) -> None:
        """Clean files in a directory matching a pattern."""
        dir_path = Path(directory)
        if not dir_path.exists():
            return
        
        count = 0
        for pattern_part in pattern.split():
            for file_path in dir_path.glob(pattern_part):
                if file_path.is_file():
                    file_path.unlink()
                    count += 1
        
        if count > 0:
            print(f"{Fore.GREEN}  ✅ Cleaned {count} files from {directory}/")
        else:
            print(f"{Fore.YELLOW}  ℹ️ No files to clean in {directory}/")
    
    def _clean_cache(self) -> None:
        """Clean Python cache files."""
        count = 0
        for cache_dir in Path('.').rglob('__pycache__'):
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir)
                count += 1
        
        if count > 0:
            print(f"{Fore.GREEN}  ✅ Cleaned {count} cache directories")
        else:
            print(f"{Fore.YELLOW}  ℹ️ No cache directories found")
    
    def update_dependencies(self) -> None:
        """Update all dependencies to latest versions."""
        print(f"{Fore.CYAN}📦 Updating dependencies...")
        
        try:
            # Update pip first
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         check=True)
            print(f"{Fore.GREEN}✅ Updated pip")
            
            # Update all packages
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', '-r', 'requirements.txt'], 
                         check=True)
            print(f"{Fore.GREEN}✅ Updated all dependencies")
            
            # Update Playwright browsers
            subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], 
                         check=True)
            print(f"{Fore.GREEN}✅ Updated Playwright browsers")
            
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}❌ Update failed: {e}")
        except Exception as e:
            print(f"{Fore.RED}❌ Error during update: {e}")
    
    def create_example_template(self) -> None:
        """Create an example template for demonstration."""
        print(f"{Fore.CYAN}📝 Creating example template...")
        
        example_template = ScrapingTemplate(
            name="example_news_scraper",
            description="Example template for scraping news headlines",
            url="https://news.ycombinator.com",
            elements=[
                {
                    "label": "headlines",
                    "selector": ".storylink",
                    "selector_type": "css",
                    "element_type": "text",
                    "is_multiple": True,
                    "is_required": True
                },
                {
                    "label": "links",
                    "selector": ".storylink",
                    "selector_type": "css",
                    "element_type": "link",
                    "is_multiple": True,
                    "is_required": True
                }
            ],
            actions=[
                {
                    "label": "next_page",
                    "selector": ".morelink",
                    "action_type": "click",
                    "wait_after": 2.0
                }
            ]
        )
        
        output_path = Path('templates') / 'example_template.json'
        example_template.save_to_file(str(output_path))
        
        print(f"{Fore.GREEN}✅ Example template created: {output_path}")
        print(f"{Fore.YELLOW}💡 Test it with: python -m src.core.cli scrape {output_path}")
    
    def validate_template(self, template_path: str) -> None:
        """Validate a template file."""
        print(f"{Fore.CYAN}🔍 Validating template: {template_path}")
        
        try:
            template = ScrapingTemplate.load_from_file(template_path)
            
            print(f"{Fore.GREEN}✅ Template is valid!")
            print(f"{Fore.BLUE}  Name: {template.name}")
            print(f"{Fore.BLUE}  URL: {template.url}")
            print(f"{Fore.BLUE}  Elements: {len(template.elements)}")
            print(f"{Fore.BLUE}  Actions: {len(template.actions)}")
            
            # Additional validation checks
            warnings = []
            
            if not template.elements:
                warnings.append("No elements defined - template won't extract any data")
            
            for element in template.elements:
                if not element.selector.strip():
                    warnings.append(f"Empty selector for element '{element.label}'")
            
            if warnings:
                print(f"\n{Fore.YELLOW}⚠️ Warnings:")
                for warning in warnings:
                    print(f"{Fore.YELLOW}  • {warning}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Template validation failed: {e}")
    
    def _confirm(self, message: str) -> bool:
        """Ask for user confirmation."""
        response = input(f"{Fore.YELLOW}❓ {message} (y/N): ").strip().lower()
        return response in ('y', 'yes')


def create_cli() -> argparse.ArgumentParser:
    """Create the enhanced CLI parser."""
    parser = argparse.ArgumentParser(
        description="Interactive Web Scraper - Complete CLI with setup and configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup and installation
  python -m src.core.cli setup                    # Initial project setup
  python -m src.core.cli status                   # Check environment status
  python -m src.core.cli config                   # Show configuration
  
  # Interactive template creation
  python -m src.core.cli interactive https://example.com
  python -m src.core.cli interactive https://example.com --output my_template.json
  
  # Automated scraping
  python -m src.core.cli scrape templates/my_template.json
  python -m src.core.cli scrape templates/my_template.json --format csv
  
  # Template management
  python -m src.core.cli list                     # List all templates
  python -m src.core.cli validate templates/my_template.json
  python -m src.core.cli example                  # Create example template
  
  # Maintenance
  python -m src.core.cli clean                    # Clean output files
  python -m src.core.cli update                   # Update dependencies
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up the project environment")
    setup_parser.add_argument("--force", action="store_true", help="Force reinstall dependencies")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check environment status")
    
    # Configuration commands
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("key", nargs="?", help="Configuration key")
    config_parser.add_argument("value", nargs="?", help="Configuration value")
    
    # Interactive session
    interactive_parser = subparsers.add_parser("interactive", help="Start interactive scraping session")
    interactive_parser.add_argument("url", type=str, help="URL to start the session with")
    interactive_parser.add_argument("--output", type=str, default="template.json", help="Output template filename")
    interactive_parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    
    # Automated scraping
    scraper_parser = subparsers.add_parser("scrape", help="Run automated scraper with template")
    scraper_parser.add_argument("template", type=str, help="Path to the scraping template file")
    scraper_parser.add_argument("--output", type=str, help="Output file path")
    scraper_parser.add_argument("--format", choices=["json", "csv", "excel"], default="json", help="Output format")
    
    # Template management
    list_parser = subparsers.add_parser("list", help="List all available templates")
    
    validate_parser = subparsers.add_parser("validate", help="Validate a template file")
    validate_parser.add_argument("template", type=str, help="Path to template file")
    
    example_parser = subparsers.add_parser("example", help="Create an example template")
    
    # Maintenance commands
    clean_parser = subparsers.add_parser("clean", help="Clean up generated files")
    clean_parser.add_argument("what", nargs="?", default="all", 
                             choices=["all", "output", "logs", "cache"], 
                             help="What to clean")
    
    update_parser = subparsers.add_parser("update", help="Update dependencies")
    
    return parser


def main():
    """Main CLI entry point."""
    # If no arguments provided, start interactive mode
    if len(sys.argv) == 1:
        from .interactive_cli import run_interactive_cli
        run_interactive_cli()
        return
    
    parser = create_cli()
    args = parser.parse_args()
    
    # Print banner
    print(f"{Fore.MAGENTA}{'='*70}")
    print(f"{Fore.MAGENTA}🕷️  Interactive Web Scraper v2.0 - Enhanced CLI")
    print(f"{Fore.MAGENTA}   Playwright + Scrapling Integration with Setup Tools")
    print(f"{Fore.MAGENTA}{'='*70}")
    print()
    
    cli = ScraperCLI()
    
    try:
        if args.command == "setup":
            cli.setup_project(force=args.force)
            
        elif args.command == "status":
            cli.check_status()
            
        elif args.command == "config":
            cli.configure(args.key, args.value)
            
        elif args.command == "interactive":
            result = start_interactive_session(args.url, args.output, args.headless)
            if result:
                print(f"\n{Fore.GREEN}🎉 Interactive session completed!")
                print(f"{Fore.BLUE}📄 Template saved: {result}")
                print(f"{Fore.YELLOW}💡 Next: python -m src.core.cli scrape {result}")
            else:
                sys.exit(1)
                
        elif args.command == "scrape":
            result = run_scraper(args.template, args.output, args.format)
            if result:
                print(f"\n{Fore.GREEN}🎉 Scraping completed!")
                print(f"{Fore.BLUE}📁 Output: {result}")
            else:
                sys.exit(1)
                
        elif args.command == "list":
            list_templates()
            
        elif args.command == "validate":
            cli.validate_template(args.template)
            
        elif args.command == "example":
            cli.create_example_template()
            
        elif args.command == "clean":
            cli.clean(args.what)
            
        elif args.command == "update":
            cli.update_dependencies()
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n{Fore.RED}❌ Unexpected error: {e}")
        print(f"{Fore.YELLOW}💡 Run 'python -m src.core.cli status' to check your environment")
        sys.exit(1)


if __name__ == "__main__":
    main()