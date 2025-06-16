# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
 
### Memory RULES: Web Scraping Best Practices

1) **When a file size is greater than the token limit (over 600 lines of code), read the entire file by quarters.**
2) **ALWAYS make backup files before making edits.**
3) **Never edit any templates or outputs.**
4) **NEVER hard code or make something code-wise that is for a specific webpage.**
## Project Overview

This is a production-ready interactive web scraping tool that combines visual element selection with automated data extraction. The tool enables users to create scraping templates by clicking on elements in a real browser, then execute those templates programmatically for large-scale data extraction.

**Core Integration:**
- **Playwright**: Browser automation for interactive template creation
- **Scrapling**: High-performance scraping engine for automated execution - https://github.com/D4Vinci/Scrapling
- **Visual Container Selection**: Advanced "point-and-click" interface for selecting repeating patterns

The application provides a clean separation between interactive template creation and automated scraping execution, making it perfect for both beginners and power users.

## Key Commands

### Interactive Template Creation
```bash
# Start interactive browser session
python -m src.core.main interactive https://example.com --output my_template.json

# Run in headless mode
python -m src.core.main interactive https://example.com --headless
```

### Automated Scraping
```bash
# Execute scraping with template
python -m src.core.main scrape templates/my_template.json --format json

# Export to different formats
python -m src.core.main scrape templates/my_template.json --format csv
python -m src.core.main scrape templates/my_template.json --format excel
```

### Template Management
```bash
# List all available templates
python -m src.core.main list
```

### Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v
pytest tests/test_scrapling_runner.py -v

# Quick testing scripts
python quick_test.py
python test_corrected_template.py
python test_fixed_template.py
python test_working_template.py
```

## Architecture

### Clean Project Structure
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
│   ├── gibsondunn.com_*_*.json          # Sample output files
│   └── ...                              # Additional scraped data
├── 📁 examples/                         # Example scripts & demonstrations
│   └── gibson_dunn_demo.py              # Gibson Dunn scraping demo
├── 📁 tests/                            # Test suite
│   ├── __init__.py                      # Package initialization
│   ├── test_models.py                   # Template model tests
│   └── test_scrapling_runner.py         # Scraping engine tests
├── 📄 requirements.txt                  # Python dependencies
├── 📄 CLAUDE.md                         # Claude Code guidance & project rules
├── 📄 README.md                         # This file - project documentation
├── 📄 quick_test.py                     # Quick testing script
├── 📄 test_*.py                         # Additional test scripts
└── 📁 venv/                             # Virtual environment (gitignored)
```

### Core Components

- **InteractiveSession** (`main.py`): Manages Playwright browser sessions for template creation
- **ScraplingRunner** (`scrapling_runner.py`): Executes automated scraping using Scrapling
- **ScrapingTemplate** (`scraping_template.py`): Pydantic models for template validation
- **Interactive Overlay** (`interactive_session.js`): Browser-based element selection interface

### Workflow
1. **Interactive Session**: Launch Playwright browser with custom overlay
2. **Visual Element Selection**: Use 4 distinct tools (Element, Action, Scroll, Container)
3. **Container-Based Extraction**: Click on repeating patterns, then sub-elements within
4. **Template Generation**: Create validated JSON template with selectors and metadata
5. **Automated Execution**: Use Scrapling to execute scraping based on template
6. **Data Export**: Output results in JSON, CSV, or Excel formats

## Key Features

### Visual Container Selection (Primary Feature)
The Container tool is the most powerful feature:
- **Smart Pattern Detection**: Click on any repeating element (product card, profile, article)
- **Sub-Element Selection**: Click inside containers to visually define data extraction points
- **Automatic Scaling**: Finds all similar elements automatically
- **Relative Selectors**: Generates smart CSS selectors that work across all similar containers

### Four Interactive Tools
1. **📌 Element Tool**: Select individual elements for single data points
2. **🔗 Action Tool**: Define navigation actions (clicks, loads, pagination)
3. **📜 Scroll Tool**: Configure infinite scroll and load-more patterns
4. **📦 Container Tool**: ⭐ The power feature for bulk data extraction

### Advanced Scraping Capabilities
- **AutoMatch Integration**: Scrapling's intelligent element detection that adapts to website changes
- **Sub-page Navigation**: Automatic navigation to profile links with additional data extraction
- **Action-based Navigation**: Click actions automatically navigate to target URLs
- **Comprehensive Error Handling**: Robust fallback strategies and logging
- **Multi-format Export**: JSON, CSV, and Excel output with proper data structure

