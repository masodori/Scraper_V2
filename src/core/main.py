#!/usr/bin/env python3
"""
Interactive Web Scraper - Main Entry Point

This module provides the CLI interface for the interactive web scraping tool.
It handles both interactive template creation and automated scraping execution.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio

from playwright.sync_api import sync_playwright, Page, Browser
from colorama import init, Fore, Style

# Import our custom modules
from ..models.scraping_template import ScrapingTemplate, CookieData, ElementSelector, NavigationAction
from .scrapling_runner import ScraplingRunner

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class InteractiveSession:
    """Manages the interactive Playwright browser session for element tagging."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.template_data: Dict[str, Any] = {}
        
    def start_interactive_session(self, url: str, output_file: str, headless: bool = False) -> str:
        """
        Launches a Playwright browser to start an interactive scraping session.
        
        Args:
            url: Target URL to scrape
            output_file: Name of the output template file
            headless: Whether to run browser in headless mode
            
        Returns:
            Path to the saved template file
        """
        print(f"{Fore.CYAN}🚀 Starting interactive session for: {url}")
        print(f"{Fore.YELLOW}📝 Output template: {output_file}")
        
        template_path = os.path.join('templates', output_file)
        
        try:
            with sync_playwright() as p:
                # Get screen resolution automatically first
                import subprocess
                try:
                    # Get screen resolution on macOS
                    result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                          capture_output=True, text=True, timeout=5)
                    lines = result.stdout.split('\n')
                    width, height = 1280, 800  # fallback
                    
                    for line in lines:
                        if 'Resolution:' in line:
                            # Extract resolution like "1920 x 1080"
                            resolution = line.split('Resolution:')[1].strip()
                            if 'x' in resolution:
                                parts = resolution.split('x')
                                if len(parts) >= 2:
                                    width = int(parts[0].strip())
                                    height = int(parts[1].strip())
                                    break
                except:
                    # Fallback for other systems or if command fails
                    width, height = 1280, 800
                
                # Reduce size slightly to account for browser chrome and dock
                viewport_width = min(width - 200, 1400)
                viewport_height = min(height - 200, 900)
                
                print(f"{Fore.BLUE}🖥️  Setting browser size: {viewport_width}x{viewport_height} (screen: {width}x{height})")
                
                # Launch browser with stealth settings and proper window size
                browser_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
                
                # Add window size arguments if not headless
                if not headless:
                    browser_args.extend([
                        f'--window-size={viewport_width},{viewport_height}',
                        '--window-position=100,50'
                    ])
                
                self.browser = p.chromium.launch(
                    headless=headless,
                    args=browser_args
                )
                
                # Create new page with stealth settings and proper sizing
                context = self.browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    viewport={'width': viewport_width, 'height': viewport_height}
                )
                
                self.page = context.new_page()
                
                # Remove webdriver property
                self.page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                return self._run_interactive_session(url, template_path)
                    
        except Exception as e:
            logger.error(f"Error in interactive session: {e}")
            print(f"{Fore.RED}❌ Error: {e}")
            return ""
        
        finally:
            try:
                if self.browser and not self.browser.is_connected():
                    self.browser.close()
            except Exception:
                pass
    
    def _run_interactive_session(self, url: str, template_path: str) -> str:
        """Handle the interactive session logic."""
        current_url = url
        session_active = True
        
        while session_active:
            try:
                # Navigate to current URL
                print(f"{Fore.BLUE}🌐 Navigating to: {current_url}")
                self.page.goto(current_url, wait_until='networkidle', timeout=30000)
                
                # Auto-handle common cookie consent pop-ups
                self._handle_cookie_consent()
                
                # Initialize template data for this page
                if not hasattr(self, 'template_data') or not self.template_data:
                    self.template_data = {
                        'url': url,  # Keep original URL as base
                        'name': Path(template_path).stem,
                        'description': f'Interactive template for {url}',
                        'cookies': self._extract_cookies(),
                        'elements': [],
                        'actions': []
                    }
                
                # Load and inject the interactive JavaScript (refactored modular version)
                js_path = Path(__file__).parent.parent / 'interactive' / 'index.js'
                with open(js_path, 'r', encoding='utf-8') as f:
                    js_code = f.read()
                
                # Check if functions are already exposed and expose them if needed
                functions_to_expose = [
                    ("save_template_py", self._save_template_callback),
                    ("add_element_py", self._add_element_callback),
                    ("add_action_py", self._add_action_callback),
                    ("log_message_py", self._log_message_callback),
                    ("navigate_to_py", self._navigate_to_callback)
                ]
                
                for func_name, callback in functions_to_expose:
                    try:
                        # Check if function already exists
                        existing = self.page.evaluate(f"typeof window.{func_name}")
                        if existing == "undefined":
                            self.page.expose_function(func_name, callback)
                            print(f"{Fore.BLUE}🔗 Exposed function: {func_name}")
                        else:
                            print(f"{Fore.YELLOW}⚠️ Function {func_name} already exists")
                    except Exception as e:
                        logger.warning(f"Error exposing {func_name}: {e}")
                
                # Inject the interactive overlay
                self.page.evaluate(js_code)
                
                print(f"{Fore.GREEN}✅ Interactive session started!")
                print(f"{Fore.YELLOW}📋 Instructions:")
                print(f"{Fore.WHITE}  • Use 'Elements' tab to select data to scrape")
                print(f"{Fore.WHITE}  • Use 'Actions' tab to select navigation elements")
                print(f"{Fore.WHITE}  • In Action mode, click to navigate to links")
                print(f"{Fore.WHITE}  • Click 'Save Template' when finished")
                print(f"{Fore.WHITE}  • Close the browser or press Ctrl+C to exit")
                
                # Wait for user interaction or navigation
                try:
                    # Wait for either page navigation or browser close
                    while True:
                        try:
                            # Check if page is still available first
                            if self.page.is_closed():
                                session_active = False
                                break
                            
                            # Check if page navigated to a new URL
                            page_url = self.page.url
                            if page_url != current_url:
                                print(f"{Fore.BLUE}🔄 Navigated to: {page_url}")
                                current_url = page_url
                                break
                                
                            # Small wait to prevent busy loop
                            self.page.wait_for_timeout(500)
                            
                        except Exception as e:
                            error_msg = str(e).lower()
                            if any(keyword in error_msg for keyword in [
                                "target page", "context", "browser has been closed",
                                "session closed", "connection closed"
                            ]):
                                session_active = False
                                break
                            else:
                                logger.warning(f"Navigation check error: {e}")
                                # Continue loop despite error
                                self.page.wait_for_timeout(1000)
                            
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in [
                        "target page", "context", "browser has been closed",
                        "session closed", "connection closed"
                    ]):
                        session_active = False
                    else:
                        logger.error(f"Session error: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"Error in session loop: {e}")
                break
        
        # Save template if data was collected
        if self.template_data and (self.template_data.get('elements') or self.template_data.get('actions')):
            self._save_template(template_path)
            print(f"{Fore.GREEN}✅ Template saved to: {template_path}")
            return template_path
        else:
            print(f"{Fore.YELLOW}⚠️ No elements were tagged. Template not saved.")
            return ""
    
    def _handle_cookie_consent(self) -> None:
        """Automatically handle common cookie consent pop-ups."""
        try:
            # Common cookie consent selectors
            consent_selectors = [
                'button:has-text("Accept")',
                'button:has-text("Accept All")',
                'button:has-text("I Accept")',
                'button:has-text("OK")',
                'button:has-text("Continue")',
                '[id*="accept"][type="button"]',
                '[class*="accept"][type="button"]',
                '[data-testid*="accept"]',
                '.cookie-accept',
                '#cookie-accept',
                '.gdpr-accept',
                '#gdpr-accept'
            ]
            
            for selector in consent_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element and element.is_visible():
                        print(f"{Fore.BLUE}🍪 Found cookie consent button, clicking...")
                        element.click()
                        self.page.wait_for_timeout(1000)  # Wait 1 second
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Cookie consent handling error: {e}")
    
    def _extract_cookies(self) -> list:
        """Extract cookies from the current page."""
        try:
            cookies = self.page.context.cookies()
            return [
                {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie.get('domain'),
                    'path': cookie.get('path', '/'),
                    'secure': cookie.get('secure', False),
                    'httpOnly': cookie.get('httpOnly', False),
                    'sameSite': cookie.get('sameSite')
                }
                for cookie in cookies
            ]
        except Exception as e:
            logger.error(f"Error extracting cookies: {e}")
            return []
    
    def _save_template_callback(self, template_json: str) -> None:
        """Callback function called from JavaScript to save the template."""
        try:
            data = json.loads(template_json)
            self.template_data.update(data)
            print(f"{Fore.GREEN}✅ Template data received from browser")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing template JSON: {e}")
            print(f"{Fore.RED}❌ Error parsing template data")
    
    def _add_element_callback(self, element_data: str) -> None:
        """Callback to add a new element to the template."""
        try:
            element = json.loads(element_data)
            self.template_data['elements'].append(element)
            print(f"{Fore.GREEN}✅ Added element: {element.get('label', 'unknown')}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing element data: {e}")
    
    def _add_action_callback(self, action_data: str) -> None:
        """Callback to add a new action to the template."""
        try:
            action = json.loads(action_data)
            self.template_data['actions'].append(action)
            print(f"{Fore.GREEN}✅ Added action: {action.get('label', 'unknown')}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing action data: {e}")
    
    def _log_message_callback(self, message: str) -> None:
        """Callback to log messages from JavaScript."""
        print(f"{Fore.CYAN}🔍 Browser: {message}")
    
    def _navigate_to_callback(self, url: str) -> None:
        """Callback to handle navigation requests from JavaScript."""
        try:
            print(f"{Fore.BLUE}🔄 Navigation requested to: {url}")
            # The navigation will be detected by the main loop
        except Exception as e:
            logger.error(f"Error in navigation callback: {e}")
    
    def _save_template(self, filepath: str) -> None:
        """Save the template to a JSON file."""
        try:
            # Ensure templates directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Create and validate the template
            template = ScrapingTemplate(**self.template_data)
            
            # Save using simple JSON write to avoid Pydantic version issues
            import json
            from datetime import datetime
            
            def json_serializer(obj):
                """JSON serializer for objects not serializable by default json code"""
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template.model_dump(), f, indent=2, ensure_ascii=False, default=json_serializer)
            
            print(f"{Fore.GREEN}✅ Template validated and saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            print(f"{Fore.RED}❌ Error saving template: {e}")


def start_interactive_session(url: str, output_file: str, headless: bool = False) -> str:
    """Start an interactive scraping session."""
    session = InteractiveSession()
    return session.start_interactive_session(url, output_file, headless)


def run_scraper(template_file: str, output_file: Optional[str] = None, format: str = "json") -> str:
    """
    Run the automated scraper with a given template.
    
    Args:
        template_file: Path to the template file
        output_file: Output file path (optional)
        format: Output format (json, csv, excel)
        
    Returns:
        Path to the output file
    """
    print(f"{Fore.CYAN}🤖 Running automated scraper with template: {template_file}")
    
    try:
        # Validate template file exists
        if not os.path.exists(template_file):
            raise FileNotFoundError(f"Template file not found: {template_file}")
        
        # Load and validate template
        template = ScrapingTemplate.load_from_file(template_file)
        print(f"{Fore.GREEN}✅ Template loaded: {template.name}")
        print(f"{Fore.BLUE}🎯 Target URL: {template.url}")
        print(f"{Fore.BLUE}📊 Elements to scrape: {len(template.elements)}")
        
        # Initialize the Scrapling runner
        runner = ScraplingRunner(template)
        
        # Execute scraping
        result = runner.execute_scraping()
        
        if result.success:
            # Generate output filename if not provided
            if not output_file:
                base_name = template.name.replace(' ', '_').lower()
                timestamp = result.scraped_at.strftime("%Y%m%d_%H%M%S")
                
                if format == "csv":
                    output_file = f"output/{base_name}_{timestamp}.csv"
                elif format == "excel":
                    output_file = f"output/{base_name}_{timestamp}.xlsx"
                else:
                    output_file = f"output/{base_name}_{timestamp}.json"
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Export data in requested format
            runner.export_data(result, output_file, format)
            
            print(f"{Fore.GREEN}✅ Scraping completed successfully!")
            print(f"{Fore.GREEN}📁 Output file: {output_file}")
            print(f"{Fore.GREEN}📊 Records scraped: {len(result.data) if isinstance(result.data, list) else 1}")
            
            return output_file
            
        else:
            print(f"{Fore.RED}❌ Scraping failed!")
            for error in result.errors:
                print(f"{Fore.RED}   • {error}")
            return ""
            
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        print(f"{Fore.RED}❌ Error: {e}")
        return ""


def list_templates() -> None:
    """List all available templates."""
    templates_dir = "templates"
    
    if not os.path.exists(templates_dir):
        print(f"{Fore.YELLOW}⚠️ No templates directory found")
        return
    
    template_files = [f for f in os.listdir(templates_dir) if f.endswith('.json')]
    
    if not template_files:
        print(f"{Fore.YELLOW}⚠️ No templates found in {templates_dir}")
        return
    
    print(f"{Fore.CYAN}📋 Available Templates:")
    print(f"{Fore.CYAN}{'='*50}")
    
    for template_file in sorted(template_files):
        try:
            template_path = os.path.join(templates_dir, template_file)
            template = ScrapingTemplate.load_from_file(template_path)
            
            print(f"{Fore.WHITE}📄 {template_file}")
            print(f"{Fore.BLUE}   Name: {template.name}")
            print(f"{Fore.BLUE}   URL: {template.url}")
            print(f"{Fore.BLUE}   Elements: {len(template.elements)}")
            print(f"{Fore.BLUE}   Created: {template.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading {template_file}: {e}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Interactive Web Scraper - Create templates and automate scraping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start interactive session
  python -m src.core.main interactive https://example.com --output my_template.json
  
  # Run automated scraping
  python -m src.core.main scrape templates/my_template.json --format csv
  
  # List available templates
  python -m src.core.main list
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")
    
    # Interactive session command
    interactive_parser = subparsers.add_parser(
        "interactive", 
        help="Start an interactive scraping session"
    )
    interactive_parser.add_argument(
        "url", 
        type=str, 
        help="The URL to start the session with"
    )
    interactive_parser.add_argument(
        "--output", 
        type=str, 
        default="template.json",
        help="The name of the output template file (default: template.json)"
    )
    interactive_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    
    # Automated scraping command
    scraper_parser = subparsers.add_parser(
        "scrape", 
        help="Run automated scraper with a template"
    )
    scraper_parser.add_argument(
        "template", 
        type=str, 
        help="Path to the scraping template file"
    )
    scraper_parser.add_argument(
        "--output",
        type=str,
        help="Output file path (auto-generated if not specified)"
    )
    scraper_parser.add_argument(
        "--format",
        choices=["json", "csv", "excel"],
        default="json",
        help="Output format (default: json)"
    )
    
    # List templates command
    list_parser = subparsers.add_parser(
        "list",
        help="List all available templates"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}🕷️  Interactive Web Scraper v2.0")
    print(f"{Fore.MAGENTA}   Playwright + Scrapling Integration")
    print(f"{Fore.MAGENTA}{'='*60}")
    print()
    
    try:
        if args.command == "interactive":
            result = start_interactive_session(args.url, args.output, args.headless)
            if result:
                print(f"\n{Fore.GREEN}🎉 Interactive session completed successfully!")
                print(f"{Fore.BLUE}📄 Template saved: {result}")
                print(f"{Fore.YELLOW}💡 Next step: Run 'python -m src.core.main scrape {result}' to test your template")
            else:
                sys.exit(1)
                
        elif args.command == "scrape":
            result = run_scraper(args.template, args.output, args.format)
            if result:
                print(f"\n{Fore.GREEN}🎉 Scraping completed successfully!")
                print(f"{Fore.BLUE}📁 Output: {result}")
            else:
                sys.exit(1)
                
        elif args.command == "list":
            list_templates()
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n{Fore.RED}❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()