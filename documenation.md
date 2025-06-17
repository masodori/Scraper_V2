# 📚 Comprehensive Code Documentation

## 🏗️ Architecture Overview

The Interactive Web Scraper v2.0 is built with a **two-phase architecture**:

1. **Interactive Phase**: Visual template creation using Playwright browser with JavaScript overlay
2. **Automated Phase**: Template execution using Scrapling engine with refactored modular components

---

## 🔧 Core Components Deep Dive

### 1. **Entry Point & Session Management**

#### `src/core/main.py` - Interactive Session Orchestrator

**Purpose**: Manages the Playwright browser session for interactive template creation.

**Key Classes & Functions**:

##### `InteractiveSession` Class
```python
class InteractiveSession:
    """
    Manages Playwright browser session for template creation.
    Handles browser lifecycle, JavaScript injection, and callback management.
    """
```

**Core Responsibilities**:
- Browser initialization and configuration
- JavaScript overlay injection
- Cookie consent handling (automatic detection and clicking)
- Session state management
- Template data collection via callbacks

**Cookie Handler Location & Functionality**:
```python
def _handle_cookie_consent(self) -> None:
    """
    LOCATION: src/core/main.py, lines ~180-210
    
    FUNCTIONALITY:
    - Automatically detects common cookie consent dialogs
    - Uses predefined selectors for "Accept" buttons
    - Clicks consent buttons when found and visible
    - Waits for page stabilization after consent
    
    SELECTORS USED:
    - 'button:has-text("Accept")'
    - 'button:has-text("Accept All")'
    - '[id*="accept"][type="button"]'
    - '.cookie-accept', '#cookie-accept'
    - '.gdpr-accept', '#gdpr-accept'
    """
```

**Cookie Extraction Process**:
```python
def _extract_cookies(self) -> list:
    """
    LOCATION: src/core/main.py, lines ~220-240
    
    PROCESS:
    1. Accesses browser context cookies
    2. Extracts: name, value, domain, path, secure, httpOnly, sameSite
    3. Formats for template storage
    4. Returns list of CookieData objects
    
    PURPOSE: Store session cookies for automated scraping
    """
```

**Browser Session Management**:
```python
def start_session(self, url: str, template_path: str, headless: bool = False):
    """
    LOCATION: src/core/main.py, lines ~120-200
    
    SESSION LIFECYCLE:
    1. Initialize Playwright browser (Chromium)
    2. Create browser context with stealth settings
    3. Navigate to target URL
    4. Auto-handle cookie consent
    5. Inject JavaScript overlay
    6. Expose Python callbacks to JavaScript
    7. Monitor for navigation and template updates
    8. Clean up browser resources
    """
```

**JavaScript Callback Bridge**:
```python
# These callbacks bridge JavaScript events to Python:
def _save_template_callback(self, template_json: str) -> None:
    """Receives complete template from JavaScript"""

def _add_element_callback(self, element_data: str) -> None:
    """Receives new element selections"""

def _add_action_callback(self, action_data: str) -> None:
    """Receives user-defined actions"""

def _navigate_to_callback(self, url: str) -> None:
    """Handles navigation requests from JavaScript"""
```

---

### 2. **Refactored Modular Architecture (v2.0)**

#### `src/core/scrapling_runner_refactored.py` - Main Orchestrator

**Purpose**: Coordinates all scraping components using composition pattern.

**Architecture Transformation**:
- **Before**: 5,213-line monolithic file with 102 methods
- **After**: 300-line orchestrator + 8 specialized modules

**Component Initialization**:
```python
def __init__(self, template: ScrapingTemplate):
    """
    INITIALIZATION SEQUENCE:
    1. Create ScrapingContext (shared state)
    2. Initialize TemplateAnalyzer (pattern detection)
    3. Initialize SelectorEngine (selector enhancement)
    4. Defer data-dependent components until page is fetched:
       - DataExtractor
       - PaginationHandler  
       - SubpageProcessor
    """
```

