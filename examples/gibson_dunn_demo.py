#!/usr/bin/env python3
"""
Demonstration of enhanced scraping features:
- AutoMatch integration for robust element selection
- Subpage navigation for comprehensive data extraction
- Action-based navigation for dynamic interactions

This demo shows how to extract Gibson Dunn lawyer data with full profiles.
"""

import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.core.scrapling_runner_refactored import ScraplingRunner
from src.models.scraping_template import ScrapingTemplate

def demonstrate_enhanced_scraping():
    """Demonstrate the enhanced scraping capabilities"""
    
    print("🕷️ Enhanced Web Scraping Demonstration")
    print("=" * 50)
    
    # Load the enhanced template
    template_path = Path(__file__).parent.parent / "templates" / "gibson_dunn_enhanced.json"
    
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"📄 Loading template: {template_path.name}")
    
    # Load and parse template
    with open(template_path, 'r') as f:
        template_data = json.load(f)
    
    template = ScrapingTemplate(**template_data)
    
    print(f"✅ Template loaded: {template.name}")
    print(f"🎯 Target URL: {template.url}")
    print(f"📊 Elements configured: {len(template.elements)}")
    
    # Check for enhanced features
    enhanced_features = []
    for element in template.elements:
        if hasattr(element, 'follow_links') and element.follow_links:
            enhanced_features.append("Subpage Navigation")
        if hasattr(element, 'subpage_elements') and element.subpage_elements:
            enhanced_features.append("Enhanced Data Extraction")
    
    if template.actions:
        enhanced_features.append("Action-based Navigation")
    
    if template.pagination:
        enhanced_features.append("Pagination Support")
    
    print(f"🚀 Enhanced features: {', '.join(enhanced_features)}")
    print()
    
    # Initialize and run scraper
    print("🤖 Starting enhanced scraping process...")
    runner = ScraplingRunner(template)
    
    try:
        result = runner.execute_scraping()
        
        if result.success:
            print("✅ Scraping completed successfully!")
            print(f"📁 Data extracted for {len(result.data.get('lawyer_cards', []))} lawyers")
            
            # Show sample of enhanced data
            lawyers = result.data.get('lawyer_cards', [])
            if lawyers:
                sample_lawyer = lawyers[0]
                print(f"\n📋 Sample lawyer data for: {sample_lawyer.get('name', 'Unknown')}")
                print(f"   📧 Email: {sample_lawyer.get('email', 'N/A')}")
                print(f"   🏢 Title: {sample_lawyer.get('title', 'N/A')}")
                print(f"   🔗 Profile: {sample_lawyer.get('profile_link', 'N/A')}")
                
                # Show subpage data if available
                subpage_fields = ['full_bio', 'education', 'experience', 'publications']
                subpage_data = {k: v for k, v in sample_lawyer.items() if k in subpage_fields and v}
                
                if subpage_data:
                    print(f"   📚 Enhanced data: {list(subpage_data.keys())}")
                else:
                    print(f"   📚 Enhanced data: None extracted (selectors may need adjustment)")
            
            # Show pagination results
            pages_data = result.data.get('pages', [])
            if pages_data:
                print(f"\n📄 Pagination results: {len(pages_data)} pages processed")
                total_lawyers = sum(len(page.get('data', {}).get('lawyer_cards', [])) for page in pages_data)
                print(f"   👥 Total lawyers across all pages: {total_lawyers}")
        
        else:
            print("❌ Scraping failed:")
            for error in result.errors:
                print(f"   • {error}")
    
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
    
    print("\n🎯 Key Benefits of Enhanced Features:")
    print("   • AutoMatch: Adapts to website changes automatically")
    print("   • Subpage Navigation: Extracts comprehensive profile data")
    print("   • Action Navigation: Handles dynamic interactions")
    print("   • Intelligent Pagination: Scales to handle thousands of records")

if __name__ == "__main__":
    demonstrate_enhanced_scraping()