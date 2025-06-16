# 🕷️ Interactive Web Scraper

A powerful web scraping tool that combines visual element selection with automated data extraction. Create scraping templates by clicking on elements in a real browser, then execute them programmatically.

## 🌟 Key Features

### 🎯 Visual Template Creation
- **Point-and-Click Interface**: Select elements visually in a real browser
- **Container Recognition**: Smart detection of repeating patterns (product cards, lists, etc.)
- **Sub-Element Selection**: Click inside containers to define structured data extraction
- **Real-time Preview**: See exactly what will be scraped as you build templates

### 🤖 Automated Execution
- **High-Performance Scraping**: Built on Scrapling for robust data extraction
- **AutoMatch Technology**: Adapts to website changes automatically
- **Multi-Format Export**: JSON, CSV, and Excel output
- **Batch Processing**: Process multiple URLs with the same template

### 📦 Container-Based Scraping
- **Repeating Patterns**: Perfect for product listings, profiles, articles
- **Visual Sub-Elements**: Click on names, prices, links inside each container
- **Automatic Scaling**: Handles hundreds of similar items efficiently
- **Smart Selectors**: Generates robust CSS selectors that survive design changes

## 🚀 Quick Start

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd Scraper_V2
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   playwright install
   ```

### Create Your First Template

```bash
# Start interactive session
python -m src.core.main interactive https://example.com --output my_template.json
```

This opens a browser with an overlay panel. You can:
1. **Select Containers**: Click on repeating elements (product cards, profiles, etc.)
2. **Add Sub-Elements**: Click inside containers to extract names, prices, links
3. **Define Actions**: Click on "Load More" buttons, navigation links
4. **Save Template**: Save your configuration as a reusable JSON template

### Run Automated Scraping

```bash
# Execute scraping with your template
python -m src.core.main scrape templates/my_template.json --format json