**Execution Flow**:
```python
def run(self) -> Optional[ScrapingResult]:
    """
    EXECUTION PHASES:
    1. Template Analysis & Fixing
    2. Browser/Fetcher Initialization  
    3. Component Wiring
    4. Auto-Detection (directory, pagination)
    5. Data Extraction Strategy Selection
    6. Execution with Progress Tracking
    7. Data Export & Cleanup
    """
```

#### `src/core/context.py` - Shared State Management

**Purpose**: Centralized state container for all components.

```python
class ScrapingContext:
    """
    SHARED STATE CONTAINER:
    - template: ScrapingTemplate instance
    - fetcher: Browser fetcher instance
    - logger: Component-specific logger
    - metadata: Runtime metadata storage
    
    BENEFITS:
    - Single source of truth
    - Loose coupling between components
    - Easy testing with mock contexts
    """
```

#### `src/core/utils/progress.py` - Progress Tracking

**Purpose**: Real-time progress bars and ETA calculations.

**Features**:
```python
class ProgressTracker:
    """
    PROGRESS VISUALIZATION:
    - Terminal progress bars with colors
    - ETA calculations based on processing speed
    - Status updates for different phases
    - Memory usage monitoring
    
    USAGE:
    progress = ProgressTracker(context)
    with progress.track("Processing pages", total=100) as bar:
        for item in items:
            # Process item
            bar.update(1)
    """
```

#### `src/core/analyzers/template_analyzer.py` - Pattern Detection

**Purpose**: Intelligent analysis of template patterns and website structure.

**Core Functions**:
```python
class TemplateAnalyzer:
    def is_directory_template(self) -> bool:
        """
        DETECTION LOGIC:
        1. URL pattern analysis (/people/, /products/, /listings/)
        2. Container element presence
        3. Multiple sub-element patterns
        4. Pagination indicators
        
        RETURNS: True if template targets a directory/listing page
        """
    
    def requires_subpage_processing(self) -> bool:
        """
        ANALYSIS:
        1. Profile link patterns in containers
        2. "follow_links" flags in elements
        3. Subpage element definitions
        
        RETURNS: True if template needs individual page processing
        """
    
    def _find_container_patterns(self) -> List[Dict]:
        """
        PATTERN DETECTION:
        1. Identifies repeating element structures
        2. Analyzes sub-element relationships
        3. Determines optimal extraction strategy
        """
```

#### `src/core/selectors/selector_engine.py` - Smart Selector Enhancement

**Purpose**: Enhances basic selectors with robust, adaptive alternatives.

**Enhancement Process**:
```python
class SelectorEngine:
    def enhance_selectors(self, elements: List[ElementSelector]) -> List[ElementSelector]:
        """
        ENHANCEMENT PIPELINE:
        1. Analyze existing selectors for robustness
        2. Generate semantic alternatives
        3. Create XPath fallbacks
        4. Add AutoMatch compatibility
        5. Optimize for Scrapling engine
        
        EXAMPLE ENHANCEMENT:
        Input:  ".card:nth-child(1)"
        Output: [".profile-card", "//div[contains(@class, 'card')]"]
        """
    
    def _generate_semantic_selector(self, selector: str) -> str:
        """
        SEMANTIC MAPPING:
        - Generic classes → Semantic classes
        - Position-based → Content-based
        - Fragile selectors → Robust alternatives
        """
```

#### `src/core/extractors/data_extractor.py` - Multi-Strategy Extraction

**Purpose**: Robust data extraction with multiple fallback strategies.

