#!/usr/bin/env python3
"""
Test script for the refactored ScraplingRunner
"""

import json
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.scrapling_runner_refactored import ScraplingRunner
from src.models.scraping_template import ScrapingTemplate

def load_template(template_path: str) -> ScrapingTemplate:
    """Load template from JSON file."""
    with open(template_path, 'r') as f:
        template_data = json.load(f)
    
    return ScrapingTemplate(**template_data)

def test_refactored_runner():
    """Test the refactored ScraplingRunner."""
    try:
        print("🕷️ Testing Refactored ScraplingRunner")
        print("="*50)
        
        # Load template
        template_path = "templates/output_new.json"
        print(f"📄 Loading template: {template_path}")
        template = load_template(template_path)
        
        print(f"✅ Template loaded:")
        print(f"   Name: {template.name}")
        print(f"   URL: {template.url}")
        print(f"   Elements: {len(template.elements)}")
        
        # Create runner
        print("\n🏃 Creating ScraplingRunner...")
        runner = ScraplingRunner(template)
        print("✅ Runner created successfully!")
        
        # Execute scraping
        print("\n🚀 Starting scraping execution...")
        result = runner.execute_scraping()
        
        print(f"\n📊 Scraping Results:")
        print(f"   Success: {result.success}")
        print(f"   Template: {result.template_name}")
        print(f"   URL: {result.url}")
        print(f"   Data keys: {list(result.data.keys()) if result.data else 'None'}")
        print(f"   Errors: {len(result.errors)}")
        
        if result.errors:
            print(f"\n❌ Errors encountered:")
            for error in result.errors:
                print(f"   • {error}")
        
        if result.data:
            print(f"\n📈 Data Summary:")
            for key, value in result.data.items():
                if isinstance(value, list):
                    print(f"   {key}: {len(value)} items")
                else:
                    print(f"   {key}: {type(value).__name__}")
        
        print(f"\n🎯 Test completed!")
        return result.success
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_refactored_runner()
    sys.exit(0 if success else 1)