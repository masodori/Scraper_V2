#!/usr/bin/env python3
"""
Interactive Menu-Driven CLI for Web Scraper

This module provides an interactive, menu-driven interface that guides users
through all scraping operations with intuitive prompts and selections.
"""

from typing import List
from pathlib import Path

from colorama import init, Fore, Style, Back
from .cli import ScraperCLI
from .main import start_interactive_session, run_scraper, list_templates

# Initialize colorama
init(autoreset=True)


class InteractiveCLI:
    """Interactive menu-driven CLI for the web scraper."""
    
    def __init__(self):
        self.cli = ScraperCLI()
        self.running = True
    
    def display_header(self):
        """Display the application header."""
        print(f"\n{Back.BLUE}{Fore.WHITE}{'='*60}")
        print(f"🕷️  Interactive Web Scraper v2.0")
        print(f"   Playwright + Scrapling Integration")
        print(f"{'='*60}{Style.RESET_ALL}\n")
    
    def display_main_menu(self):
        """Display the main menu options."""
        print(f"{Fore.CYAN}📋 Main Menu:")
        print(f"{Fore.WHITE}1. 🎯 Create Template (Interactive)")
        print(f"{Fore.WHITE}2. 🤖 Run Scraping (Automated)")
        print(f"{Fore.WHITE}3. 📄 Template Management")
        print(f"{Fore.WHITE}4. ⚙️  Configuration")
        print(f"{Fore.WHITE}5. 🧹 Maintenance")
        print(f"{Fore.WHITE}6. 📊 Examples & Help")
        print(f"{Fore.RED}0. ❌ Exit")
        print()
    
    def get_user_choice(self, prompt: str = "Enter your choice: ", valid_choices: List[str] = None) -> str:
        """Get user input with validation."""
        while True:
            try:
                choice = input(f"{Fore.YELLOW}{prompt}{Style.RESET_ALL}").strip()
                if valid_choices is None or choice in valid_choices:
                    return choice
                else:
                    print(f"{Fore.RED}❌ Invalid choice. Please select from: {', '.join(valid_choices)}")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⏹️  Operation cancelled by user")
                return "0"
            except EOFError:
                return "0"
    
    def create_template_menu(self):
        """Interactive template creation menu."""
        print(f"\n{Fore.CYAN}🎯 Create Scraping Template")
        print(f"{Fore.WHITE}{'='*40}")
        
        # Get URL
        while True:
            url = input(f"{Fore.YELLOW}Enter target URL: {Style.RESET_ALL}").strip()
            if url:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                break
            print(f"{Fore.RED}❌ Please enter a valid URL")
        
        # Get output filename
        default_name = "template.json"
        output_file = input(f"{Fore.YELLOW}Output filename [{default_name}]: {Style.RESET_ALL}").strip()
        if not output_file:
            output_file = default_name
        
        if not output_file.endswith('.json'):
            output_file += '.json'
        
        # Ensure templates directory exists
        templates_dir = Path('templates')
        templates_dir.mkdir(exist_ok=True)
        
        if not output_file.startswith('templates/'):
            output_file = f"templates/{output_file}"
        
        # Headless mode option
        print(f"\n{Fore.CYAN}Browser Options:")
        print(f"{Fore.WHITE}1. Visual mode (browser window)")
        print(f"{Fore.WHITE}2. Headless mode (background)")
        
        browser_choice = self.get_user_choice("Choose browser mode [1]: ", ["1", "2", ""])
        headless = browser_choice == "2"
        
        try:
            print(f"\n{Fore.GREEN}🚀 Starting interactive session...")
            print(f"{Fore.WHITE}URL: {url}")
            print(f"{Fore.WHITE}Output: {output_file}")
            print(f"{Fore.WHITE}Mode: {'Headless' if headless else 'Visual'}")
            print()
            
            start_interactive_session(
                url=url,
                output_file=output_file,
                headless=headless
            )
            
            print(f"\n{Fore.GREEN}✅ Template creation completed!")
            print(f"{Fore.WHITE}📁 Saved to: {output_file}")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⏹️  Template creation cancelled")
        except Exception as e:
            print(f"\n{Fore.RED}❌ Error creating template: {e}")
        
        self.pause()
    
    def run_scraping_menu(self):
        """Interactive scraping execution menu."""
        print(f"\n{Fore.CYAN}🤖 Run Automated Scraping")
        print(f"{Fore.WHITE}{'='*40}")
        
        # List available templates
        templates_dir = Path('templates')
        if not templates_dir.exists():
            print(f"{Fore.RED}❌ No templates directory found")
            print(f"{Fore.WHITE}💡 Create templates first using option 1")
            self.pause()
            return
        
        template_files = list(templates_dir.glob('*.json'))
        if not template_files:
            print(f"{Fore.RED}❌ No templates found in templates/")
            print(f"{Fore.WHITE}💡 Create templates first using option 1")
            self.pause()
            return
        
        print(f"{Fore.WHITE}📋 Available templates:")
        for i, template_file in enumerate(template_files, 1):
            print(f"{Fore.WHITE}{i}. {template_file.name}")
        
        # Get template selection
        choice = self.get_user_choice(
            f"Select template [1-{len(template_files)}]: ",
            [str(i) for i in range(1, len(template_files) + 1)]
        )
        
        if choice == "0":
            return
        
        selected_template = template_files[int(choice) - 1]
        
        # Get output format
        print(f"\n{Fore.CYAN}Output Format:")
        print(f"{Fore.WHITE}1. JSON (structured data)")
        print(f"{Fore.WHITE}2. CSV (spreadsheet)")
        print(f"{Fore.WHITE}3. Excel (multi-sheet)")
        
        format_choice = self.get_user_choice("Choose format [1]: ", ["1", "2", "3", ""])
        format_map = {"1": "json", "2": "csv", "3": "excel", "": "json"}
        output_format = format_map[format_choice]
        
        # Generate output filename
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        template_name = selected_template.stem
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        output_file = str(output_dir / f"{template_name}_{timestamp}.{output_format}")
        
        try:
            print(f"\n{Fore.GREEN}🚀 Starting scraping...")
            print(f"{Fore.WHITE}Template: {selected_template}")
            print(f"{Fore.WHITE}Output: {output_file}")
            print(f"{Fore.WHITE}Format: {output_format.upper()}")
            print()
            
            output_path = run_scraper(
                template_file=str(selected_template),
                output_file=output_file,
                format=output_format
            )
            
            if output_path:
                print(f"\n{Fore.GREEN}✅ Scraping completed successfully!")
                print(f"{Fore.WHITE}📁 Output saved to: {output_path}")
            else:
                print(f"\n{Fore.RED}❌ Scraping failed - check logs for details")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⏹️  Scraping cancelled")
        except Exception as e:
            print(f"\n{Fore.RED}❌ Error during scraping: {e}")
        
        self.pause()
    
    def template_management_menu(self):
        """Template management submenu."""
        while True:
            print(f"\n{Fore.CYAN}📄 Template Management")
            print(f"{Fore.WHITE}{'='*40}")
            print(f"{Fore.WHITE}1. 📋 List templates")
            print(f"{Fore.WHITE}2. ✅ Validate template")
            print(f"{Fore.WHITE}3. 📝 Create example template")
            print(f"{Fore.WHITE}4. 🗑️  Delete template")
            print(f"{Fore.RED}0. ← Back to main menu")
            
            choice = self.get_user_choice("Select option: ", ["0", "1", "2", "3", "4"])
            
            if choice == "0":
                break
            elif choice == "1":
                self.list_templates()
            elif choice == "2":
                self.validate_template()
            elif choice == "3":
                self.create_example_template()
            elif choice == "4":
                self.delete_template()
    
    def list_templates(self):
        """List all available templates."""
        print(f"\n{Fore.CYAN}📋 Available Templates")
        print(f"{Fore.WHITE}{'='*40}")
        
        try:
            templates = list_templates('templates')
            if not templates:
                print(f"{Fore.YELLOW}📁 No templates found")
                print(f"{Fore.WHITE}💡 Create templates using option 1")
            else:
                for template in templates:
                    print(f"{Fore.GREEN}📄 {template['name']}")
                    print(f"{Fore.WHITE}   URL: {template['url']}")
                    print(f"{Fore.WHITE}   Elements: {template['elements']} | Actions: {template['actions']}")
                    print()
        except Exception as e:
            print(f"{Fore.RED}❌ Error listing templates: {e}")
        
        self.pause()
    
    def validate_template(self):
        """Validate a specific template."""
        templates_dir = Path('templates')
        if not templates_dir.exists():
            print(f"{Fore.RED}❌ No templates directory found")
            self.pause()
            return
        
        template_files = list(templates_dir.glob('*.json'))
        if not template_files:
            print(f"{Fore.RED}❌ No templates found")
            self.pause()
            return
        
        print(f"\n{Fore.CYAN}✅ Validate Template")
        print(f"{Fore.WHITE}{'='*40}")
        
        for i, template_file in enumerate(template_files, 1):
            print(f"{Fore.WHITE}{i}. {template_file.name}")
        
        choice = self.get_user_choice(
            f"Select template [1-{len(template_files)}]: ",
            [str(i) for i in range(1, len(template_files) + 1)]
        )
        
        if choice == "0":
            return
        
        selected_template = template_files[int(choice) - 1]
        
        try:
            from ..models.scraping_template import ScrapingTemplate
            template = ScrapingTemplate.load_from_file(str(selected_template))
            print(f"\n{Fore.GREEN}✅ Template is valid!")
            print(f"{Fore.WHITE}Name: {template.name}")
            print(f"{Fore.WHITE}URL: {template.url}")
            print(f"{Fore.WHITE}Elements: {len(template.elements)}")
            print(f"{Fore.WHITE}Actions: {len(template.actions)}")
        except Exception as e:
            print(f"\n{Fore.RED}❌ Template validation failed: {e}")
        
        self.pause()
    
    def create_example_template(self):
        """Create an example template."""
        print(f"\n{Fore.CYAN}📝 Create Example Template")
        print(f"{Fore.WHITE}{'='*40}")
        
        example_template = {
            "name": "example_template",
            "url": "https://news.ycombinator.com/",
            "elements": [
                {
                    "label": "stories",
                    "selector": ".storylink",
                    "element_type": "text",
                    "is_multiple": True,
                    "is_required": True
                },
                {
                    "label": "story_links",
                    "selector": ".storylink",
                    "element_type": "link",
                    "is_multiple": True,
                    "is_required": False
                }
            ],
            "actions": [],
            "cookies": [],
            "stealth_mode": True,
            "headless": False,
            "wait_timeout": 30
        }
        
        templates_dir = Path('templates')
        templates_dir.mkdir(exist_ok=True)
        
        example_file = templates_dir / 'example_template.json'
        
        try:
            import json
            with open(example_file, 'w') as f:
                json.dump(example_template, f, indent=2)
            
            print(f"{Fore.GREEN}✅ Example template created!")
            print(f"{Fore.WHITE}📁 Saved to: {example_file}")
            print(f"{Fore.WHITE}💡 This template scrapes Hacker News story titles")
            print(f"{Fore.WHITE}💡 Test it with option 2 (Run Scraping)")
        except Exception as e:
            print(f"{Fore.RED}❌ Error creating example: {e}")
        
        self.pause()
    
    def delete_template(self):
        """Delete a template file."""
        templates_dir = Path('templates')
        if not templates_dir.exists():
            print(f"{Fore.RED}❌ No templates directory found")
            self.pause()
            return
        
        template_files = list(templates_dir.glob('*.json'))
        if not template_files:
            print(f"{Fore.RED}❌ No templates found")
            self.pause()
            return
        
        print(f"\n{Fore.CYAN}🗑️  Delete Template")
        print(f"{Fore.WHITE}{'='*40}")
        
        for i, template_file in enumerate(template_files, 1):
            print(f"{Fore.WHITE}{i}. {template_file.name}")
        
        choice = self.get_user_choice(
            f"Select template to delete [1-{len(template_files)}]: ",
            [str(i) for i in range(1, len(template_files) + 1)]
        )
        
        if choice == "0":
            return
        
        selected_template = template_files[int(choice) - 1]
        
        # Confirm deletion
        confirm = self.get_user_choice(
            f"Are you sure you want to delete '{selected_template.name}'? [y/N]: ",
            ["y", "Y", "n", "N", ""]
        )
        
        if confirm.lower() == 'y':
            try:
                selected_template.unlink()
                print(f"\n{Fore.GREEN}✅ Template deleted successfully!")
            except Exception as e:
                print(f"\n{Fore.RED}❌ Error deleting template: {e}")
        else:
            print(f"\n{Fore.YELLOW}⏹️  Deletion cancelled")
        
        self.pause()
    
    def configuration_menu(self):
        """Configuration submenu."""
        while True:
            print(f"\n{Fore.CYAN}⚙️  Configuration")
            print(f"{Fore.WHITE}{'='*40}")
            print(f"{Fore.WHITE}1. 📋 View current settings")
            print(f"{Fore.WHITE}2. ⏱️  Set default timeout")
            print(f"{Fore.WHITE}3. 🕶️  Toggle stealth mode")
            print(f"{Fore.WHITE}4. 👁️  Toggle headless default")
            print(f"{Fore.WHITE}5. 📁 Set default directories")
            print(f"{Fore.RED}0. ← Back to main menu")
            
            choice = self.get_user_choice("Select option: ", ["0", "1", "2", "3", "4", "5"])
            
            if choice == "0":
                break
            elif choice == "1":
                self.view_config()
            elif choice == "2":
                self.set_timeout()
            elif choice == "3":
                self.toggle_stealth()
            elif choice == "4":
                self.toggle_headless()
            elif choice == "5":
                self.set_directories()
    
    def view_config(self):
        """View current configuration."""
        print(f"\n{Fore.CYAN}📋 Current Configuration")
        print(f"{Fore.WHITE}{'='*40}")
        print(f"{Fore.WHITE}Default timeout: 30 seconds")
        print(f"{Fore.WHITE}Stealth mode: Enabled")
        print(f"{Fore.WHITE}Headless default: Disabled")
        print(f"{Fore.WHITE}Templates directory: templates/")
        print(f"{Fore.WHITE}Output directory: output/")
        self.pause()
    
    def maintenance_menu(self):
        """Maintenance submenu."""
        while True:
            print(f"\n{Fore.CYAN}🧹 Maintenance")
            print(f"{Fore.WHITE}{'='*40}")
            print(f"{Fore.WHITE}1. 🗑️  Clean output files")
            print(f"{Fore.WHITE}2. 📊 View statistics")
            print(f"{Fore.WHITE}3. 📋 View logs")
            print(f"{Fore.WHITE}4. 🔧 Check dependencies")
            print(f"{Fore.RED}0. ← Back to main menu")
            
            choice = self.get_user_choice("Select option: ", ["0", "1", "2", "3", "4"])
            
            if choice == "0":
                break
            elif choice == "1":
                self.clean_files()
            elif choice == "2":
                self.view_statistics()
            elif choice == "3":
                self.view_logs()
            elif choice == "4":
                self.check_dependencies()
    
    def clean_files(self):
        """Clean output files."""
        print(f"\n{Fore.CYAN}🗑️  Clean Files")
        print(f"{Fore.WHITE}{'='*40}")
        
        output_dir = Path('output')
        if output_dir.exists():
            files = list(output_dir.glob('*'))
            if files:
                print(f"{Fore.WHITE}Found {len(files)} files in output/")
                confirm = self.get_user_choice("Delete all output files? [y/N]: ", ["y", "Y", "n", "N", ""])
                
                if confirm.lower() == 'y':
                    try:
                        for file in files:
                            file.unlink()
                        print(f"{Fore.GREEN}✅ Output files cleaned!")
                    except Exception as e:
                        print(f"{Fore.RED}❌ Error cleaning files: {e}")
                else:
                    print(f"{Fore.YELLOW}⏹️  Cleaning cancelled")
            else:
                print(f"{Fore.WHITE}📁 Output directory is already clean")
        else:
            print(f"{Fore.WHITE}📁 No output directory found")
        
        self.pause()
    
    def examples_help_menu(self):
        """Examples and help submenu."""
        while True:
            print(f"\n{Fore.CYAN}📊 Examples & Help")
            print(f"{Fore.WHITE}{'='*40}")
            print(f"{Fore.WHITE}1. 📖 Quick start guide")
            print(f"{Fore.WHITE}2. 💡 Best practices")
            print(f"{Fore.WHITE}3. 🔧 Troubleshooting")
            print(f"{Fore.WHITE}4. 📞 Support info")
            print(f"{Fore.RED}0. ← Back to main menu")
            
            choice = self.get_user_choice("Select option: ", ["0", "1", "2", "3", "4"])
            
            if choice == "0":
                break
            elif choice == "1":
                self.show_quick_start()
            elif choice == "2":
                self.show_best_practices()
            elif choice == "3":
                self.show_troubleshooting()
            elif choice == "4":
                self.show_support_info()
    
    def show_quick_start(self):
        """Show quick start guide."""
        print(f"\n{Fore.CYAN}📖 Quick Start Guide")
        print(f"{Fore.WHITE}{'='*40}")
        print(f"{Fore.WHITE}1. Create Template:")
        print(f"{Fore.WHITE}   • Choose option 1 from main menu")
        print(f"{Fore.WHITE}   • Enter target website URL")
        print(f"{Fore.WHITE}   • Browser opens with overlay panel")
        print(f"{Fore.WHITE}   • Click on elements to select them")
        print(f"{Fore.WHITE}   • Save template when finished")
        print()
        print(f"{Fore.WHITE}2. Run Scraping:")
        print(f"{Fore.WHITE}   • Choose option 2 from main menu")
        print(f"{Fore.WHITE}   • Select your saved template")
        print(f"{Fore.WHITE}   • Choose output format")
        print(f"{Fore.WHITE}   • Wait for completion")
        print()
        print(f"{Fore.WHITE}3. View Results:")
        print(f"{Fore.WHITE}   • Check output/ directory")
        print(f"{Fore.WHITE}   • Open files in appropriate application")
        self.pause()
    
    def pause(self):
        """Pause for user input."""
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def run(self):
        """Run the interactive CLI."""
        while self.running:
            try:
                self.display_header()
                self.display_main_menu()
                
                choice = self.get_user_choice("Enter your choice: ", ["0", "1", "2", "3", "4", "5", "6"])
                
                if choice == "0":
                    print(f"\n{Fore.GREEN}👋 Thank you for using Interactive Web Scraper!")
                    print(f"{Fore.WHITE}Happy scraping! 🕷️")
                    self.running = False
                elif choice == "1":
                    self.create_template_menu()
                elif choice == "2":
                    self.run_scraping_menu()
                elif choice == "3":
                    self.template_management_menu()
                elif choice == "4":
                    self.configuration_menu()
                elif choice == "5":
                    self.maintenance_menu()
                elif choice == "6":
                    self.examples_help_menu()
                    
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}⏹️  Operation cancelled by user")
                confirm = self.get_user_choice("Exit application? [y/N]: ", ["y", "Y", "n", "N", ""])
                if confirm.lower() == 'y':
                    self.running = False
            except Exception as e:
                print(f"\n{Fore.RED}❌ Unexpected error: {e}")
                print(f"{Fore.WHITE}Please report this issue if it persists.")
                self.pause()


def main():
    """Main entry point for interactive CLI."""
    cli = InteractiveCLI()
    cli.run()


if __name__ == '__main__':
    main()