**Extraction Strategies**:
```python
class DataExtractor:
    def extract_data(self) -> Dict[str, Any]:
        """
        EXTRACTION PIPELINE:
        1. Primary CSS selector attempt
        2. XPath fallback if CSS fails
        3. AutoMatch similarity search
        4. Text-based searching as last resort
        5. Graceful degradation with partial results
        """
    
    def _find_elements_css(self, page, selector: str) -> List:
        """CSS selector strategy with error handling"""
    
    def _find_elements_xpath(self, page, selector: str) -> List:
        """XPath selector strategy with robust generation"""
    
    def _find_elements_automatch(self, page, selector: str) -> List:
        """Scrapling AutoMatch for adaptive selection"""
    
    def _process_containers(self, page, container_element: ElementSelector) -> List[Dict]:
        """
        CONTAINER PROCESSING:
        1. Find all container instances
        2. Extract sub-elements from each container
        3. Maintain data relationships
        4. Handle dynamic loading
        """
```

**Container Processing Deep Dive**:
```python
def _extract_container_data(self, container, sub_elements: List[SubElement]) -> Dict:
    """
    CONTAINER DATA EXTRACTION:
    1. Iterate through each sub-element definition
    2. Apply relative selectors within container scope
    3. Extract different data types (text, links, attributes)
    4. Validate required elements
    5. Return structured data dictionary
    
    EXAMPLE:
    Container: .profile-card
    Sub-elements:
      - name: h3 → "John Doe"
      - title: .title → "Senior Partner"
      - email: a[href*="mailto"] → "john@firm.com"
    Result: {"name": "John Doe", "title": "Senior Partner", "email": "john@firm.com"}
    """
```

#### `src/core/handlers/pagination_handler.py` - Pagination Logic

**Purpose**: Handles all types of pagination patterns intelligently.

**Pagination Types Supported**:
```python
class PaginationHandler:
    def handle_pagination(self) -> Dict[str, Any]:
        """
        PAGINATION DETECTION & HANDLING:
        1. Infinite scroll detection
        2. Load-more button identification
        3. URL-based pagination analysis
        4. WordPress Grid Builder support
        5. JavaScript-driven pagination
        """
    
    def auto_scroll_to_load_all_content(self) -> None:
        """
        INFINITE SCROLL ALGORITHM:
        1. Detect current content count
        2. Scroll down gradually
        3. Wait for new content to load
        4. Compare content count
        5. Repeat until no new content
        6. Show progress with updates
        """
    
    def _try_load_more_pagination(self) -> Dict[str, Any]:
        """
        LOAD-MORE STRATEGY:
        1. Find load-more buttons
        2. Click and wait for content
        3. Track loaded items
        4. Prevent infinite loops
        5. Extract accumulated data
        """
    
    def _try_url_based_pagination(self) -> Dict[str, Any]:
        """
        URL PAGINATION:
        1. Analyze URL patterns
        2. Detect pagination parameters
        3. Generate page URLs
        4. Fetch each page sequentially
        5. Merge results
        """
```

**Dual Browser Strategy**:
```python
def _use_dual_browser_strategy(self) -> Dict[str, Any]:
    """
    ADVANCED PAGINATION:
    - Engine 1: Handles main page navigation
    - Engine 2: Processes individual subpages
    - Async queue for efficient processing
    - Session isolation between engines
    """
```

#### `src/core/processors/subpage_processor.py` - Individual Page Processing

**Purpose**: Navigates to individual pages and extracts detailed data.

**Processing Pipeline**:
```python
class SubpageProcessor:
    def process_subpages(self, profile_links: List[str]) -> Dict[str, Any]:
        """
        SUBPAGE PROCESSING:
        1. Queue profile links for processing
        2. Navigate to each individual page
        3. Extract detailed data using subpage selectors
        4. Merge with main page data
        5. Handle navigation errors gracefully
        6. Maintain progress tracking
        """
    
    def _process_single_subpage(self, url: str) -> Dict[str, Any]:
        """
        SINGLE PAGE PROCESSING:
        1. Navigate to individual URL
        2. Wait for page load completion
        3. Apply subpage element selectors
        4. Extract biographical/detailed data
        5. Return structured data
        """
    
    def _merge_subpage_data(self, main_data: Dict, subpage_data: Dict) -> Dict:
        """
        DATA MERGING:
        1. Match main page entries with subpage data
        2. Combine based on profile identifiers
        3. Handle missing subpage data
        4. Maintain data consistency
        """
```

