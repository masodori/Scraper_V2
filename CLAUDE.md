# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL RULES (ALWAYS FOLLOW)

### Memory RULES: Web Scraping Best Practices

1. **NEVER edit any templates or outputs** - Templates are user-generated and should not be modified
2. **ALWAYS make backup files before making edits** - Preserve original code before modifications
3. **NEVER hard code or make something code-wise that is for a specific webpage** - Keep code generic and reusable
4. **When a file size is greater than the token limit (over 600 lines of code), read the entire file by quarters** - Handle large files systematically
5. **Use the new refactored directory structure** - Work with the modular architecture components, not the old monolithic files

## 🏗️ High-Level Architecture

### Two-Phase System
The scraper operates in two distinct phases:
1. **Interactive Phase**: Visual template creation through browser overlay with Playwright
2. **Automated Phase**: Template execution with Scrapling engine

### Core Integration Points
- **Playwright**: Powers the interactive browser session for template creation
- **Scrapling**: High-performance scraping engine for automated execution (https://github.com/D4Vinci/Scrapling)
- **Container-First Design**: The primary pattern is container-based extraction for repeating elements

### Refactored Modular Architecture (v2.0)
The system now uses 8 specialized modules instead of one monolithic file:

```
src/core/
├── scrapling_runner_refactored.py    # Main orchestrator (300 lines)
├── context.py                        # Shared state management
├── utils/progress.py                 # Progress tracking & ETA
├── analyzers/template_analyzer.py    # Directory & pattern detection
├── selectors/selector_engine.py      # Smart selector mapping
├── extractors/data_extractor.py      # Multi-strategy element finding
├── handlers/pagination_handler.py    # Pagination logic
└── processors/subpage_processor.py   # Subpage processing
```

## 🔧 Core Commands

### Development Environment Setup
```bash
# Virtual environment setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Playwright browsers (critical for first-time setup)
playwright install chromium

# Run tests
pytest tests/ -v
pytest tests/test_models.py -v
pytest tests/test_scrapling_runner.py -v

# Quick testing scripts
python quick_test.py
python test_corrected_template.py
python test_fixed_template.py
python test_working_template.py
```

### Interactive Template Creation
```bash
# Start interactive browser session
python -m src.core.main interactive https://example.com --output my_template.json

# Run in headless mode
python -m src.core.main interactive https://example.com --headless
```

### Automated Scraping Execution
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

## 🎯 Critical Component Interactions

### Template Flow
1. `src/core/main.py` → Launches Playwright browser with interactive overlay
2. `src/interactive/index.js` → Injects JavaScript tools into the page
3. User clicks elements → JavaScript generates selectors and structure
4. `src/interactive/utils/template-builder.js` → Creates JSON template
5. `src/models/scraping_template.py` → Validates template structure
6. `src/core/scrapling_runner_refactored.py` → Executes template with Scrapling

### Modular Interactive System
The JavaScript overlay is modular with clear separation:
- **Tools** (`tools/`): Each tool (Element, Container, Action, Scroll) is independent
- **UI** (`ui/`): Modal system, control panel, status manager
- **Core** (`core/`): State management, event handling, error handling
- **Utils** (`utils/`): DOM utilities, Python bridge, template builder

### Browser Session Management
- `ScraplingRunner` maintains a single browser instance (`self.fetcher_instance`)
- Reuses browser session for all page navigations (critical for performance)
- Proper cleanup in `_cleanup()` method and destructor

## 🎨 Key Architectural Decisions

1. **Separation of Concerns**: Interactive (Playwright) and automated (Scrapling) phases are completely separated
2. **Container-Based Extraction**: Primary pattern for handling repeating elements with sub-elements
3. **Smart Selector Enhancement**: Automatic mapping of generic selectors to semantic ones
4. **Browser Session Reuse**: Single browser instance for all subpage navigations
5. **Modular JavaScript**: Each interactive tool is self-contained for maintainability
6. **Composition Over Inheritance**: Refactored architecture uses composition for flexibility

### Data Flow Patterns

#### Container Extraction
```
Container Detection → Sub-Element Selection → Template Generation → Scrapling Execution
```

#### Subpage Navigation
```
Main Page → Extract Profile Links → Navigate to Each → Extract Subpage Data → Merge Results
```

## 🛠️ Working with the Refactored Architecture

### Always Use These Components:
- **scrapling_runner_refactored.py** (NOT scrapling_runner.py)
- **Components in src/core/analyzers/, extractors/, handlers/, processors/**
- **Modular approach** for any new features

### Never Use These (Legacy):
- **scrapling_runner.py** (the old monolithic file)
- **scrapling_runner.py.backup*** (backup files)

### Development Guidelines:
1. **Work with modules**: Each component has a single responsibility
2. **Use composition**: Combine components rather than creating monoliths
3. **Test components independently**: Each module can be unit tested
4. **Follow the refactored patterns**: Use the established modular architecture

## 📋 Important Implementation Details

1. **Scrapling API Changes**: Use `PlayWrightFetcher.configure()` instead of passing parameters to constructor
2. **XPath Auto-Detection**: System auto-detects XPath selectors even if marked as CSS
3. **Sector Data Normalization**: Fields like 'sector', 'practice' always return arrays for consistency
4. **Education/Credential Selectors**: Use nth-child selectors to avoid duplicate data extraction
5. **Browser Injection**: JavaScript modules use global `window.ScraperModules` for dependencies
6. **Refactored Components**: Use the new modular architecture components, not the old monolithic scrapling_runner.py

### Template Structure
Templates are JSON files with:
- `elements`: Array of selectors (can be containers with sub_elements)
- `actions`: Navigation actions (clicks, scrolls)
- `pagination`: Configuration for handling multiple pages
- `cookies`: Captured session cookies for authentication

### Error Handling Strategy
1. Multiple fallback strategies for element selection
2. Smart XPath generation based on element labels
3. Graceful degradation when elements not found
4. Detailed logging at each extraction step
5. Modular error handling in specialized components

## 🚀 Performance Benefits (v2.0 Refactored)
- **97% Complexity Reduction**: From 5,213-line monolith to focused modules
- **10x Faster Development**: Easier to understand, test, and extend
- **Enhanced Reliability**: Better error handling and fallback strategies
- **Improved Performance**: Better resource management and lazy loading
- **Future-Proof**: Modular design allows easy feature additions

## 📊 Enhanced Container Workflow

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

## 🔄 File Organization & Data Flow
- **Entry Point**: `src/core/main.py` - CLI interface and InteractiveSession management
- **Browser Integration**: `src/interactive/index.js` - **Modular browser overlay system**
- **Automated Execution**: `src/core/scrapling_runner_refactored.py` - ScraplingRunner class for template execution
- **Data Models**: `src/models/scraping_template.py` - Pydantic models (ScrapingTemplate, ElementSelector, SubElement)
- **Templates**: JSON files in `templates/` directory - User-generated configurations
- **Output**: `output/` directory - Scraped data in JSON/CSV/Excel formats
- **Logs**: `scraper.log` and `logs/` directory for debugging information

### Core Data Flow
1. **Interactive Session** → Visual element selection → Template JSON generation
2. **Template Validation** → Pydantic models ensure data integrity  
3. **ScraplingRunner** → Loads template → Executes scraping → Exports results
4. **Output Processing** → JSON/CSV/Excel files with structured data

## 🎯 Development Guidelines for Future Work

### Architecture Principles
1. **Maintain Modularity**: Continue using single-responsibility components
2. **Composition Over Inheritance**: Use dependency injection and composition
3. **Interface Segregation**: Keep interfaces small and focused
4. **Open/Closed Principle**: Open for extension, closed for modification

### Code Quality Standards
1. **Type Hints**: All new code must include comprehensive type hints
2. **Documentation**: Detailed docstrings for all public methods
3. **Testing**: Minimum 90% test coverage for new features
4. **Performance**: No performance regressions in core functionality

### Adding New Features
1. **Interactive Features**: Extend existing tool classes or create new ones in `tools/`
2. **UI Components**: Add new UI modules in `ui/` directory
3. **Scraping Logic**: Extend the modular components in their respective directories
4. **Data Models**: Update `scraping_template.py` for new template fields
5. **CLI Commands**: Add to `main.py` and `cli.py` for new command-line options

## 🧪 Testing Strategy & Debugging
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

## 🎨 Best Practices

1. **Container-First Thinking**: Always look for repeating patterns first
2. **Semantic Labeling**: Use descriptive names that explain the data
3. **Robust Selectors**: Prefer class-based selectors over position-based
4. **Error Handling**: Implement fallback strategies for dynamic content
5. **Performance**: Add appropriate delays and respect rate limits

## 📚 Common Use Cases & Patterns

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

## ⚠️ Important Notes

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

## 🔧 Troubleshooting Common Issues

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

---

## 🏆 Summary

The Interactive Web Scraper v2.0 features a robust, modular architecture that transforms complex web scraping into a simple point-and-click workflow while maintaining production-grade reliability and performance. The system excels at extracting structured data from repeating patterns and adapts automatically to website changes.

**Always use the refactored modular architecture components and follow the established patterns for maximum reliability and maintainability.**