# Export to different formats
python -m src.core.main scrape templates/my_template.json --format csv
python -m src.core.main scrape templates/my_template.json --format excel
```

## 🎮 Interactive Interface

The browser overlay provides four main tools:

### 📌 Element Tool
- Click individual elements to extract single values
- Perfect for titles, descriptions, unique content

### 🔗 Action Tool  
- Define navigation actions (clicks, scrolls)
- Handle "Load More" buttons, pagination
- Enable comprehensive data collection

### 📜 Scroll Tool
- Configure infinite scroll handling
- Auto-detect pagination patterns
- Extract all available data, not just visible items

### 📦 Container Tool ⭐
- **The Power Feature**: Click on repeating containers
- Automatically detects similar patterns
- Visual sub-element selection within containers
- Perfect for product listings, profiles, articles

## 📝 Template Examples

### Basic Product Scraping
```json
{
  "name": "product_scraper",
  "url": "https://shop.example.com",
  "elements": [
    {
      "label": "product_cards",
      "selector": ".product-item",
      "is_container": true,
      "is_multiple": true,
      "sub_elements": [
        {"label": "name", "selector": "h3", "element_type": "text"},
        {"label": "price", "selector": ".price", "element_type": "text"},
        {"label": "link", "selector": "a", "element_type": "link"}
      ]
    }
  ]
}
```

### With Pagination
```json
{
  "name": "comprehensive_scraper",
  "elements": [...],
  "actions": [
    {
      "label": "load_more",
      "selector": "button.load-more",
      "action_type": "click",
      "wait_after": 2.0
    }
  ]
}
```

## 🎯 Perfect Use Cases

### E-commerce
- **Product Listings**: Names, prices, descriptions, images
- **Review Extraction**: User reviews, ratings, dates
- **Inventory Monitoring**: Stock levels, price changes

### Professional Networks
- **Profile Extraction**: Names, titles, companies, contact info
- **Directory Scraping**: Member listings, professional details
- **Company Information**: Team pages, employee lists

### News & Content
- **Article Extraction**: Headlines, content, authors, dates
- **Social Media**: Posts, comments, engagement metrics
- **Event Listings**: Dates, venues, descriptions

### Real Estate
- **Property Listings**: Prices, features, locations
- **Agent Directories**: Contact information, specialties
- **Market Data**: Trends, statistics, comparisons

## 📊 Output Formats

### JSON (Structured Data)
```json
{
  "template_name": "product_scraper",
  "success": true,
  "data": {
    "product_cards": [
      {
        "name": "Widget Pro",
        "price": "$29.99",
        "link": "https://example.com/widget-pro"
      }
    ]
  },
  "metadata": {
    "elements_found": 15,
    "scraped_at": "2024-01-15T10:30:00Z"
  }
}
```

### CSV (Tabular Data)
```csv
name,price,link
"Widget Pro","$29.99","https://example.com/widget-pro"
"Widget Basic","$19.99","https://example.com/widget-basic"
```

### Excel (Multi-Sheet)
- **Main Data**: Scraped information
- **Metadata**: Session details, statistics
- **Errors**: Any issues encountered

## 🔧 Advanced Features

### AutoMatch Technology
- Automatically adapts to website design changes
- Finds elements even when CSS classes change
- Reduces template maintenance overhead

### Smart Container Detection
- Recognizes repeating patterns automatically
- Generates optimal selectors for bulk extraction
- Handles dynamic content loading

### Anti-Detection
- Stealth mode for public data extraction
- Automatic cookie consent handling
- Human-like interaction patterns

### Error Recovery
- Robust error handling and retries
- Fallback selector strategies
- Detailed logging and debugging

## 📁 Project Structure

```
Scraper_V2/
├── 📁 src/                              # Main source code
│   ├── 📁 core/                         # Core scraping functionality
│   │   ├── __init__.py                  # Package initialization
│   │   ├── __main__.py                  # Module entry point
│   │   ├── cli.py                       # Command-line interface
│   │   ├── interactive_cli.py           # Interactive CLI utilities
│   │   ├── main.py                      # Session management & Playwright integration
│   │   └── scrapling_runner.py          # Automated scraping execution engine
│   ├── 📁 interactive/                  # Browser-based interactive system
│   │   ├── __init__.py                  # Package initialization
│   │   ├── index.js                     # Main entry point & orchestration
│   │   ├── 📁 core/                     # Core interactive functionality
│   │   │   ├── config.js                # Configuration constants
│   │   │   ├── error-handler.js         # Error handling utilities
│   │   │   ├── event-manager.js         # Event delegation & handling
│   │   │   └── state-manager.js         # Centralized state management
│   │   ├── 📁 navigation/               # Navigation & session management
│   │   │   └── state-persistence.js     # Save/restore session state
│   │   ├── 📁 selectors/                # CSS selector generation
│   │   │   └── selector-generator.js    # Smart CSS selector creation
│   │   ├── 📁 tools/                    # Interactive selection tools
│   │   │   ├── base-tool.js             # Base tool interface
│   │   │   ├── element-tool.js          # Element selection functionality
│   │   │   ├── action-tool.js           # Action selection & handling
│   │   │   ├── container-tool.js        # Container selection logic (⭐ power feature)
│   │   │   └── scroll-tool.js           # Scroll/pagination handling
│   │   ├── 📁 ui/                       # User interface components
│   │   │   ├── control-panel.js         # Main control panel UI
│   │   │   ├── modal-manager.js         # Modal dialogs & prompts
│   │   │   ├── status-manager.js        # Status updates & feedback
│   │   │   └── styles.js                # CSS injection & styling
│   │   └── 📁 utils/                    # Utility functions
│   │       ├── dom-utils.js             # DOM manipulation helpers
│   │       ├── python-bridge.js         # Python callback interface
│   │       └── template-builder.js      # Template generation logic
│   └── 📁 models/                       # Data models & validation
│       ├── __init__.py                  # Package initialization
│       └── scraping_template.py         # Pydantic models for templates
├── 📁 templates/                        # Generated JSON templates
│   └── template.json                    # Example/current template
├── 📁 output/                           # Scraped data files (JSON/CSV/Excel)
│   └── ...                              # Additional scraped data
├── 📁 examples/                         # Example scripts & demonstrations
├── 📁 tests/                            # Test suite
│   ├── __init__.py                      # Package initialization
│   ├── test_models.py                   # Template model tests
│   └── test_scrapling_runner.py         # Scraping engine tests
├── 📄 requirements.txt                  # Python dependencies
├── 📄 README.md                         # This file - project documentation
├── 📄 quick_test.py                     # Quick testing script
├── 📄 test_*.py                         # Additional test scripts
└── 📁 venv/                             # Virtual environment (gitignored)
```

### 🔍 File Descriptions

#### Core Python Files
- **`main.py`**: Manages Playwright browser sessions, handles interactive template creation
- **`scrapling_runner.py`**: Executes automated scraping using Scrapling engine, handles data export
- **`cli.py`**: Command-line interface for interactive and scraping commands
- **`scraping_template.py`**: Pydantic data models for template validation and structure

#### Interactive JavaScript System
- **`index.js`**: Main orchestrator for browser overlay, coordinates all interactive tools
- **`container-tool.js`**: ⭐ Primary feature - visual container selection and sub-element extraction
- **`element-tool.js`**: Single element selection for unique data points
- **`action-tool.js`**: Navigation actions (clicks, loads, pagination)
- **`scroll-tool.js`**: Infinite scroll and load-more pattern handling
- **`template-builder.js`**: Generates JSON templates from interactive selections

#### Configuration & Testing
- **`requirements.txt`**: Python dependencies (Scrapling, Playwright, Pydantic, etc.)
- **`test_*.py`**: Template validation and functionality testing scripts
- **`CLAUDE.md`**: Development guidelines and architectural documentation

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_models.py
```