---

### 3. **Data Models & Validation**

#### `src/models/scraping_template.py` - Pydantic Models

**Purpose**: Type-safe data models with validation for all template components.

**Core Models**:

##### `ElementSelector` - Individual Element Definition
```python
class ElementSelector(BaseModel):
    """
    ELEMENT DEFINITION:
    - label: User-friendly name
    - selector: CSS/XPath selector
    - selector_type: "css" or "xpath"
    - element_type: "text", "attribute", "html", "link", "container"
    - is_multiple: Boolean for multiple elements
    - is_required: Boolean for validation
    
    CONTAINER SUPPORT:
    - is_container: Boolean flag
    - sub_elements: List[SubElement] for nested extraction
    - use_find_similar: Scrapling AutoMatch integration
    
    SUBPAGE SUPPORT:
    - follow_links: Boolean to enable link following
    - subpage_elements: List[ElementSelector] for detail pages
    """
```

##### `SubElement` - Container Sub-Element
```python
class SubElement(BaseModel):
    """
    SUB-ELEMENT WITHIN CONTAINERS:
    - label: Data field name
    - selector: Relative selector within container
    - element_type: Type of data to extract
    - attribute_name: For attribute extraction
    - is_required: Validation flag
    
    USAGE:
    Container: .profile-card
    SubElement: {label: "name", selector: "h3", element_type: "text"}
    """
```

##### `CookieData` - Session Cookie Storage
```python
class CookieData(BaseModel):
    """
    COOKIE STORAGE MODEL:
    - name: Cookie name
    - value: Cookie value
    - domain: Cookie domain (.example.com)
    - path: Cookie path (default: "/")
    - secure: HTTPS-only flag
    - httpOnly: JavaScript access flag
    - sameSite: CSRF protection setting
    
    PURPOSE: Store authentication/session cookies for automated scraping
    """
```

##### `NavigationAction` - User Actions
```python
class NavigationAction(BaseModel):
    """
    USER ACTION DEFINITION:
    - label: Action description
    - selector: Element to interact with
    - action_type: "click", "scroll", "type", "wait"
    - value: Text to type (for type actions)
    - wait_after: Delay after action
    
    EXAMPLE ACTIONS:
    - Click load-more button
    - Scroll to trigger infinite scroll
    - Type in search box
    - Wait for dynamic content
    """
```

##### `ScrapingTemplate` - Complete Template Definition
```python
class ScrapingTemplate(BaseModel):
    """
    COMPLETE TEMPLATE STRUCTURE:
    
    METADATA:
    - name: Template identifier
    - description: Human-readable description
    - version: Template version
    - created_at: Timestamp
    
    TARGET:
    - url: Target website URL
    - user_agent: Custom user agent
    
    BROWSER CONFIG:
    - headless: Headless mode flag
    - wait_timeout: Element wait timeout
    - page_load_timeout: Page load timeout
    
    SESSION:
    - cookies: List[CookieData] for authentication
    
    EXTRACTION:
    - elements: List[ElementSelector] for data extraction
    - actions: List[NavigationAction] for interactions
    
    ADVANCED:
    - pagination: PaginationPattern configuration
    - enable_subpage_scraping: Boolean flag
    - subpage_url_pattern: Regex for valid subpages
    - stealth_mode: Anti-detection settings
    """
```

**Validation Features**:
```python
@field_validator('url')
@classmethod
def validate_url(cls, v):
    """URL format validation using urlparse"""

@field_validator('selector_type')
@classmethod
def validate_selector_type(cls, v):
    """Ensures selector_type is 'css' or 'xpath'"""

@field_validator('element_type')
@classmethod
def validate_element_type(cls, v):
    """Validates element_type against allowed values"""
```