### Key Dependencies
```
scrapling      # High-performance scraping engine
playwright     # Browser automation for interactive sessions
pandas         # Data processing and CSV/Excel export
openpyxl       # Excel file creation
pydantic       # Data validation and settings management
pytest         # Testing framework
```

### Environment Setup
```bash
# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Critical: Install Playwright browsers
playwright install chromium
```

## Enhanced Container Workflow

### Container-First Approach
This is the recommended workflow for extracting repeating data:

```json
{
  "elements": [
    {
      "label": "lawyer_cards",
      "selector": ".people.loading",
      "is_container": true,
      "is_multiple": true,
      "sub_elements": [
        {"label": "name", "selector": "p.name strong", "element_type": "text"},
        {"label": "title", "selector": "p.title span", "element_type": "text"},
        {"label": "email", "selector": "p.contact-details a", "element_type": "text"},
        {"label": "profile_link", "selector": "a", "element_type": "link"}
      ]
    }
  ]
}
```

### Visual Sub-Element Selection Process
1. **Select Container**: Click Container tool → Click on any repeating element
2. **Confirm Pattern**: System detects similar elements, user confirms
3. **Add Sub-Elements**: Click inside the container to define what data to extract
4. **Label Elements**: Provide semantic names ("name", "price", "link")
5. **Auto-Generate**: System creates relative selectors automatically

## Scrapling Integration & Advanced Patterns

### Understanding Scrapling's Power
Scrapling provides powerful element selection and adaptation capabilities:

**AutoMatch Technology:**
```python
# Scrapling adapts to website changes automatically
elements = page.css('.product-card', auto_match=True)
```

**Benefits:**
- Survives website redesigns and structure changes
- Finds elements even when classes/IDs change
- Reduces template maintenance overhead
- Uses semantic similarity for robust selection

### Container + AutoMatch Workflow
The combination of visual container selection + Scrapling's AutoMatch creates extremely robust scraping:

1. **Visual Creation**: User clicks on containers and sub-elements visually
2. **Smart Selectors**: System generates selectors optimized for AutoMatch
3. **Adaptive Execution**: Scrapling adapts selectors during execution
4. **Minimal Maintenance**: Templates continue working despite website changes

### Production Implementation

#### Bulk Data Extraction
```python
# Example: Extract all lawyers from firm directory
template = {
    "elements": [
        {
            "label": "lawyers",
            "selector": ".people-card",
            "is_container": True,
            "sub_elements": [
                {"label": "name", "selector": "h3"},
                {"label": "practice_area", "selector": ".practice"},
                {"label": "email", "selector": ".email"}
            ]
        }
    ]
}
# Results in structured data for 100s of lawyers
```

#### Sub-page Enhancement
```python
# Automatic navigation to individual profiles
template = {
    "elements": [
        {
            "label": "lawyers",
            "follow_links": True,
            "subpage_elements": [
                {"label": "full_bio", "selector": ".biography"},
                {"label": "education", "selector": ".education"},
                {"label": "experience", "selector": ".experience"}
            ]
        }
    ]
}
```

## Development Guidelines

### File Organization & Data Flow
- **Entry Point**: `src/core/main.py` - CLI interface and InteractiveSession management
- **Browser Integration**: `src/interactive/index.js` - **Modular browser overlay system**
- **Automated Execution**: `src/core/scrapling_runner.py` - ScraplingRunner class for template execution
- **Data Models**: `src/models/scraping_template.py` - Pydantic models (ScrapingTemplate, ElementSelector, SubElement)
- **Templates**: JSON files in `templates/` directory - User-generated configurations
- **Output**: `output/` directory - Scraped data in JSON/CSV/Excel formats
- **Logs**: `scraper.log` and `logs/` directory for debugging information

### Modular Interactive System Architecture
```
src/interactive/
├── index.js                    # Main entry point & orchestration
├── core/
│   ├── state-manager.js        # Centralized state management  
│   ├── event-manager.js        # Event delegation & handling
│   ├── error-handler.js        # Error handling utilities
│   └── config.js              # Configuration constants
├── ui/
│   ├── modal-manager.js        # Modal dialogs & prompts
│   ├── control-panel.js        # Main control panel UI
│   ├── styles.js              # CSS injection & styling
│   └── status-manager.js       # Status updates & feedback
├── tools/
│   ├── base-tool.js           # Base tool interface
│   ├── element-tool.js         # Element selection functionality
│   ├── action-tool.js          # Action selection & handling
│   ├── container-tool.js       # Container selection logic
│   └── scroll-tool.js          # Scroll/pagination handling
├── selectors/
│   └── selector-generator.js   # CSS selector generation
├── navigation/
│   └── state-persistence.js    # Save/restore session state
└── utils/
    ├── dom-utils.js            # DOM manipulation helpers
    ├── template-builder.js     # Template generation logic
    └── python-bridge.js        # Python callback interface
```