## 🎯 Best Practices

### Template Creation
1. **Start with Containers**: Look for repeating patterns first
2. **Test Selectors**: Verify they work across multiple similar items
3. **Use Semantic Labels**: Choose descriptive names like "product_title" not "element_1"
4. **Handle Pagination**: Add scroll/load more actions for complete data

### Production Scraping
1. **Respect Rate Limits**: Add delays between requests
2. **Monitor Changes**: Validate templates periodically
3. **Handle Errors**: Check scraping results for success/failure
4. **Scale Appropriately**: Use batch processing for large datasets

## 🔍 Common Workflows

### Law Firm Directory (Example)
1. Navigate to firm's people page
2. Click **Container Tool** → Click on any lawyer card
3. System detects all similar lawyer cards
4. Click inside first card to add sub-elements:
   - Click name → Label: "name"
   - Click title → Label: "title"  
   - Click email → Label: "email"
   - Click profile link → Label: "profile_link"
5. Add pagination if needed (Load More button)
6. Save template
7. Run automated extraction for all lawyers

### E-commerce Products
1. Navigate to product listing page
2. Use **Container Tool** on product cards
3. Extract names, prices, images, links
4. Add **Scroll Tool** for infinite scroll
5. Execute to get complete product catalog

## 🆘 Troubleshooting

### Browser Won't Start
```bash
# Reinstall Playwright browsers
playwright install chromium
```

### Elements Not Found
- Verify selectors in browser dev tools
- Check if content loads dynamically
- Use AutoMatch for adaptive selection

### Performance Issues
- Add delays between actions
- Reduce concurrent processing
- Clean temporary files regularly

## 🔗 Dependencies

- **Scrapling**: High-performance scraping engine
- **Playwright**: Browser automation for interactive sessions
- **Pydantic**: Data validation and settings
- **Pandas**: Data processing and export

---

**Built for efficiency, designed for scale** 🚀

Transform any website into structured data with just a few clicks!