**File Operations**:
```python
def save_to_file(self, filepath: str) -> None:
    """Save template to JSON file with validation"""

@classmethod
def load_from_file(cls, filepath: str) -> 'ScrapingTemplate':
    """Load and validate template from JSON file"""

def to_json(self, indent: int = 2) -> str:
    """Export to JSON string with formatting"""
```

---

### 4. **Interactive JavaScript System**

#### `src/interactive/index.js` - Modular Overlay System

**Purpose**: Browser-based visual element selection interface.

**Modular Architecture**:
```javascript
// GLOBAL NAMESPACE
window.ScraperModules = {
    Config: {...},          // Configuration constants
    StateManager: {...},    // Centralized state management
    EventManager: {...},    // Event delegation
    ErrorHandler: {...},    // Error handling utilities
    NavigationState: {...}, // Session persistence
    ModalManager: {...},    // Dialog system
    Tools: {                // Interactive selection tools
        ElementTool: {...},
        ActionTool: {...},
        ContainerTool: {...},
        ScrollTool: {...}
    },
    UI: {                   // User interface components
        ControlPanel: {...},
        StatusManager: {...},
        Styles: {...}
    },
    Utils: {                // Utility functions
        DOMUtils: {...},
        SelectorGenerator: {...},
        TemplateBuilder: {...},
        PythonBridge: {...}
    }
};
```

**State Management**:
```javascript
const StateManager = {
    /**
     * CENTRALIZED STATE:
     * - selectedElements: Array of selected elements
     * - containers: Array of container definitions  
     * - actions: Array of user actions
     * - currentTool: Active tool name
     * - currentContainer: Active container context
     */
    
    setState: function(updates) {
        // Update state and notify subscribers
    },
    
    addElement: function(element) {
        // Add new element to selection
    },
    
    addContainer: function(container) {
        // Add container with sub-elements
    }
};
```

**Tool System**:
```javascript
// ELEMENT TOOL - Individual element selection
const ElementTool = {
    activate: function() {
        // Enable element selection mode
        // Add click handlers to all elements
        // Show selection indicators
    },
    
    selectElement: function(element) {
        // Capture element data
        // Generate CSS selector
        // Add to state
        // Update UI
    }
};

// CONTAINER TOOL - Repeating pattern selection
const ContainerTool = {
    activate: function() {
        // Enable container selection mode
        // Highlight similar elements
    },
    
    selectContainer: function(element) {
        // Find similar elements using DOM traversal
        // Create container definition
        // Enable sub-element selection
        // Update UI with container context
    },
    
    selectSubElement: function(element, container) {
        // Add sub-element to container
        // Generate relative selector
        // Update container definition
    }
};
```

**Selector Generation**:
```javascript
const SelectorGenerator = {
    generateSelector: function(element) {
        /**
         * SELECTOR GENERATION ALGORITHM:
         * 1. Try ID selector (most specific)
         * 2. Try unique class combinations
         * 3. Use semantic classes over generic ones
         * 4. Fall back to structural selectors
         * 5. Generate XPath as backup
         * 6. Optimize for Scrapling AutoMatch
         */
    },
    
    generateRelativeSelector: function(element, container) {
        /**
         * RELATIVE SELECTOR FOR SUB-ELEMENTS:
         * 1. Find path from container to element
         * 2. Generate minimal selector
         * 3. Prefer semantic classes
         * 4. Test selector reliability
         */
    }
};
```

**Template Building**:
```javascript
const TemplateBuilder = {
    buildTemplate: function(state) {
        /**
         * TEMPLATE CONSTRUCTION:
         * 1. Collect all selected elements
         * 2. Format container structures
         * 3. Include user actions
         * 4. Add metadata and configuration
         * 5. Validate structure
         * 6. Return JSON template
         */
    },
    
    formatContainerElements: function(containers) {
        /**
         * CONTAINER FORMATTING:
         * 1. Convert DOM containers to JSON
         * 2. Include sub-element selectors
         * 3. Set container flags
         * 4. Optimize for bulk extraction
         */
    }
};
```