### Core Data Flow
1. **Interactive Session** → Visual element selection → Template JSON generation
2. **Template Validation** → Pydantic models ensure data integrity  
3. **ScraplingRunner** → Loads template → Executes scraping → Exports results
4. **Output Processing** → JSON/CSV/Excel files with structured data

### Adding New Features
1. **Interactive Features**: Extend existing tool classes or create new ones in `tools/`
2. **UI Components**: Add new UI modules in `ui/` directory
3. **Scraping Logic**: Extend `scrapling_runner.py` for execution capabilities
4. **Data Models**: Update `scraping_template.py` for new template fields
5. **CLI Commands**: Add to `main.py` and `cli.py` for new command-line options

### Modular System Benefits
- **70% Smaller Files**: Main entry point is ~300 lines vs 3600+ lines
- **Better Maintainability**: Each module has single responsibility
- **Enhanced Testability**: Individual modules can be unit tested
- **Code Reusability**: Components can be imported and reused
- **Easier Debugging**: Issues isolated to specific modules
- **Future Extensibility**: Easy to add new tools or UI components

### Testing Strategy & Debugging
```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_models.py -v
pytest tests/test_scrapling_runner.py -v

# Quick test scripts for template validation
python quick_test.py
python test_working_template.py
python test_corrected_template.py
python test_fixed_template.py
```

**Debugging Templates:**
- Check `scraper.log` for detailed error logs
- Examine template JSON structure in `templates/` directory  
- Use browser dev tools to verify selectors work correctly
- Test templates with small datasets before running full extraction

### Best Practices

1. **Container-First Thinking**: Always look for repeating patterns first
2. **Semantic Labeling**: Use descriptive names that explain the data
3. **Robust Selectors**: Prefer class-based selectors over position-based
4. **Error Handling**: Implement fallback strategies for dynamic content
5. **Performance**: Add appropriate delays and respect rate limits

## Common Use Cases & Patterns

### E-commerce Product Extraction
- **Container**: Product cards, search results
- **Sub-elements**: Name, price, image, rating, availability
- **Actions**: Load more, pagination, category navigation

### Professional Directory Scraping
- **Container**: Profile cards, member listings
- **Sub-elements**: Name, title, company, contact info
- **Enhancement**: Navigate to individual profiles for detailed information

### News & Content Aggregation
- **Container**: Article listings, blog posts
- **Sub-elements**: Headline, author, date, summary, full link
- **Pagination**: Handle multiple pages of articles

### Real Estate Listings
- **Container**: Property cards, search results
- **Sub-elements**: Address, price, features, photos, agent info
- **Actions**: Navigate through listing pages, apply filters

## Important Notes

### Visual Selection Benefits
- **No CSS Knowledge Required**: Users click, system generates selectors
- **Immediate Feedback**: See exactly what will be extracted
- **Pattern Recognition**: Automatically finds similar elements
- **Robust Output**: Generated selectors work reliably in production

### Production Reliability
- **Scrapling AutoMatch**: Adapts to website changes automatically
- **Fallback Strategies**: Multiple selector approaches for reliability
- **Error Recovery**: Graceful handling of missing elements
- **Monitoring**: Detailed logging for debugging and maintenance

### Maintenance
- **Template Validation**: Regular checks ensure templates still work
- **Update Detection**: System can detect when sites change significantly
- **Selector Evolution**: AutoMatch improves selectors over time

The system excels at transforming complex, repetitive web data extraction into a simple point-and-click workflow while maintaining production-grade reliability and performance.

## Troubleshooting Common Issues

### Playwright Browser Issues
```bash
# Browser fails to start
playwright install chromium --force

# Permission issues on Linux/Mac
sudo playwright install-deps chromium
```

### Template Execution Problems
- **Elements not found**: Check selectors in browser dev tools, ensure dynamic content has loaded
- **Empty results**: Verify is_multiple flag matches expected element count
- **Timeout errors**: Increase wait_timeout in template or add explicit waits
- **Memory issues**: Process smaller batches, clear browser cache between runs

### Template Structure Reference
```json
{
  "name": "template_name",
  "url": "target_url", 
  "elements": [
    {
      "label": "container_name",
      "selector": ".css-selector",
      "is_container": true,
      "is_multiple": true,
      "sub_elements": [
        {"label": "field_name", "selector": "relative_selector", "element_type": "text"}
      ]
    }
  ],
  "actions": [
    {"label": "action_name", "selector": ".button", "action_type": "click"}
  ]
}
```

