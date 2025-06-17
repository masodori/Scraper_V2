# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL RULES (ALWAYS FOLLOW)

### Memory RULES: Web Scraping Best Practices

1. **NEVER edit any templates or outputs** - Templates are user-generated and should not be modified
2. **ALWAYS make backup files before making edits** - Preserve original code before modifications
3. **NEVER hard code or make something code-wise that is for a specific webpage** - Keep code generic and reusable
4. **When a file size is greater than the token limit (over 600 lines of code), read the entire file by quarters** - Handle large files systematically
5. **Use the new refactored directory structure** - Work with the modular architecture components, not the old monolithic files

## Key Commands

### Development Commands
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

## High-Level Architecture

### Two-Phase System
The scraper operates in two distinct phases:
1. **Interactive Phase**: Visual template creation through browser overlay
2. **Automated Phase**: Template execution with Scrapling engine

### Core Integration Points
- **Playwright**: Powers the interactive browser session for template creation
- **Scrapling**: High-performance scraping engine for automated execution
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

### Critical Component Interactions

#### Template Flow
1. `src/core/main.py` → Launches Playwright browser with interactive overlay
2. `src/interactive/index.js` → Injects JavaScript tools into the page
3. User clicks elements → JavaScript generates selectors and structure
4. `src/interactive/utils/template-builder.js` → Creates JSON template
5. `src/models/scraping_template.py` → Validates template structure
6. `src/core/scrapling_runner_refactored.py` → Executes template with Scrapling

#### Modular Interactive System
The JavaScript overlay is modular with clear separation:
- **Tools** (`tools/`): Each tool (Element, Container, Action, Scroll) is independent
- **UI** (`ui/`): Modal system, control panel, status manager
- **Core** (`core/`): State management, event handling, error handling
- **Utils** (`utils/`): DOM utilities, Python bridge, template builder

#### Browser Session Management
- `ScraplingRunner` maintains a single browser instance (`self.fetcher_instance`)
- Reuses browser session for all page navigations (critical for performance)
- Proper cleanup in `_cleanup()` method and destructor

### Key Architectural Decisions

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

### Important Implementation Details

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

## Working with the Refactored Architecture

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

## Performance Benefits (v2.0 Refactored)
- **97% Complexity Reduction**: From 5,213-line monolith to focused modules
- **10x Faster Development**: Easier to understand, test, and extend
- **Enhanced Reliability**: Better error handling and fallback strategies
- **Improved Performance**: Better resource management and lazy loading
- **Future-Proof**: Modular design allows easy feature additions