**Python Bridge**:
```javascript
const PythonBridge = {
    saveTemplate: function(templateData) {
        // Call Python callback to save template
        window.save_template_py(JSON.stringify(templateData));
    },
    
    addElement: function(elementData) {
        // Send element to Python backend
        window.add_element_py(JSON.stringify(elementData));
    },
    
    logMessage: function(message) {
        // Send log message to Python
        window.log_message_py(message);
    }
};
```

---

### 5. **Browser Integration & Session Management**

#### Session Lifecycle Management

**Browser Initialization**:
```python
def _initialize_browser(self) -> None:
    """
    BROWSER SETUP:
    1. Launch Chromium with stealth settings
    2. Configure viewport and user agent
    3. Set anti-detection headers
    4. Enable JavaScript execution
    5. Set appropriate timeouts
    """
```

**Context Management**:
```python
def _create_browser_context(self) -> BrowserContext:
    """
    CONTEXT CONFIGURATION:
    1. Set user agent and headers
    2. Configure cookie handling
    3. Enable stealth mode
    4. Set permission policies
    5. Configure request interception
    """
```

**Cookie Session Handling**:
```python
def _set_cookies(self, cookies: List[CookieData]) -> None:
    """
    COOKIE MANAGEMENT:
    1. Convert CookieData models to browser format
    2. Set cookies in browser context
    3. Handle domain and path restrictions
    4. Validate cookie security settings
    5. Log cookie application status
    """
```

**Navigation Management**:
```python
def _handle_navigation(self, url: str) -> None:
    """
    NAVIGATION HANDLING:
    1. Validate URL format
    2. Handle redirects
    3. Wait for network idle
    4. Handle loading errors
    5. Update session state
    """
```

---

### 6. **Data Export & Processing**

#### Export System

**Multi-Format Export**:
```python
def export_data(self, data: Dict[str, Any], format: str, output_path: str = None) -> str:
    """
    EXPORT PIPELINE:
    1. Validate data structure
    2. Apply format-specific transformations
    3. Handle nested data flattening
    4. Generate timestamps and metadata
    5. Write to file system
    6. Return output path
    """

def _export_json(self, data: Dict, output_path: str) -> str:
    """JSON export with pretty formatting and metadata"""

def _export_csv(self, data: Dict, output_path: str) -> str:
    """CSV export with data flattening and relationship preservation"""

def _export_excel(self, data: Dict, output_path: str) -> str:
    """Excel export with multiple sheets and formatting"""
```

**Data Flattening**:
```python
def _flatten_data_for_export(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    FLATTENING ALGORITHM:
    1. Handle list data by indexing or combining
    2. Flatten nested dictionaries with prefixed keys
    3. Preserve data relationships
    4. Handle missing values gracefully
    5. Maintain type information
    
    EXAMPLE:
    Input:  {"profiles": [{"name": "John", "contact": {"email": "john@example.com"}}]}
    Output: {"profiles_1_name": "John", "profiles_1_contact_email": "john@example.com"}
    """
```

---

### 7. **Error Handling & Logging**

#### Logging System

**Hierarchical Logging**:
```python
# Component-specific loggers
logger = logging.getLogger(__name__)
session_logger = logging.getLogger(f"scrapling_runner.{template.name}")

# Log levels and formatting
def _configure_logging(self) -> None:
    """
    LOGGING CONFIGURATION:
    1. Set log levels for different components
    2. Configure formatters with timestamps
    3. Set up file and console handlers
    4. Suppress third-party library warnings
    5. Create session-specific log files
    """
```

**Error Recovery**:
```python
def _handle_extraction_error(self, error: Exception, element: ElementSelector) -> Any:
    """
    ERROR RECOVERY STRATEGY:
    1. Log error with context
    2. Try alternative selectors
    3. Use AutoMatch as fallback
    4. Return None for optional elements
    5. Raise for required elements
    """
```

---

### 8. **Performance & Memory Management**

#### Resource Management

**Memory Optimization**:
```python
def _cleanup(self) -> None:
    """
    RESOURCE CLEANUP:
    1. Close browser pages
    2. Dispose browser context
    3. Clear large data structures
    4. Reset component states
    5. Release file handles
    """

def __del__(self):
    """Destructor ensures cleanup on object destruction"""
```

**Progress Tracking**:
```python
class ProgressTracker:
    def track_memory_usage(self) -> Dict[str, float]:
        """
        MEMORY MONITORING:
        1. Track process memory usage
        2. Monitor browser memory consumption
        3. Calculate data structure sizes
        4. Warn about memory leaks
        5. Suggest optimization strategies
        """
```

---

### 9. **Testing Infrastructure**

#### Test Organization

**Model Tests** (`tests/test_models.py`):
```python
class TestElementSelector:
    """Tests for ElementSelector validation and functionality"""

class TestCookieData:
    """Tests for cookie data handling"""

class TestScrapingTemplate:
    """Tests for complete template validation"""
```

**Integration Tests** (`tests/test_scrapling_runner.py`):
```python
class TestScraplingRunner:
    """Tests for end-to-end scraping functionality"""

class TestBrowserIntegration:
    """Tests for browser session management"""
```

---

### 10. **Configuration & CLI System**

#### Command Line Interface

**Unified CLI** (Needs Implementation):
```python
class UnifiedCLI:
    """
    PLANNED CLI UNIFICATION:
    1. Merge cli.py and interactive_cli.py
    2. Update imports for refactored components
    3. Add enhanced features using modular architecture
    4. Implement component health checks
    5. Provide real-time progress feedback
    """
```

**Configuration Management**:
```python
def _load_config(self) -> Dict[str, Any]:
    """
    CONFIGURATION LOADING:
    1. Load from ~/.scraper_config.json
    2. Provide sensible defaults
    3. Validate configuration values
    4. Handle missing or corrupted config
    5. Support environment variable overrides
    """
```

---

## 🔄 Data Flow Summary

### Complete Data Flow Pipeline

1. **Interactive Phase**:
   ```
   User Opens Browser → Selects Elements → JavaScript Captures → Python Receives → Template Validation → JSON Storage
   ```

2. **Automated Phase**:
   ```
   Template Loading → Component Initialization → Browser Launch → Data Extraction → Processing → Export
   ```

3. **Component Interaction**:
   ```
   ScraplingRunner ↔ Context ↔ {TemplateAnalyzer, SelectorEngine, DataExtractor, PaginationHandler, SubpageProcessor}
   ```

### Cookie Handling Flow

```
Page Load → Auto-Detect Consent → Click Accept → Extract All Cookies → Store in Template → Apply in Automated Phase
```

### Error Handling Flow

```
Primary Selector → CSS Fallback → XPath Fallback → AutoMatch → Text Search → Graceful Degradation
```

---

## 📊 Performance Characteristics

### Memory Usage Optimization

- **Lazy Loading**: Components initialized only when needed
- **Resource Cleanup**: Automatic browser and memory cleanup
- **Data Streaming**: Process large datasets incrementally
- **Memory Monitoring**: Track usage and warn about leaks

### Execution Speed

- **Browser Reuse**: Single browser session for all operations
- **Parallel Processing**: Async subpage processing
- **Smart Caching**: Selector and pattern caching
- **Optimized Selectors**: Generated for maximum speed

---

This documentation provides comprehensive coverage of every major component, process, and data flow in the Interactive Web Scraper v2.0. Each section includes location details, functionality explanations, and code examples for deep understanding of the system architecture.
