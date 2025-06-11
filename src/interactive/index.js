/**
 * Interactive Web Scraper - Refactored Modular Entry Point
 * 
 * This is the refactored modular system using traditional JavaScript (no ES6 imports)
 * while maintaining the same functionality as the backup file.
 * All modules are bundled into this single file for Playwright injection compatibility.
 */

(function() {
    'use strict';
    
    console.log("🕷️ Interactive Scraper overlay injected successfully");
    
    // Check if overlay already exists to prevent duplicate initialization
    if (window.ScraperState && document.querySelector('.scraper-control-panel')) {
        console.log("🔄 Scraper overlay already exists, skipping initialization");
        return;
    }
    
    // Configuration constants
    const CONFIG = {
        MODAL_Z_INDEX: 999999999,
        SELECTION_TIMEOUT: 5 * 60 * 1000,
        SELECTORS: {
            CONTROL_PANEL: '.scraper-control-panel',
            HIGHLIGHT: 'scraper-highlight'
        },
        MESSAGES: {
            NO_LABEL: 'Please provide a label for this element',
            DUPLICATE_LABEL: 'An element with this label already exists'
        }
    };
    
    // Global state management
    window.ScraperState = window.ScraperState || {
        isSelectionMode: false,
        selectedElements: [],
        containers: [],
        actions: [],
        currentTool: 'element', // 'element', 'action', 'scroll', or 'container'
        scrollConfig: null,
        currentContainer: null,
        currentContainerElements: [],
        pageNavigationState: null,
        highlightedElement: null,
        overlay: null,
        controlPanel: null,
        selectorMode: 'css' // 'css' or 'xpath'
    };
    
    const ScraperState = window.ScraperState;
    
    // =============================================================================
    // ERROR HANDLER MODULE
    // =============================================================================
    
    const ErrorHandler = {
        handle: function(operation, fallback) {
            try {
                if (typeof operation === 'function') {
                    return operation();
                }
            } catch (error) {
                console.error('❌ Error:', error);
                if (typeof window.log_message_py === 'function') {
                    window.log_message_py(`Error: ${error.message}`);
                }
                if (typeof fallback === 'function') {
                    return fallback(error);
                }
            }
        },
        
        handleAsync: async function(operation, fallback) {
            try {
                if (typeof operation === 'function') {
                    return await operation();
                }
            } catch (error) {
                console.error('❌ Async Error:', error);
                if (typeof window.log_message_py === 'function') {
                    window.log_message_py(`Async Error: ${error.message}`);
                }
                if (typeof fallback === 'function') {
                    return await fallback(error);
                }
            }
        }
    };
    
    // =============================================================================
    // MODAL MANAGER MODULE
    // =============================================================================
    
    const ModalManager = {
        show: function(config) {
            return new Promise((resolve) => {
                const { type, title, message, buttons = [], input = null, content = null } = config;
                
                const modal = document.createElement('div');
                modal.className = 'scraper-modal';
                
                let inputHtml = '';
                if (input) {
                    inputHtml = `<input type="text" class="scraper-modal-input" placeholder="${input.placeholder || ''}" ${input.autofocus ? 'autofocus' : ''}>`;
                }
                
                let messageHtml = '';
                if (message) {
                    messageHtml = `<div class="scraper-modal-message">${message}</div>`;
                }
                
                let customContentHtml = '';
                if (content) {
                    customContentHtml = content;
                }
                
                const buttonsHtml = buttons.map((btn, index) => {
                    const isPrimary = btn.primary || index === buttons.length - 1;
                    const buttonClass = isPrimary ? 'scraper-modal-btn-primary' : 'scraper-modal-btn-secondary';
                    
                    // Handle both string and object button definitions
                    let buttonText, buttonAction;
                    if (typeof btn === 'string') {
                        buttonText = btn;
                        buttonAction = btn.toLowerCase();
                    } else {
                        buttonText = btn.text || btn;
                        buttonAction = btn.action || btn.text?.toLowerCase() || 'button';
                    }
                    
                    return `<button class="scraper-modal-btn ${buttonClass}" data-action="${buttonAction}">${buttonText}</button>`;
                }).join('');
                
                modal.innerHTML = `
                    <div class="scraper-modal-content">
                        <div class="scraper-modal-title">${title}</div>
                        ${messageHtml}
                        ${customContentHtml}
                        ${inputHtml}
                        <div class="scraper-modal-buttons">
                            ${buttonsHtml}
                        </div>
                    </div>
                `;
                
                document.body.appendChild(modal);
                
                const inputElement = modal.querySelector('.scraper-modal-input');
                const buttonElements = modal.querySelectorAll('.scraper-modal-btn');
                
                // Focus input if present
                if (inputElement && input && input.autofocus) {
                    setTimeout(() => {
                        inputElement.focus();
                        inputElement.select(); // Select all text for easier editing
                    }, 100);
                }
                
                const cleanup = () => {
                    if (modal.parentNode) {
                        modal.parentNode.removeChild(modal);
                    }
                };
                
                // Button handlers with explicit event handling
                buttonElements.forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        console.log('Modal button clicked:', btn.dataset.action);
                        
                        const action = btn.dataset.action;
                        let result = action;
                        
                        if (input && inputElement) {
                            result = {
                                action: action,
                                value: inputElement.value.trim()
                            };
                        }
                        
                        cleanup();
                        resolve(result);
                    }, true); // Use capture phase to ensure we get the event first
                });
                
                // Handle Enter key for input
                if (inputElement) {
                    inputElement.addEventListener('keypress', (e) => {
                        if (e.key === 'Enter') {
                            const primaryBtn = modal.querySelector('.scraper-modal-btn-primary');
                            if (primaryBtn) {
                                primaryBtn.click();
                            }
                        }
                    });
                }
                
                // Handle ESC key
                const handleEsc = (e) => {
                    if (e.key === 'Escape') {
                        cleanup();
                        resolve('cancel');
                        document.removeEventListener('keydown', handleEsc);
                    }
                };
                document.addEventListener('keydown', handleEsc);
            });
        },
        
        alert: function(message) {
            return this.show({
                title: 'Alert',
                message: message,
                buttons: ['OK']
            });
        },
        
        confirm: function(title, message) {
            return this.show({
                title: title,
                message: message,
                buttons: [
                    { text: 'Cancel', action: 'cancel', primary: false },
                    { text: 'OK', action: 'ok', primary: true }
                ]
            }).then(result => result === 'ok');
        },
        
        prompt: function(title, placeholder = '', element = null) {
            const config = {
                title: title,
                input: { placeholder: placeholder, autofocus: true },
                buttons: [
                    { text: 'Cancel', action: 'cancel', primary: false },
                    { text: 'OK', action: 'ok', primary: true }
                ]
            };
            
            // Add preview content if element is provided
            if (element) {
                const textContent = element.textContent ? element.textContent.trim() : '';
                const previewText = textContent.length > 100 ? 
                    textContent.substring(0, 100) + '...' : textContent;
                
                config.content = `
                    <div class="scraper-preview-section">
                        <strong>Element Preview:</strong>
                        <div class="scraper-preview-text">${previewText || 'No text content'}</div>
                        <div class="scraper-preview-info">
                            Tag: ${element.tagName.toLowerCase()}
                            ${element.className ? ` | Classes: ${element.className}` : ''}
                        </div>
                    </div>
                `;
            }
            
            return this.show(config).then(result => {
                if (result && result.action === 'ok') {
                    return result.value;
                }
                return null;
            });
        }
    };
    
    // =============================================================================
    // STATE MANAGER MODULE
    // =============================================================================
    
    const StateManager = {
        subscribers: [],
        
        subscribe: function(callback) {
            this.subscribers.push(callback);
        },
        
        unsubscribe: function(callback) {
            this.subscribers = this.subscribers.filter(sub => sub !== callback);
        },
        
        setState: function(updates) {
            const oldState = { ...ScraperState };
            Object.assign(ScraperState, updates);
            
            this.subscribers.forEach(callback => {
                try {
                    callback(ScraperState, oldState);
                } catch (error) {
                    console.error('State update error:', error);
                }
            });
        },
        
        getState: function() {
            return ScraperState;
        },
        
        addElement: function(element) {
            const elements = [...ScraperState.selectedElements, element];
            this.setState({ selectedElements: elements });
        },
        
        removeElement: function(index) {
            const elements = ScraperState.selectedElements.filter((_, i) => i !== index);
            this.setState({ selectedElements: elements });
        },
        
        clearElements: function() {
            this.setState({ selectedElements: [] });
        },
        
        addAction: function(action) {
            const actions = [...ScraperState.actions, action];
            this.setState({ actions: actions });
        },
        
        clearActions: function() {
            this.setState({ actions: [] });
        },
        
        addContainer: function(container) {
            const containers = [...ScraperState.containers, container];
            this.setState({ containers: containers });
        },
        
        clearContainers: function() {
            this.setState({ containers: [], currentContainer: null, currentContainerElements: [] });
        }
    };
    
    // =============================================================================
    // EVENT MANAGER MODULE
    // =============================================================================
    
    const EventManager = {
        handlers: new Map(),
        
        setupDelegation: function() {
            // Main document event delegation
            document.addEventListener('click', this.handleClick.bind(this), true);
            document.addEventListener('mouseover', this.handleMouseOver.bind(this), true);
            document.addEventListener('mouseout', this.handleMouseOut.bind(this), true);
        },
        
        handleClick: function(e) {
            // Check if click is inside modal - let modal handle its own events
            if (e.target.closest('.scraper-modal')) {
                return; // Don't interfere with modal events
            }
            
            // Check if click is inside control panel
            const controlPanel = document.querySelector('.scraper-control-panel');
            if (controlPanel && controlPanel.contains(e.target)) {
                // Handle UI clicks
                this.handleUIClick(e);
                return;
            }
            
            // Handle selection clicks
            if (ScraperState.isSelectionMode) {
                this.handleSelectionClick(e);
            }
        },
        
        handleUIClick: function(e) {
            const target = e.target;
            const buttonId = target.id || target.dataset.action;
            
            if (buttonId && this.handlers.has(buttonId)) {
                e.preventDefault();
                e.stopPropagation();
                const handler = this.handlers.get(buttonId);
                handler(e);
            }
        },
        
        handleSelectionClick: function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const element = e.target;
            
            // Skip if it's part of the scraper UI
            if (element.closest('.scraper-control-panel, .scraper-modal, .scraper-highlight-overlay')) {
                return;
            }
            
            // Check if we're in sub-element selection mode (container tool with existing container)
            const currentTool = ScraperState.currentTool;
            if (currentTool === 'container' && ScraperState.currentContainer) {
                // Check if the "Add Sub-Element" button was recently clicked
                const addSubElementBtn = document.getElementById('add-sub-element-btn');
                if (addSubElementBtn && addSubElementBtn.dataset.active === 'true') {
                    ContainerTool.handleSubElementSelection(element);
                    return;
                }
            }
            
            // Route to appropriate tool handler
            if (currentTool === 'element') {
                ElementTool.handleSelection(element);
            } else if (currentTool === 'action') {
                ActionTool.handleSelection(element);
            } else if (currentTool === 'container') {
                ContainerTool.handleSelection(element);
            }
        },
        
        handleMouseOver: function(e) {
            if (!ScraperState.isSelectionMode) return;
            
            const element = e.target;
            if (element.closest('.scraper-control-panel, .scraper-modal')) {
                return;
            }
            
            VisualManager.highlightElement(element);
        },
        
        handleMouseOut: function(e) {
            if (!ScraperState.isSelectionMode) return;
            VisualManager.removeHighlight();
        },
        
        attachHandler: function(id, handler) {
            this.handlers.set(id, handler);
        },
        
        attachMultipleHandlers: function(handlerMap) {
            Object.entries(handlerMap).forEach(([id, handler]) => {
                this.attachHandler(id, handler);
            });
        }
    };
    
    // =============================================================================
    // VISUAL MANAGER MODULE
    // =============================================================================
    
    const VisualManager = {
        overlays: [], // Track all overlays for scroll updates
        scrollHandler: null,
        
        highlightElement: function(element) {
            this.removeHighlight();
            
            if (!element || element === document.body || element === document.documentElement) {
                return;
            }
            
            ScraperState.highlightedElement = element;
            element.classList.add(CONFIG.SELECTORS.HIGHLIGHT);
        },
        
        removeHighlight: function() {
            if (ScraperState.highlightedElement) {
                ScraperState.highlightedElement.classList.remove(CONFIG.SELECTORS.HIGHLIGHT);
                ScraperState.highlightedElement = null;
            }
        },
        
        addElementVisual: function(element, label, index) {
            const overlay = this.createOverlay(element, label, index, 'element');
            this.overlays.push({
                overlay: overlay,
                element: element,
                type: 'element'
            });
            this.setupScrollHandling();
        },
        
        addActionVisual: function(element, label, index) {
            const overlay = this.createOverlay(element, label, index, 'action');
            this.overlays.push({
                overlay: overlay,
                element: element,
                type: 'action'
            });
            this.setupScrollHandling();
        },
        
        createOverlay: function(element, label, index, type) {
            const rect = element.getBoundingClientRect();
            const overlay = document.createElement('div');
            overlay.className = `scraper-${type}-overlay`;
            overlay.innerHTML = `<div class="scraper-${type}-label">${index + 1}. ${label}</div>`;
            
            const borderColor = type === 'element' ? '#4CAF50' : '#2196F3';
            overlay.style.cssText = `
                position: fixed;
                top: ${rect.top}px;
                left: ${rect.left}px;
                width: ${rect.width}px;
                height: ${rect.height}px;
                border: 2px solid ${borderColor};
                pointer-events: none;
                z-index: 999999;
            `;
            
            document.body.appendChild(overlay);
            element.classList.add('scraper-selected-element');
            
            return overlay;
        },
        
        setupScrollHandling: function() {
            if (this.scrollHandler) return; // Already set up
            
            this.scrollHandler = () => {
                this.updateOverlayPositions();
            };
            
            // Use passive listeners for better performance
            window.addEventListener('scroll', this.scrollHandler, { passive: true });
            window.addEventListener('resize', this.scrollHandler, { passive: true });
        },
        
        updateOverlayPositions: function() {
            this.overlays.forEach(overlayData => {
                if (!overlayData.element || !overlayData.overlay) return;
                
                // Check if element is still in DOM
                if (!document.contains(overlayData.element)) {
                    overlayData.overlay.remove();
                    return;
                }
                
                const rect = overlayData.element.getBoundingClientRect();
                const overlay = overlayData.overlay;
                
                overlay.style.top = `${rect.top}px`;
                overlay.style.left = `${rect.left}px`;
                overlay.style.width = `${rect.width}px`;
                overlay.style.height = `${rect.height}px`;
            });
            
            // Clean up removed overlays
            this.overlays = this.overlays.filter(overlayData => 
                document.contains(overlayData.overlay)
            );
        },
        
        clearAllVisuals: function() {
            // Remove all overlays
            document.querySelectorAll('.scraper-element-overlay, .scraper-action-overlay, .scraper-container-overlay').forEach(el => el.remove());
            document.querySelectorAll('.scraper-selected-element').forEach(el => el.classList.remove('scraper-selected-element'));
            
            // Clear overlay tracking
            this.overlays = [];
            
            // Remove scroll handler if no more overlays
            if (this.scrollHandler) {
                window.removeEventListener('scroll', this.scrollHandler);
                window.removeEventListener('resize', this.scrollHandler);
                this.scrollHandler = null;
            }
        },
        
        restoreVisuals: function() {
            // Restore element visuals
            ScraperState.selectedElements.forEach((elementData, index) => {
                try {
                    const element = document.querySelector(elementData.selector);
                    if (element) {
                        this.addElementVisual(element, elementData.label, index);
                    }
                } catch (error) {
                    console.warn(`Could not restore visual for element: ${elementData.label}`, error);
                }
            });
            
            // Restore action visuals
            ScraperState.actions.forEach((actionData, index) => {
                try {
                    const element = document.querySelector(actionData.selector);
                    if (element) {
                        this.addActionVisual(element, actionData.label, index);
                    }
                } catch (error) {
                    console.warn(`Could not restore visual for action: ${actionData.label}`, error);
                }
            });
        }
    };
    
    // =============================================================================
    // SELECTOR GENERATOR MODULE
    // =============================================================================
    
    const SelectorGenerator = {
        generate: function(element) {
            // Check current selector mode and route accordingly
            if (ScraperState.selectorMode === 'xpath') {
                return this.generateXPathSelector(element);
            } else {
                return this.generateCSSSelector(element);
            }
        },
        
        generateCSSSelector: function(element) {
            // Try multiple strategies in order of preference
            const strategies = [
                this.generateIdSelector,
                this.generateClassSelector,
                this.generateAttributeSelector,
                this.generateTextSelector,
                this.generateContextualSelector,
                this.generateNthChildSelector
            ];
            
            for (const strategy of strategies) {
                const selector = strategy.call(this, element);
                if (selector && this.validateSelector(selector, element)) {
                    return selector;
                }
            }
            
            // Enhanced fallback
            return this.generateEnhancedFallbackSelector(element);
        },
        
        generateXPathSelector: function(element) {
            // Generate XPath selector strategies
            const strategies = [
                this.generateXPathById,
                this.generateXPathByClass,
                this.generateXPathByText,
                this.generateXPathByPosition,
                this.generateXPathByAttributes
            ];
            
            for (const strategy of strategies) {
                const xpath = strategy.call(this, element);
                if (xpath && this.validateXPathSelector(xpath, element)) {
                    return `xpath:${xpath}`;
                }
            }
            
            // Fallback XPath
            return `xpath:${this.generateFallbackXPath(element)}`;
        },
        
        generateIdSelector: function(element) {
            if (element.id && /^[a-zA-Z][\w-]*$/.test(element.id)) {
                return `#${element.id}`;
            }
            return null;
        },
        
        generateClassSelector: function(element) {
            if (element.className && typeof element.className === 'string') {
                const classes = element.className.trim().split(/\s+/)
                    .filter(cls => cls && /^[a-zA-Z][\w-]*$/.test(cls))
                    .filter(cls => !this.isGenericClass(cls));
                
                if (classes.length > 0) {
                    // Try the most specific class combination first
                    const selector = `.${classes.join('.')}`;
                    if (this.getSelectorMatchCount(selector) < 10) {
                        return selector;
                    }
                    
                    // Try individual classes if combination is too broad
                    for (const cls of classes) {
                        const singleSelector = `.${cls}`;
                        if (this.getSelectorMatchCount(singleSelector) < 10) {
                            return singleSelector;
                        }
                    }
                }
            }
            return null;
        },
        
        generateAttributeSelector: function(element) {
            const attributes = ['data-testid', 'data-test', 'data-cy', 'aria-label', 'name', 'role', 'type'];
            
            for (const attr of attributes) {
                const value = element.getAttribute(attr);
                if (value) {
                    const selector = `[${attr}="${value}"]`;
                    if (this.getSelectorMatchCount(selector) < 10) {
                        return selector;
                    }
                }
            }
            return null;
        },
        
        generateTextSelector: function(element) {
            const text = element.textContent?.trim();
            if (text && text.length > 2 && text.length < 100 && !text.includes('"') && !text.includes('\n')) {
                const tagName = element.tagName.toLowerCase();
                if (['button', 'a', 'span', 'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
                    // Try XPath text-based selector for better specificity
                    return this.generateXPathTextSelector(element, text);
                }
            }
            return null;
        },
        
        generateXPathTextSelector: function(element, text) {
            const tagName = element.tagName.toLowerCase();
            
            // Generate XPath selectors for common patterns
            const xpathSelectors = [
                // Exact text match
                `//${tagName}[normalize-space(text())="${text}"]`,
                // Contains text (for partial matches)
                `//${tagName}[contains(normalize-space(text()), "${text}")]`,
                // Text with specific parent context
                `//*[@class]/${tagName}[normalize-space(text())="${text}"]`
            ];
            
            // Test each XPath selector for uniqueness
            for (const xpath of xpathSelectors) {
                try {
                    const results = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    if (results.snapshotLength === 1 && results.snapshotItem(0) === element) {
                        return `xpath:${xpath}`;
                    } else if (results.snapshotLength > 1 && results.snapshotLength < 5) {
                        // Multiple matches but still manageable
                        for (let i = 0; i < results.snapshotLength; i++) {
                            if (results.snapshotItem(i) === element) {
                                return `xpath:(${xpath})[${i + 1}]`;
                            }
                        }
                    }
                } catch (error) {
                    continue;
                }
            }
            
            // Fallback to content-based CSS approach
            return this.generateTextContainsSelector(element, text);
        },
        
        generateTextContainsSelector: function(element, text) {
            // Generate a selector that targets elements containing specific text
            const tagName = element.tagName.toLowerCase();
            const parent = element.parentElement;
            
            if (parent) {
                const parentSelector = this.generateParentContext(parent);
                if (parentSelector) {
                    return `${parentSelector} ${tagName}`;
                }
            }
            
            return null;
        },
        
        generateContextualSelector: function(element) {
            // Try XPath semantic selectors first for better targeting
            const xpathSelector = this.generateSemanticXPath(element);
            if (xpathSelector) {
                return xpathSelector;
            }
            
            // Generate selector based on parent context
            const parent = element.parentElement;
            if (!parent) return null;
            
            const parentSelector = this.generateParentContext(parent);
            if (parentSelector) {
                const tagName = element.tagName.toLowerCase();
                const selector = `${parentSelector} ${tagName}`;
                
                // Make it more specific if there are multiple matches
                const matchCount = this.getSelectorMatchCount(selector);
                if (matchCount === 1) {
                    return selector;
                } else if (matchCount > 1 && matchCount < 10) {
                    // Add position-based specificity
                    const siblings = Array.from(parent.children);
                    const index = siblings.indexOf(element);
                    if (index >= 0) {
                        return `${parentSelector} ${tagName}:nth-child(${index + 1})`;
                    }
                }
            }
            return null;
        },
        
        generateSemanticXPath: function(element) {
            // Generate semantic XPath selectors for common legal/professional patterns
            const text = element.textContent?.trim();
            const tagName = element.tagName.toLowerCase();
            
            if (!text) return null;
            
            // Patterns for lawyer/professional profiles
            const semanticPatterns = [
                // Email patterns
                {
                    test: () => text.includes('@') && text.includes('.'),
                    xpath: `//a[contains(@href, 'mailto:') and contains(text(), '${text}')]`
                },
                // Phone patterns
                {
                    test: () => /[\+\-\(\)\s\d]{10,}/.test(text) && /\d{3,}/.test(text),
                    xpath: `//*[contains(text(), '${text}') and (contains(text(), '+') or contains(text(), '(') or string-length(translate(text(), '0123456789', '')) < string-length(text()) - 6)]`
                },
                // Name patterns (capitalized text in specific contexts)
                {
                    test: () => /^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$/.test(text) && text.split(' ').length <= 4,
                    xpath: `//*[normalize-space(text())='${text}' and (parent::*[contains(@class, 'name')] or parent::*[contains(@class, 'title')] or self::h1 or self::h2 or self::strong)]`
                },
                // Job titles/positions
                {
                    test: () => ['partner', 'associate', 'counsel', 'attorney', 'lawyer', 'director'].some(title => text.toLowerCase().includes(title)),
                    xpath: `//*[contains(normalize-space(text()), '${text}') and (contains(@class, 'title') or contains(@class, 'position') or contains(@class, 'job'))]`
                },
                // Practice areas/sectors
                {
                    test: () => ['law', 'legal', 'practice', 'litigation', 'corporate', 'finance', 'tax', 'real estate'].some(area => text.toLowerCase().includes(area)),
                    xpath: `//*[contains(normalize-space(text()), '${text}') and (contains(@class, 'practice') or contains(@class, 'sector') or contains(@class, 'area'))]`
                },
                // Education patterns
                {
                    test: () => /university|college|school|j\.?d\.?|ll\.?m\.?|b\.?a\.?|b\.?s\.?|\d{4}/.test(text.toLowerCase()),
                    xpath: `//*[contains(normalize-space(text()), '${text}') and (ancestor::*[contains(@class, 'education')] or ancestor::*[contains(@class, 'credential')] or preceding-sibling::*[contains(text(), 'Education')])]`
                }
            ];
            
            for (const pattern of semanticPatterns) {
                if (pattern.test()) {
                    try {
                        const results = document.evaluate(pattern.xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                        if (results.snapshotLength > 0 && results.snapshotLength < 10) {
                            // Find the exact element
                            for (let i = 0; i < results.snapshotLength; i++) {
                                if (results.snapshotItem(i) === element) {
                                    return `xpath:${pattern.xpath}${results.snapshotLength > 1 ? `[${i + 1}]` : ''}`;
                                }
                            }
                        }
                    } catch (error) {
                        continue;
                    }
                }
            }
            
            return null;
        },
        
        generateParentContext: function(parent) {
            // Generate a selector for the parent element
            if (parent.id && /^[a-zA-Z][\w-]*$/.test(parent.id)) {
                return `#${parent.id}`;
            }
            
            if (parent.className && typeof parent.className === 'string') {
                const classes = parent.className.trim().split(/\s+/)
                    .filter(cls => cls && /^[a-zA-Z][\w-]*$/.test(cls))
                    .filter(cls => !this.isGenericClass(cls));
                
                if (classes.length > 0) {
                    const selector = `.${classes.join('.')}`;
                    if (this.getSelectorMatchCount(selector) < 5) {
                        return selector;
                    }
                }
            }
            
            // Check for semantic parent tags
            const semanticTags = ['article', 'section', 'header', 'footer', 'nav', 'main', 'aside'];
            if (semanticTags.includes(parent.tagName.toLowerCase())) {
                return parent.tagName.toLowerCase();
            }
            
            return null;
        },
        
        generateNthChildSelector: function(element) {
            const parent = element.parentElement;
            if (!parent) return null;
            
            const siblings = Array.from(parent.children);
            const index = siblings.indexOf(element);
            
            if (index >= 0) {
                const tagName = element.tagName.toLowerCase();
                const parentSelector = this.generateParentContext(parent);
                
                if (parentSelector) {
                    return `${parentSelector} ${tagName}:nth-child(${index + 1})`;
                } else {
                    // Only use nth-child if there are few matches
                    const selector = `${tagName}:nth-child(${index + 1})`;
                    if (this.getSelectorMatchCount(selector) < 5) {
                        return selector;
                    }
                }
            }
            return null;
        },
        
        generateEnhancedFallbackSelector: function(element) {
            // Enhanced fallback that considers context and uniqueness
            const tagName = element.tagName.toLowerCase();
            
            // Try to make tag-based selector more specific
            const parent = element.parentElement;
            if (parent) {
                const parentSelector = this.generateParentContext(parent);
                if (parentSelector) {
                    const contextSelector = `${parentSelector} ${tagName}`;
                    if (this.getSelectorMatchCount(contextSelector) < 20) {
                        return contextSelector;
                    }
                }
            }
            
            // Add attributes if available to make it more specific
            const attrs = [];
            if (element.className) {
                const classes = element.className.trim().split(/\s+/)
                    .filter(cls => cls && /^[a-zA-Z][\w-]*$/.test(cls))
                    .filter(cls => !this.isGenericClass(cls));
                if (classes.length > 0) {
                    attrs.push(`.${classes[0]}`);
                }
            }
            
            // Check for useful attributes
            const importantAttrs = ['type', 'role', 'name'];
            for (const attr of importantAttrs) {
                const value = element.getAttribute(attr);
                if (value) {
                    attrs.push(`[${attr}="${value}"]`);
                    break;
                }
            }
            
            if (attrs.length > 0) {
                const enhancedSelector = `${tagName}${attrs.join('')}`;
                if (this.getSelectorMatchCount(enhancedSelector) < 20) {
                    return enhancedSelector;
                }
            }
            
            // Last resort: just the tag name but warn about potential issues
            console.warn(`⚠️ Using generic selector "${tagName}" for element. This may match multiple elements.`);
            return tagName;
        },
        
        isGenericClass: function(className) {
            // Filter out overly generic class names that don't add specificity
            const genericClasses = [
                'container', 'wrapper', 'content', 'item', 'element', 'component',
                'block', 'section', 'row', 'col', 'column', 'box', 'card',
                'text', 'title', 'label', 'value', 'data', 'info',
                'left', 'right', 'center', 'top', 'bottom', 'middle',
                'first', 'last', 'active', 'selected', 'current',
                'small', 'large', 'medium', 'big', 'full', 'half'
            ];
            
            return genericClasses.includes(className.toLowerCase()) || 
                   className.length < 3 || 
                   /^[a-z]\d*$/.test(className); // single letter + optional numbers
        },
        
        getSelectorMatchCount: function(selector) {
            try {
                return document.querySelectorAll(selector).length;
            } catch (error) {
                return Infinity; // Invalid selector
            }
        },
        
        validateSelector: function(selector, element) {
            try {
                // Handle XPath selectors
                if (selector.startsWith('xpath:')) {
                    const xpath = selector.substring(6);
                    const results = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    
                    // Check if the selector finds the right element and isn't too broad
                    if (results.snapshotLength === 0 || results.snapshotLength > 50) {
                        return false;
                    }
                    
                    // Check if our target element is in the results
                    for (let i = 0; i < results.snapshotLength; i++) {
                        if (results.snapshotItem(i) === element) {
                            return true;
                        }
                    }
                    return false;
                }
                
                // Handle CSS selectors
                const found = document.querySelector(selector);
                const matchCount = this.getSelectorMatchCount(selector);
                
                // Validate that selector points to the right element and isn't too broad
                return found === element && matchCount < 50;
            } catch (error) {
                return false;
            }
        },
        
        // XPath Generation Functions
        generateXPathById: function(element) {
            if (element.id && /^[a-zA-Z][\w-]*$/.test(element.id)) {
                return `//*[@id='${element.id}']`;
            }
            return null;
        },
        
        generateXPathByClass: function(element) {
            if (element.className && typeof element.className === 'string') {
                const classes = element.className.trim().split(/\s+/)
                    .filter(cls => cls && /^[a-zA-Z][\w-]*$/.test(cls))
                    .filter(cls => !this.isGenericClass(cls));
                
                if (classes.length > 0) {
                    // Try most specific class first
                    const className = classes[0];
                    const xpath = `//*[contains(@class, '${className}')]`;
                    if (this.getXPathMatchCount(xpath) < 10) {
                        return xpath;
                    }
                }
            }
            return null;
        },
        
        generateXPathByText: function(element) {
            if (element.textContent) {
                const text = element.textContent.trim();
                if (text.length > 2 && text.length < 50) {
                    // Try exact text match
                    const xpath = `//*[text()='${text.replace(/'/g, "\\'")}']`;
                    if (this.getXPathMatchCount(xpath) < 5) {
                        return xpath;
                    }
                    
                    // Try contains text match for longer text
                    if (text.length > 10) {
                        const shortText = text.substring(0, 20);
                        const containsXpath = `//*[contains(text(), '${shortText.replace(/'/g, "\\'")}')]`;
                        if (this.getXPathMatchCount(containsXpath) < 5) {
                            return containsXpath;
                        }
                    }
                }
            }
            return null;
        },
        
        generateXPathByPosition: function(element) {
            const parent = element.parentElement;
            if (parent) {
                const tagName = element.tagName.toLowerCase();
                const siblings = Array.from(parent.children).filter(child => 
                    child.tagName.toLowerCase() === tagName
                );
                const index = siblings.indexOf(element) + 1; // XPath is 1-indexed
                
                if (siblings.length > 1) {
                    const parentXPath = this.getElementXPath(parent);
                    if (parentXPath) {
                        return `${parentXPath}/${tagName}[${index}]`;
                    }
                }
            }
            return null;
        },
        
        generateXPathByAttributes: function(element) {
            const tagName = element.tagName.toLowerCase();
            const attributes = ['href', 'src', 'alt', 'title', 'data-*'];
            
            for (const attr of attributes) {
                if (attr === 'data-*') {
                    // Check for data attributes
                    for (const attrName of element.getAttributeNames()) {
                        if (attrName.startsWith('data-')) {
                            const value = element.getAttribute(attrName);
                            if (value) {
                                const xpath = `//${tagName}[@${attrName}='${value}']`;
                                if (this.getXPathMatchCount(xpath) < 10) {
                                    return xpath;
                                }
                            }
                        }
                    }
                } else {
                    const value = element.getAttribute(attr);
                    if (value) {
                        const xpath = `//${tagName}[@${attr}='${value}']`;
                        if (this.getXPathMatchCount(xpath) < 10) {
                            return xpath;
                        }
                    }
                }
            }
            return null;
        },
        
        generateFallbackXPath: function(element) {
            // Generate a simple position-based XPath as fallback
            return this.getElementXPath(element);
        },
        
        getElementXPath: function(element) {
            if (element.id) {
                return `//*[@id='${element.id}']`;
            }
            
            const parts = [];
            let currentElement = element;
            
            while (currentElement && currentElement.nodeType === Node.ELEMENT_NODE) {
                let part = currentElement.tagName.toLowerCase();
                
                if (currentElement.parentElement) {
                    const siblings = Array.from(currentElement.parentElement.children)
                        .filter(child => child.tagName === currentElement.tagName);
                    
                    if (siblings.length > 1) {
                        const index = siblings.indexOf(currentElement) + 1;
                        part += `[${index}]`;
                    }
                }
                
                parts.unshift(part);
                currentElement = currentElement.parentElement;
            }
            
            return '/' + parts.join('/');
        },
        
        getXPathMatchCount: function(xpath) {
            try {
                const results = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                return results.snapshotLength;
            } catch (error) {
                return Infinity; // Invalid XPath
            }
        },
        
        validateXPathSelector: function(xpath, element) {
            try {
                const results = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                
                // Check if the selector finds the right element and isn't too broad
                if (results.snapshotLength === 0 || results.snapshotLength > 50) {
                    return false;
                }
                
                // Check if our target element is in the results
                for (let i = 0; i < results.snapshotLength; i++) {
                    if (results.snapshotItem(i) === element) {
                        return true;
                    }
                }
                return false;
            } catch (error) {
                return false;
            }
        }
    };
    
    // =============================================================================
    // TOOL MODULES
    // =============================================================================
    
    const ElementTool = {
        activate: function() {
            console.log('📌 Element tool activated');
            StatusManager.setStatus('Click on elements to select them for data extraction');
        },
        
        deactivate: function() {
            this.stopSelection();
        },
        
        startSelection: function() {
            ScraperState.isSelectionMode = true;
            StatusManager.setStatus('Click on elements to select them. Press ESC to cancel.');
            
            // Add ESC listener
            this.escapeHandler = (e) => {
                if (e.key === 'Escape') {
                    this.stopSelection();
                }
            };
            document.addEventListener('keydown', this.escapeHandler);
        },
        
        stopSelection: function() {
            ScraperState.isSelectionMode = false;
            VisualManager.removeHighlight();
            StatusManager.setStatus('Element selection stopped');
            
            if (this.escapeHandler) {
                document.removeEventListener('keydown', this.escapeHandler);
                this.escapeHandler = null;
            }
        },
        
        handleSelection: async function(element) {
            console.log('🔍 Element selection starting, showing prompt...');
            const label = await ModalManager.prompt('Element Label', 'Enter a label for this element', element);
            console.log('✅ Prompt result:', label);
            
            if (!label) {
                console.log('⚠️ No label provided');
                StatusManager.setError('Element label is required');
                return;
            }
            
            // Check for duplicate labels
            if (ScraperState.selectedElements.some(el => el.label === label)) {
                StatusManager.setError('An element with this label already exists');
                return;
            }
            
            const selector = SelectorGenerator.generate(element);
            const elementData = {
                label: label,
                selector: selector,
                selector_type: ScraperState.selectorMode, // Dynamic selector type
                element_type: this.detectElementType(element),
                attribute_name: null,
                is_multiple: false,
                is_required: true,
                is_container: false,
                use_find_similar: false,
                sub_elements: [],
                follow_links: false,
                subpage_elements: []
            };
            
            StateManager.addElement(elementData);
            VisualManager.addElementVisual(element, label, ScraperState.selectedElements.length - 1);
            
            console.log(`✅ Element selected: ${label} -> ${selector}`);
            StatusManager.setSuccessStatus(`Element "${label}" added successfully`);
            
            // Add to Python if callback available
            if (typeof window.add_element_py === 'function') {
                try {
                    window.add_element_py(JSON.stringify(elementData));
                } catch (error) {
                    console.error('Error calling Python callback:', error);
                }
            }
        },
        
        detectElementType: function(element) {
            const tagName = element.tagName.toLowerCase();
            
            if (tagName === 'a') return 'link';
            if (tagName === 'img') return 'image';
            if (['input', 'textarea', 'select'].includes(tagName)) return 'input';
            
            // Check if element contains primarily numeric content
            const text = element.textContent?.trim();
            if (text && /^\$?[\d,]+\.?\d*$/.test(text)) return 'number';
            
            return 'text';
        }
    };
    
    const ActionTool = {
        activate: function() {
            console.log('🔗 Action tool activated');
            StatusManager.setStatus('Click on interactive elements (buttons, links) to add actions');
        },
        
        deactivate: function() {
            this.stopSelection();
        },
        
        startSelection: function() {
            ScraperState.isSelectionMode = true;
            StatusManager.setStatus('Click on buttons or links to add actions. Press ESC to cancel.');
            
            this.escapeHandler = (e) => {
                if (e.key === 'Escape') {
                    this.stopSelection();
                }
            };
            document.addEventListener('keydown', this.escapeHandler);
        },
        
        stopSelection: function() {
            ScraperState.isSelectionMode = false;
            VisualManager.removeHighlight();
            StatusManager.setStatus('Action selection stopped');
            
            if (this.escapeHandler) {
                document.removeEventListener('keydown', this.escapeHandler);
                this.escapeHandler = null;
            }
        },
        
        handleSelection: async function(element) {
            const label = await ModalManager.prompt('Action Label', 'Enter a label for this action', element);
            
            if (!label) {
                StatusManager.setError('Action label is required');
                return;
            }
            
            const selector = SelectorGenerator.generate(element);
            const targetUrl = this.extractTargetUrl(element);
            
            const actionData = {
                label: label,
                selector: selector,
                action_type: 'click',
                target_url: targetUrl
            };
            
            StateManager.addAction(actionData);
            VisualManager.addActionVisual(element, label, ScraperState.actions.length - 1);
            
            console.log(`✅ Action selected: ${label} -> ${selector}`);
            StatusManager.setSuccessStatus(`Action "${label}" added successfully`);
            
            // Add to Python if callback available
            if (typeof window.add_action_py === 'function') {
                try {
                    window.add_action_py(JSON.stringify(actionData));
                } catch (error) {
                    console.error('Error calling Python callback:', error);
                }
            }
        },
        
        extractTargetUrl: function(element) {
            if (element.tagName.toLowerCase() === 'a' && element.href) {
                return element.href;
            }
            
            // Check for data attributes that might contain URLs
            const urlAttrs = ['data-url', 'data-href', 'data-link'];
            for (const attr of urlAttrs) {
                const url = element.getAttribute(attr);
                if (url) return url;
            }
            
            return null;
        }
    };
    
    const ContainerTool = {
        activate: function() {
            console.log('📦 Container tool activated');
            StatusManager.setStatus('Click on repeating elements (cards, items) to create containers');
        },
        
        deactivate: function() {
            this.stopSelection();
        },
        
        startSelection: function() {
            ScraperState.isSelectionMode = true;
            StatusManager.setStatus('Click on a repeating element to create a container. Press ESC to cancel.');
            
            this.escapeHandler = (e) => {
                if (e.key === 'Escape') {
                    this.stopSelection();
                }
            };
            document.addEventListener('keydown', this.escapeHandler);
        },
        
        stopSelection: function() {
            ScraperState.isSelectionMode = false;
            VisualManager.removeHighlight();
            StatusManager.setStatus('Container selection stopped');
            
            if (this.escapeHandler) {
                document.removeEventListener('keydown', this.escapeHandler);
                this.escapeHandler = null;
            }
        },
        
        handleSelection: async function(element) {
            const label = await ModalManager.prompt('Container Label', 'Enter a label for this container', element);
            
            if (!label) {
                StatusManager.setError('Container label is required');
                return;
            }
            
            const selector = SelectorGenerator.generate(element);
            const similarElements = this.findSimilarElements(element);
            
            // Validate that we're selecting a meaningful container
            if (similarElements.length < 2) {
                const proceed = await ModalManager.confirm(
                    'Container Validation',
                    `Only ${similarElements.length} element(s) found with this selector. Containers should have multiple similar elements. Continue anyway?`
                );
                if (!proceed) {
                    StatusManager.setStatus('Container selection cancelled');
                    return;
                }
            }
            
            // Warn if too many elements
            if (similarElements.length > 100) {
                const proceed = await ModalManager.confirm(
                    'Too Many Elements',
                    `This selector matches ${similarElements.length} elements, which is very high. This might be too generic. Continue anyway?`
                );
                if (!proceed) {
                    StatusManager.setStatus('Container selection cancelled');
                    return;
                }
            }
            
            const containerData = {
                label: label,
                selector: selector,
                selector_type: ScraperState.selectorMode, // Dynamic selector type
                element_type: 'container',
                is_container: true,
                is_multiple: true,
                is_required: true,
                use_find_similar: false,
                sub_elements: [],
                follow_links: false,
                subpage_elements: [],
                similar_count: similarElements.length
            };
            
            StateManager.addContainer(containerData);
            StateManager.setState({ currentContainer: containerData });
            
            console.log(`✅ Container selected: ${label} -> ${selector} (${similarElements.length} similar elements)`);
            StatusManager.setSuccessStatus(`Container "${label}" created with ${similarElements.length} similar elements. Now click "Add Sub-Element" to select data within the container.`);
        },
        
        startSubElementSelection: function() {
            if (!ScraperState.currentContainer) {
                StatusManager.setError('Please select a container first');
                return;
            }
            
            ScraperState.isSelectionMode = true;
            StatusManager.setStatus('Click on elements inside the container to add sub-elements. Press ESC to cancel.');
            
            this.escapeHandler = (e) => {
                if (e.key === 'Escape') {
                    this.stopSelection();
                }
            };
            document.addEventListener('keydown', this.escapeHandler);
        },
        
        handleSubElementSelection: async function(element) {
            if (!ScraperState.currentContainer) {
                StatusManager.setError('No container selected');
                return;
            }
            
            const label = await ModalManager.prompt('Sub-Element Label', 'Enter a label for this sub-element (e.g., "name", "price", "link")', element);
            
            if (!label) {
                StatusManager.setError('Sub-element label is required');
                return;
            }
            
            // Check if label already exists in current container
            const existingLabels = ScraperState.currentContainer.sub_elements.map(sub => sub.label);
            if (existingLabels.includes(label)) {
                StatusManager.setError('A sub-element with this label already exists in this container');
                return;
            }
            
            // Generate a relative selector within the container
            const relativeSelector = this.generateRelativeSelector(element, ScraperState.currentContainer.selector);
            
            const subElementData = {
                label: label,
                selector: relativeSelector,
                selector_type: ScraperState.selectorMode, // Dynamic selector type
                element_type: ElementTool.detectElementType(element),
                attribute_name: null,
                is_multiple: false,
                is_required: true
            };
            
            // Add to current container's sub_elements
            ScraperState.currentContainer.sub_elements.push(subElementData);
            
            // Update the container in the containers array
            const containerIndex = ScraperState.containers.findIndex(c => c.label === ScraperState.currentContainer.label);
            if (containerIndex >= 0) {
                ScraperState.containers[containerIndex] = ScraperState.currentContainer;
            }
            
            console.log(`✅ Sub-element added to container "${ScraperState.currentContainer.label}": ${label} -> ${relativeSelector}`);
            StatusManager.setSuccessStatus(`Sub-element "${label}" added to container "${ScraperState.currentContainer.label}"`);
            
            // Update display
            ControlPanel.updateContainersList();
        },
        
        generateRelativeSelector: function(element, containerSelector) {
            // Try to generate a selector relative to the container
            try {
                // Use current selector mode to generate appropriate selector
                if (ScraperState.selectorMode === 'xpath') {
                    return this.generateRelativeXPathSelector(element, containerSelector);
                } else {
                    return this.generateRelativeCSSSelector(element, containerSelector);
                }
            } catch (error) {
                console.error('Error generating relative selector:', error);
                return element.tagName.toLowerCase();
            }
        },
        
        generateRelativeCSSSelector: function(element, containerSelector) {
            // First, try to generate a simple relative selector
            const directSelector = SelectorGenerator.generateCSSSelector(element);
            
            // Test if this selector works within the container context
            const containers = document.querySelectorAll(containerSelector.replace('xpath:', ''));
            if (containers.length > 0) {
                const firstContainer = containers[0];
                const foundInContainer = firstContainer.querySelector(directSelector);
                
                if (foundInContainer) {
                    return directSelector;
                }
            }
            
            // If direct selector doesn't work, try to create a more specific relative path
            const tagName = element.tagName.toLowerCase();
            
            // Try class-based selector
            if (element.className && typeof element.className === 'string') {
                const classes = element.className.trim().split(/\s+/)
                    .filter(cls => cls && /^[a-zA-Z][\w-]*$/.test(cls))
                    .filter(cls => !SelectorGenerator.isGenericClass(cls));
                
                if (classes.length > 0) {
                    const classSelector = `.${classes.join('.')}`;
                    // Test this selector in container context
                    if (containers.length > 0) {
                        const foundElements = containers[0].querySelectorAll(classSelector);
                        if (foundElements.length > 0 && foundElements.length < 10) {
                            return classSelector;
                        }
                    }
                }
            }
            
            // Try attribute-based selectors
            const attributes = ['data-testid', 'data-test', 'aria-label', 'name', 'role', 'type'];
            for (const attr of attributes) {
                const value = element.getAttribute(attr);
                if (value) {
                    const attrSelector = `[${attr}="${value}"]`;
                    if (containers.length > 0) {
                        const foundElements = containers[0].querySelectorAll(attrSelector);
                        if (foundElements.length > 0 && foundElements.length < 10) {
                            return attrSelector;
                        }
                    }
                }
            }
            
            // Try nth-child approach
            const parent = element.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children);
                const index = siblings.indexOf(element);
                if (index >= 0) {
                    return `${tagName}:nth-child(${index + 1})`;
                }
            }
            
            // Fallback to tag name
            return tagName;
        },
        
        generateRelativeXPathSelector: function(element, containerSelector) {
            // Generate smart XPath selectors that differentiate between similar elements
            const tagName = element.tagName.toLowerCase();
            
            // Get element text content for semantic matching
            const textContent = element.textContent ? element.textContent.trim() : '';
            
            // Generate context-aware XPath based on element purpose
            if (element.tagName === 'A') {
                // For links, differentiate by href attribute
                const href = element.getAttribute('href');
                if (href) {
                    if (href.includes('mailto:')) {
                        return `xpath:.//a[contains(@href, 'mailto:')]`;
                    } else if (href.includes('tel:')) {
                        return `xpath:.//a[contains(@href, 'tel:')]`;
                    } else if (href.includes('/lawyer/')) {
                        return `xpath:.//a[contains(@href, '/lawyer/')]`;
                    }
                    // For other links, use position if multiple
                    const parent = element.parentElement;
                    if (parent) {
                        const linkSiblings = Array.from(parent.querySelectorAll('a'));
                        if (linkSiblings.length > 1) {
                            const position = linkSiblings.indexOf(element) + 1;
                            return `xpath:.//a[${position}]`;
                        }
                    }
                }
            }
            
            // For span elements, use text content and position to differentiate
            if (tagName === 'span') {
                const parent = element.parentElement;
                if (parent) {
                    const spanSiblings = Array.from(parent.querySelectorAll('span'));
                    const position = spanSiblings.indexOf(element) + 1;
                    
                    // Check if there are multiple spans to differentiate
                    if (spanSiblings.length > 1) {
                        // Use position-based selector for multiple spans
                        return `xpath:.//span[${position}]`;
                    } else {
                        // Single span, use more general selector
                        return `xpath:.//span`;
                    }
                }
            }
            
            // For strong elements (names)
            if (tagName === 'strong') {
                return `xpath:.//strong[1]`; // Usually the first strong tag is the name
            }
            
            // Try class-based XPath
            if (element.className && typeof element.className === 'string') {
                const classes = element.className.trim().split(/\s+/)
                    .filter(cls => cls && /^[a-zA-Z][\w-]*$/.test(cls))
                    .filter(cls => !SelectorGenerator.isGenericClass(cls));
                
                if (classes.length > 0) {
                    const className = classes[0];
                    return `xpath:.//*[contains(@class, '${className}')]`;
                }
            }
            
            // Try attribute-based XPath
            const attributes = ['data-testid', 'data-test', 'aria-label', 'name', 'role', 'type'];
            for (const attr of attributes) {
                const value = element.getAttribute(attr);
                if (value) {
                    return `xpath:.//${tagName}[@${attr}='${value}']`;
                }
            }
            
            // Try text-based matching for unique text (only for very specific/unique text)
            if (textContent && textContent.length > 15 && textContent.length < 30) {
                // Only use text matching for very specific content, not generic terms
                const isGenericText = /^(partner|associate|counsel|director|finance|corporate|litigation|tax)$/i.test(textContent.trim());
                if (!isGenericText) {
                    return `xpath:.//*[contains(text(), '${textContent.substring(0, 20).replace(/'/g, "\\'")}')]`;
                }
            }
            
            // Position-based fallback
            const parent = element.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(child => 
                    child.tagName.toLowerCase() === tagName
                );
                const index = siblings.indexOf(element) + 1;
                
                if (siblings.length > 1) {
                    return `xpath:.//${tagName}[${index}]`;
                }
            }
            
            // Final fallback
            return `xpath:.//${tagName}[1]`;
        },
        
        findSimilarElements: function(element) {
            const selector = SelectorGenerator.generate(element);
            try {
                return Array.from(document.querySelectorAll(selector));
            } catch (error) {
                console.error('Error finding similar elements:', error);
                return [element];
            }
        }
    };
    
    const ScrollTool = {
        activate: function() {
            console.log('📜 Scroll tool activated');
            StatusManager.setStatus('Configure pagination and infinite scroll settings');
        },
        
        deactivate: function() {
            // No special deactivation needed
        },
        
        autoDetectScroll: function() {
            console.log('🔍 Starting auto-detect scroll patterns...');
            
            // Auto-detect common scroll patterns
            const detectedConfig = this.detectScrollPatterns();
            
            if (detectedConfig) {
                console.log('✅ Detected scroll pattern:', detectedConfig);
                StateManager.setState({ scrollConfig: detectedConfig });
                
                let message = `Auto-detected: ${detectedConfig.type}`;
                if (detectedConfig.detected_text) {
                    message += ` ("${detectedConfig.detected_text}")`;
                }
                StatusManager.setSuccessStatus(message);
            } else {
                console.log('❌ No scroll patterns found');
                StatusManager.setError('No scroll patterns detected on this page');
            }
        },
        
        detectScrollPatterns: function() {
            // Look for common pagination patterns using CSS selectors and text matching
            const loadMorePatterns = [
                // Common CSS selectors
                { selector: '.load-more', type: 'css' },
                { selector: '.show-more', type: 'css' },
                { selector: '.load-more-button', type: 'css' },
                { selector: '.show-more-button', type: 'css' },
                { selector: '.view-more', type: 'css' },
                { selector: '[data-load-more]', type: 'css' },
                { selector: '[data-show-more]', type: 'css' },
                { selector: '[data-view-more]', type: 'css' },
                { selector: '.pagination-load-more', type: 'css' },
                { selector: '.load-next', type: 'css' },
                { selector: '.show-all', type: 'css' },
                { selector: '.more-button', type: 'css' },
                { selector: '.expand-button', type: 'css' },
                
                // Site-specific selectors
                { selector: '.wcc-show-desc-btn', type: 'css' }, // Gibson Dunn
                { selector: '.js-load-more', type: 'css' },
                { selector: '.btn-load-more', type: 'css' },
                { selector: '.load-more-btn', type: 'css' },
                
                // Text-based patterns (most comprehensive)
                { text: 'Load More', type: 'text' },
                { text: 'Show More', type: 'text' },
                { text: 'View More', type: 'text' },
                { text: 'See More', type: 'text' },
                { text: 'More Results', type: 'text' },
                { text: 'Load More Results', type: 'text' },
                { text: 'Show All', type: 'text' },
                { text: 'View All', type: 'text' },
                { text: 'Expand', type: 'text' },
                { text: 'Continue', type: 'text' },
                { text: 'Next', type: 'text' },
                { text: 'More', type: 'text' }
            ];
            
            for (const pattern of loadMorePatterns) {
                try {
                    let element = null;
                    
                    if (pattern.type === 'css') {
                        element = document.querySelector(pattern.selector);
                    } else if (pattern.type === 'text') {
                        // Find buttons/links containing the text
                        const buttons = Array.from(document.querySelectorAll('button, a, [role="button"]'));
                        element = buttons.find(btn => 
                            btn.textContent.trim().toLowerCase().includes(pattern.text.toLowerCase())
                        );
                    }
                    
                    if (element && element.offsetParent !== null) {
                        // Generate a selector for the found element
                        let foundSelector = pattern.selector || this.generateSelectorForElement(element);
                        
                        return {
                            type: 'load_more',
                            selector: foundSelector,
                            max_pages: 10,
                            detected_text: element.textContent.trim()
                        };
                    }
                } catch (error) {
                    console.log(`Error checking pattern: ${pattern.selector || pattern.text}`, error);
                    continue;
                }
            }
            
            // Check for infinite scroll indicators
            if (this.hasInfiniteScroll()) {
                return {
                    type: 'infinite_scroll',
                    max_scrolls: 20,
                    scroll_pause: 2000
                };
            }
            
            return null;
        },
        
        generateSelectorForElement: function(element) {
            // Generate a simple selector for the element
            if (element.id) {
                return `#${element.id}`;
            }
            
            if (element.className && typeof element.className === 'string') {
                const classes = element.className.trim().split(/\s+/)
                    .filter(cls => cls && /^[a-zA-Z][\w-]*$/.test(cls));
                if (classes.length > 0) {
                    return `.${classes.join('.')}`;
                }
            }
            
            // Fallback to tag name with text content
            const text = element.textContent.trim();
            if (text && text.length < 50) {
                return `${element.tagName.toLowerCase()}`;
            }
            
            return element.tagName.toLowerCase();
        },
        
        hasInfiniteScroll: function() {
            // Simple heuristic: check if page is much taller than viewport
            return document.body.scrollHeight > window.innerHeight * 3;
        },
        
        addLoadMoreButton: async function() {
            const selector = await ModalManager.prompt('Load More Button', 'Enter CSS selector for "Load More" button');
            
            if (selector) {
                const config = {
                    type: 'load_more',
                    selector: selector,
                    max_pages: 10
                };
                
                StateManager.setState({ scrollConfig: config });
                StatusManager.setSuccessStatus('Load More configuration added');
            }
        },
        
        addInfiniteScroll: function() {
            const config = {
                type: 'infinite_scroll',
                max_scrolls: 20,
                scroll_pause: 2000
            };
            
            StateManager.setState({ scrollConfig: config });
            StatusManager.setSuccessStatus('Infinite Scroll configuration added');
        },
        
        clearScroll: function() {
            StateManager.setState({ scrollConfig: null });
            StatusManager.setSuccessStatus('Scroll configuration cleared');
        }
    };
    
    // =============================================================================
    // STATUS MANAGER MODULE
    // =============================================================================
    
    const StatusManager = {
        setStatus: function(message) {
            console.log(`ℹ️ Status: ${message}`);
            this.updateStatusDisplay(message, 'info');
        },
        
        setSuccessStatus: function(message) {
            console.log(`✅ Success: ${message}`);
            this.updateStatusDisplay(message, 'success');
        },
        
        setError: function(message) {
            console.error(`❌ Error: ${message}`);
            this.updateStatusDisplay(message, 'error');
        },
        
        updateStatusDisplay: function(message, type) {
            const statusEl = document.querySelector('.scraper-status');
            if (statusEl) {
                statusEl.textContent = message;
                statusEl.className = `scraper-status scraper-status-${type}`;
                
                // Auto-clear after 5 seconds for success/error messages
                if (type !== 'info') {
                    setTimeout(() => {
                        if (statusEl.textContent === message) {
                            statusEl.textContent = 'Ready';
                            statusEl.className = 'scraper-status scraper-status-info';
                        }
                    }, 5000);
                }
            }
        }
    };
    
    // =============================================================================
    // CONTROL PANEL MODULE
    // =============================================================================
    
    const ControlPanel = {
        create: function() {
            if (document.querySelector('.scraper-control-panel')) {
                return; // Already exists
            }
            
            const panel = document.createElement('div');
            panel.className = 'scraper-control-panel';
            panel.innerHTML = this.getHTML();
            
            document.body.appendChild(panel);
            
            this.attachEventHandlers();
            this.updateDisplay();
        },
        
        getHTML: function() {
            return `
                <div class="scraper-panel-header">
                    <h3>🕷️ Interactive Scraper</h3>
                    <button id="toggle-panel-btn" class="scraper-btn scraper-btn-secondary">−</button>
                </div>
                
                <div class="scraper-panel-content">
                    <div class="scraper-status">Ready</div>
                    
                    <div class="scraper-selector-mode">
                        <label class="scraper-mode-label">
                            Selector Mode:
                            <div class="scraper-toggle-container">
                                <span class="scraper-mode-text">CSS</span>
                                <div class="scraper-toggle-switch" id="selector-mode-toggle">
                                    <div class="scraper-toggle-slider"></div>
                                </div>
                                <span class="scraper-mode-text">XPath</span>
                            </div>
                        </label>
                    </div>
                    
                    <div class="scraper-tools">
                        <button id="element-tool-btn" class="scraper-tool-btn scraper-tool-active" data-tool="element">📌 Elements</button>
                        <button id="action-tool-btn" class="scraper-tool-btn" data-tool="action">🔗 Actions</button>
                        <button id="container-tool-btn" class="scraper-tool-btn" data-tool="container">📦 Containers</button>
                        <button id="scroll-tool-btn" class="scraper-tool-btn" data-tool="scroll">📜 Scroll</button>
                    </div>
                    
                    <div id="element-section" class="scraper-section">
                        <div class="scraper-section-actions">
                            <button id="start-element-btn" class="scraper-btn scraper-btn-primary">Select Element</button>
                            <button id="clear-elements-btn" class="scraper-btn scraper-btn-secondary">Clear All</button>
                        </div>
                        <div id="elements-list" class="scraper-list"></div>
                    </div>
                    
                    <div id="action-section" class="scraper-section" style="display: none;">
                        <div class="scraper-section-actions">
                            <button id="start-action-btn" class="scraper-btn scraper-btn-primary">Select Action</button>
                            <button id="clear-actions-btn" class="scraper-btn scraper-btn-secondary">Clear All</button>
                        </div>
                        <div id="actions-list" class="scraper-list"></div>
                    </div>
                    
                    <div id="container-section" class="scraper-section" style="display: none;">
                        <div class="scraper-section-actions">
                            <button id="start-container-btn" class="scraper-btn scraper-btn-primary">Select Container</button>
                            <button id="add-sub-element-btn" class="scraper-btn scraper-btn-secondary">Add Sub-Element</button>
                            <button id="clear-containers-btn" class="scraper-btn scraper-btn-secondary">Clear All</button>
                        </div>
                        <div id="containers-list" class="scraper-list"></div>
                    </div>
                    
                    <div id="scroll-section" class="scraper-section" style="display: none;">
                        <div class="scraper-section-actions">
                            <button id="detect-scroll-btn" class="scraper-btn scraper-btn-primary">Auto-Detect</button>
                            <button id="add-load-more-btn" class="scraper-btn scraper-btn-secondary">Load More</button>
                            <button id="add-infinite-scroll-btn" class="scraper-btn scraper-btn-secondary">Infinite Scroll</button>
                            <button id="clear-scroll-btn" class="scraper-btn scraper-btn-secondary">Clear</button>
                        </div>
                        <div id="scroll-display" class="scraper-list"></div>
                    </div>
                    
                    <div class="scraper-main-actions">
                        <button id="preview-template-btn" class="scraper-btn scraper-btn-secondary">Preview Template</button>
                        <button id="save-template-btn" class="scraper-btn scraper-btn-primary">Save Template</button>
                    </div>
                </div>
            `;
        },
        
        attachEventHandlers: function() {
            const buttonHandlers = {
                'toggle-panel-btn': () => this.toggle(),
                'selector-mode-toggle': () => this.toggleSelectorMode(),
                'element-tool-btn': () => this.switchTool('element'),
                'action-tool-btn': () => this.switchTool('action'),
                'container-tool-btn': () => this.switchTool('container'),
                'scroll-tool-btn': () => this.switchTool('scroll'),
                'start-element-btn': () => ElementTool.startSelection(),
                'clear-elements-btn': () => this.clearElements(),
                'start-action-btn': () => ActionTool.startSelection(),
                'clear-actions-btn': () => this.clearActions(),
                'start-container-btn': () => ContainerTool.startSelection(),
                'add-sub-element-btn': () => this.toggleSubElementSelection(),
                'clear-containers-btn': () => this.clearContainers(),
                'detect-scroll-btn': () => ScrollTool.autoDetectScroll(),
                'add-load-more-btn': () => ScrollTool.addLoadMoreButton(),
                'add-infinite-scroll-btn': () => ScrollTool.addInfiniteScroll(),
                'clear-scroll-btn': () => ScrollTool.clearScroll(),
                'preview-template-btn': () => this.previewTemplate(),
                'save-template-btn': () => this.saveTemplate()
            };
            
            EventManager.attachMultipleHandlers(buttonHandlers);
        },
        
        toggle: function() {
            const panel = document.querySelector('.scraper-control-panel');
            const content = panel.querySelector('.scraper-panel-content');
            const toggleBtn = panel.querySelector('#toggle-panel-btn');
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                toggleBtn.textContent = '−';
            } else {
                content.style.display = 'none';
                toggleBtn.textContent = '+';
            }
        },
        
        toggleSelectorMode: function() {
            // Toggle between CSS and XPath modes
            ScraperState.selectorMode = ScraperState.selectorMode === 'css' ? 'xpath' : 'css';
            
            // Update the toggle switch visual state
            const toggleSwitch = document.getElementById('selector-mode-toggle');
            const slider = toggleSwitch.querySelector('.scraper-toggle-slider');
            
            if (ScraperState.selectorMode === 'xpath') {
                toggleSwitch.classList.add('scraper-toggle-active');
                slider.style.transform = 'translateX(20px)';
            } else {
                toggleSwitch.classList.remove('scraper-toggle-active');
                slider.style.transform = 'translateX(0)';
            }
            
            // Update status to show current mode
            const status = document.querySelector('.scraper-status');
            if (status) {
                status.textContent = `Ready (${ScraperState.selectorMode.toUpperCase()} mode)`;
            }
            
            console.log(`🔧 Switched to ${ScraperState.selectorMode.toUpperCase()} selector mode`);
            
            // Log to Python if available
            if (typeof window.log_message_py === 'function') {
                window.log_message_py(`Switched to ${ScraperState.selectorMode.toUpperCase()} selector mode`);
            }
        },
        
        switchTool: function(toolName) {
            // Update button states
            document.querySelectorAll('.scraper-tool-btn').forEach(btn => {
                btn.classList.remove('scraper-tool-active');
            });
            document.getElementById(`${toolName}-tool-btn`).classList.add('scraper-tool-active');
            
            // Show/hide sections
            document.querySelectorAll('.scraper-section').forEach(section => {
                section.style.display = 'none';
            });
            document.getElementById(`${toolName}-section`).style.display = 'block';
            
            // Update state and activate tool
            StateManager.setState({ currentTool: toolName });
            
            // Activate the appropriate tool
            if (toolName === 'element') ElementTool.activate();
            else if (toolName === 'action') ActionTool.activate();
            else if (toolName === 'container') ContainerTool.activate();
            else if (toolName === 'scroll') ScrollTool.activate();
        },
        
        updateDisplay: function() {
            this.updateElementsList();
            this.updateActionsList();
            this.updateContainersList();
            this.updateScrollDisplay();
        },
        
        updateElementsList: function() {
            const listEl = document.getElementById('elements-list');
            if (!listEl) return;
            
            listEl.innerHTML = ScraperState.selectedElements.map((element, index) => `
                <div class="scraper-list-item">
                    <span class="scraper-list-label">${index + 1}. ${element.label}</span>
                    <span class="scraper-list-selector">${element.selector}</span>
                    <button class="scraper-btn-remove" data-action="remove-element-${index}">×</button>
                </div>
            `).join('');
            
            // Attach remove handlers
            ScraperState.selectedElements.forEach((_, index) => {
                EventManager.attachHandler(`remove-element-${index}`, () => this.removeElement(index));
            });
        },
        
        updateActionsList: function() {
            const listEl = document.getElementById('actions-list');
            if (!listEl) return;
            
            listEl.innerHTML = ScraperState.actions.map((action, index) => `
                <div class="scraper-list-item">
                    <span class="scraper-list-label">${index + 1}. ${action.label}</span>
                    <span class="scraper-list-selector">${action.selector}</span>
                    ${action.target_url ? `<button class="scraper-btn-navigate" data-action="navigate-${index}">→</button>` : ''}
                    <button class="scraper-btn-remove" data-action="remove-action-${index}">×</button>
                </div>
            `).join('');
            
            // Attach handlers
            ScraperState.actions.forEach((action, index) => {
                EventManager.attachHandler(`remove-action-${index}`, () => this.removeAction(index));
                if (action.target_url) {
                    EventManager.attachHandler(`navigate-${index}`, () => this.navigateToAction(index));
                }
            });
        },
        
        updateContainersList: function() {
            const listEl = document.getElementById('containers-list');
            if (!listEl) return;
            
            listEl.innerHTML = ScraperState.containers.map((container, index) => {
                const subElementsHtml = container.sub_elements && container.sub_elements.length > 0 
                    ? container.sub_elements.map(sub => `
                        <div class="scraper-sub-element">
                            <span class="scraper-sub-label">• ${sub.label}</span>
                            <span class="scraper-sub-selector">${sub.selector}</span>
                            <span class="scraper-sub-type">[${sub.element_type}]</span>
                        </div>
                    `).join('') 
                    : '<div class="scraper-sub-element-empty">No sub-elements defined</div>';
                
                return `
                    <div class="scraper-container-item">
                        <div class="scraper-list-item">
                            <span class="scraper-list-label">${index + 1}. ${container.label}</span>
                            <span class="scraper-list-selector">${container.selector}</span>
                            <span class="scraper-list-count">(${container.similar_count || 0} items)</span>
                            <button class="scraper-btn-remove" data-action="remove-container-${index}">×</button>
                        </div>
                        <div class="scraper-sub-elements">
                            ${subElementsHtml}
                        </div>
                    </div>
                `;
            }).join('');
            
            // Attach remove handlers
            ScraperState.containers.forEach((_, index) => {
                EventManager.attachHandler(`remove-container-${index}`, () => this.removeContainer(index));
            });
        },
        
        updateScrollDisplay: function() {
            const displayEl = document.getElementById('scroll-display');
            if (!displayEl) return;
            
            if (ScraperState.scrollConfig) {
                const config = ScraperState.scrollConfig;
                displayEl.innerHTML = `
                    <div class="scraper-list-item">
                        <span class="scraper-list-label">Type: ${config.type}</span>
                        ${config.selector ? `<span class="scraper-list-selector">${config.selector}</span>` : ''}
                        <button class="scraper-btn-remove" data-action="remove-scroll">×</button>
                    </div>
                `;
                
                EventManager.attachHandler('remove-scroll', () => ScrollTool.clearScroll());
            } else {
                displayEl.innerHTML = '<div class="scraper-empty">No scroll configuration</div>';
            }
        },
        
        removeElement: function(index) {
            StateManager.removeElement(index);
            VisualManager.clearAllVisuals();
            this.updateElementsList();
        },
        
        removeAction: function(index) {
            const actions = ScraperState.actions.filter((_, i) => i !== index);
            StateManager.setState({ actions });
            this.updateActionsList();
        },
        
        removeContainer: function(index) {
            const containers = ScraperState.containers.filter((_, i) => i !== index);
            StateManager.setState({ containers });
            this.updateContainersList();
        },
        
        clearElements: function() {
            StateManager.clearElements();
            VisualManager.clearAllVisuals();
            this.updateElementsList();
        },
        
        clearActions: function() {
            StateManager.clearActions();
            this.updateActionsList();
        },
        
        clearContainers: function() {
            StateManager.clearContainers();
            this.updateContainersList();
        },
        
        startSubElementSelection: function() {
            if (!ScraperState.currentContainer) {
                StatusManager.setError('Please select a container first');
                return;
            }
            
            // Set button as active for sub-element mode
            const addSubElementBtn = document.getElementById('add-sub-element-btn');
            if (addSubElementBtn) {
                addSubElementBtn.dataset.active = 'true';
                addSubElementBtn.textContent = 'Cancel Sub-Element';
                addSubElementBtn.style.background = '#dc3545';
                addSubElementBtn.style.borderColor = '#dc3545';
            }
            
            ContainerTool.startSubElementSelection();
        },
        
        stopSubElementSelection: function() {
            // Reset button state
            const addSubElementBtn = document.getElementById('add-sub-element-btn');
            if (addSubElementBtn) {
                addSubElementBtn.dataset.active = 'false';
                addSubElementBtn.textContent = 'Add Sub-Element';
                addSubElementBtn.style.background = '';
                addSubElementBtn.style.borderColor = '';
            }
            
            ContainerTool.stopSelection();
        },
        
        toggleSubElementSelection: function() {
            const addSubElementBtn = document.getElementById('add-sub-element-btn');
            const isActive = addSubElementBtn && addSubElementBtn.dataset.active === 'true';
            
            if (isActive) {
                this.stopSubElementSelection();
            } else {
                this.startSubElementSelection();
            }
        },
        
        navigateToAction: function(index) {
            const action = ScraperState.actions[index];
            if (action?.target_url) {
                console.log(`🌐 Navigating to: ${action.target_url}`);
                
                // Save navigation state before navigating
                NavigationState.save(ScraperState);
                
                if (typeof window.log_message_py === 'function') {
                    window.log_message_py(`Navigating to action: ${action.label} -> ${action.target_url}`);
                }
                
                setTimeout(() => {
                    window.location.href = action.target_url;
                }, 100);
            }
        },
        
        previewTemplate: function() {
            const template = TemplateBuilder.build();
            console.log('👁️ Template Preview:', template);
            
            const content = `<pre>${JSON.stringify(template, null, 2)}</pre>`;
            ModalManager.show({
                title: 'Template Preview',
                content: content,
                buttons: ['Close']
            });
        },
        
        saveTemplate: async function() {
            if (ScraperState.selectedElements.length === 0 && 
                ScraperState.containers.length === 0 && 
                ScraperState.actions.length === 0) {
                await ModalManager.alert('Please select at least one element, container, or action before saving.');
                return;
            }
            
            try {
                const template = TemplateBuilder.build();
                console.log('💾 Saving template:', template);
                
                if (typeof window.save_template_py === 'function') {
                    window.save_template_py(JSON.stringify(template));
                    StatusManager.setSuccessStatus('Template saved successfully!');
                    
                    // Clear navigation state since template is saved
                    NavigationState.clear();
                    
                    setTimeout(async () => {
                        const shouldClose = await ModalManager.confirm('Session Complete', 'Template saved successfully! Close the browser to complete the session?');
                        if (shouldClose) {
                            window.close();
                        }
                    }, 2000);
                } else {
                    await ModalManager.alert('Error: Unable to save template. Python callback not available.');
                }
            } catch (error) {
                console.error('Save error:', error);
                await ModalManager.alert(`Error saving template: ${error.message}`);
            }
        }
    };
    
    // =============================================================================
    // TEMPLATE BUILDER MODULE
    // =============================================================================
    
    const TemplateBuilder = {
        build: function() {
            const template = {
                name: this.generateTemplateName(),
                url: window.location.href,
                description: `Interactive template for ${window.location.hostname}`,
                elements: [...ScraperState.selectedElements, ...this.convertContainersToElements()],
                actions: ScraperState.actions,
                created_at: new Date().toISOString()
            };
            
            if (ScraperState.scrollConfig) {
                template.scroll_config = ScraperState.scrollConfig;
            }
            
            return template;
        },
        
        convertContainersToElements: function() {
            return ScraperState.containers.map(container => ({
                ...container,
                element_type: 'container'
            }));
        },
        
        generateTemplateName: function() {
            const hostname = window.location.hostname.replace('www.', '');
            const timestamp = new Date().toISOString().slice(0, 16).replace(/[-:]/g, '');
            return `${hostname}_${timestamp}`;
        }
    };
    
    // =============================================================================
    // STYLES INJECTION
    // =============================================================================
    
    function injectStyles() {
        if (document.getElementById('scraper-styles')) {
            return; // Already injected
        }
        
        const style = document.createElement('style');
        style.id = 'scraper-styles';
        style.textContent = `
            .scraper-control-panel {
                position: fixed !important;
                top: 20px !important;
                right: 20px !important;
                width: 350px !important;
                max-height: 80vh !important;
                overflow-y: auto !important;
                background: #ffffff !important;
                border: 2px solid #ddd !important;
                border-radius: 8px !important;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15) !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                font-size: 14px !important;
                z-index: ${CONFIG.MODAL_Z_INDEX - 1000} !important;
                color: #333 !important;
                line-height: 1.4 !important;
            }
            
            .scraper-panel-header {
                padding: 12px 16px !important;
                background: #f8f9fa !important;
                border-bottom: 1px solid #ddd !important;
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
            }
            
            .scraper-panel-header h3 {
                margin: 0 !important;
                font-size: 16px !important;
                font-weight: 600 !important;
                color: #333 !important;
            }
            
            .scraper-panel-content {
                padding: 16px !important;
            }
            
            .scraper-status {
                padding: 8px 12px !important;
                margin-bottom: 16px !important;
                border-radius: 4px !important;
                font-size: 13px !important;
                font-weight: 500 !important;
            }
            
            .scraper-status-info {
                background: #e3f2fd !important;
                color: #1976d2 !important;
                border: 1px solid #bbdefb !important;
            }
            
            .scraper-status-success {
                background: #e8f5e8 !important;
                color: #2e7d32 !important;
                border: 1px solid #c8e6c9 !important;
            }
            
            .scraper-status-error {
                background: #ffebee !important;
                color: #c62828 !important;
                border: 1px solid #ffcdd2 !important;
            }
            
            .scraper-selector-mode {
                margin-bottom: 16px !important;
                padding: 8px 0 !important;
            }
            
            .scraper-mode-label {
                display: block !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                color: #555 !important;
                margin-bottom: 8px !important;
            }
            
            .scraper-toggle-container {
                display: flex !important;
                align-items: center !important;
                gap: 8px !important;
                margin-top: 4px !important;
            }
            
            .scraper-mode-text {
                font-size: 12px !important;
                color: #666 !important;
                font-weight: 500 !important;
                min-width: 35px !important;
                text-align: center !important;
            }
            
            .scraper-toggle-switch {
                position: relative !important;
                width: 40px !important;
                height: 20px !important;
                background: #ccc !important;
                border-radius: 20px !important;
                cursor: pointer !important;
                transition: background 0.3s !important;
            }
            
            .scraper-toggle-switch.scraper-toggle-active {
                background: #4CAF50 !important;
            }
            
            .scraper-toggle-slider {
                position: absolute !important;
                top: 2px !important;
                left: 2px !important;
                width: 16px !important;
                height: 16px !important;
                background: white !important;
                border-radius: 50% !important;
                transition: transform 0.3s !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
            }
            
            .scraper-tools {
                display: flex !important;
                gap: 4px !important;
                margin-bottom: 16px !important;
                flex-wrap: wrap !important;
            }
            
            .scraper-tool-btn {
                padding: 6px 12px !important;
                border: 1px solid #ddd !important;
                background: #f8f9fa !important;
                border-radius: 4px !important;
                cursor: pointer !important;
                font-size: 12px !important;
                transition: all 0.2s !important;
                flex: 1 !important;
                min-width: 70px !important;
            }
            
            .scraper-tool-btn:hover {
                background: #e9ecef !important;
                border-color: #adb5bd !important;
            }
            
            .scraper-tool-active {
                background: #007bff !important;
                color: white !important;
                border-color: #007bff !important;
            }
            
            .scraper-section {
                margin-bottom: 20px !important;
            }
            
            .scraper-section-actions {
                display: flex !important;
                gap: 8px !important;
                margin-bottom: 12px !important;
                flex-wrap: wrap !important;
            }
            
            .scraper-btn {
                padding: 8px 16px !important;
                border: 1px solid #ddd !important;
                border-radius: 4px !important;
                cursor: pointer !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                transition: all 0.2s !important;
                background: #fff !important;
                color: #333 !important;
            }
            
            .scraper-btn-primary {
                background: #007bff !important;
                color: white !important;
                border-color: #007bff !important;
            }
            
            .scraper-btn-primary:hover {
                background: #0056b3 !important;
                border-color: #004085 !important;
            }
            
            .scraper-btn-secondary {
                background: #6c757d !important;
                color: white !important;
                border-color: #6c757d !important;
            }
            
            .scraper-btn-secondary:hover {
                background: #545b62 !important;
                border-color: #4e555b !important;
            }
            
            .scraper-list {
                max-height: 200px !important;
                overflow-y: auto !important;
                border: 1px solid #ddd !important;
                border-radius: 4px !important;
                background: #f8f9fa !important;
            }
            
            .scraper-list-item {
                padding: 8px 12px !important;
                border-bottom: 1px solid #eee !important;
                display: flex !important;
                align-items: center !important;
                gap: 8px !important;
                font-size: 12px !important;
            }
            
            .scraper-list-item:last-child {
                border-bottom: none !important;
            }
            
            .scraper-list-label {
                font-weight: 600 !important;
                color: #495057 !important;
                min-width: 60px !important;
            }
            
            .scraper-list-selector {
                flex: 1 !important;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
                font-size: 11px !important;
                color: #666 !important;
                background: #fff !important;
                padding: 2px 4px !important;
                border-radius: 2px !important;
                word-break: break-all !important;
            }
            
            .scraper-list-count {
                font-size: 11px !important;
                color: #6c757d !important;
                background: #e9ecef !important;
                padding: 2px 6px !important;
                border-radius: 10px !important;
            }
            
            .scraper-btn-remove, .scraper-btn-navigate {
                width: 20px !important;
                height: 20px !important;
                border: none !important;
                border-radius: 50% !important;
                cursor: pointer !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                font-size: 12px !important;
                font-weight: bold !important;
            }
            
            .scraper-btn-remove {
                background: #dc3545 !important;
                color: white !important;
            }
            
            .scraper-btn-remove:hover {
                background: #c82333 !important;
            }
            
            .scraper-btn-navigate {
                background: #28a745 !important;
                color: white !important;
            }
            
            .scraper-btn-navigate:hover {
                background: #218838 !important;
            }
            
            .scraper-empty {
                padding: 20px !important;
                text-align: center !important;
                color: #6c757d !important;
                font-style: italic !important;
            }
            
            .scraper-container-item {
                margin-bottom: 8px !important;
                border: 1px solid #ddd !important;
                border-radius: 4px !important;
                background: #f8f9fa !important;
            }
            
            .scraper-sub-elements {
                padding: 8px 12px !important;
                background: #ffffff !important;
                border-top: 1px solid #eee !important;
            }
            
            .scraper-sub-element {
                padding: 4px 8px !important;
                margin: 2px 0 !important;
                background: #f1f3f4 !important;
                border-radius: 3px !important;
                display: flex !important;
                align-items: center !important;
                gap: 8px !important;
                font-size: 11px !important;
            }
            
            .scraper-sub-label {
                font-weight: 600 !important;
                color: #495057 !important;
                min-width: 80px !important;
            }
            
            .scraper-sub-selector {
                flex: 1 !important;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
                font-size: 10px !important;
                color: #666 !important;
                background: #fff !important;
                padding: 1px 3px !important;
                border-radius: 2px !important;
                border: 1px solid #ddd !important;
            }
            
            .scraper-sub-type {
                font-size: 10px !important;
                color: #6c757d !important;
                background: #e9ecef !important;
                padding: 1px 4px !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
            }
            
            .scraper-sub-element-empty {
                padding: 8px !important;
                text-align: center !important;
                color: #6c757d !important;
                font-style: italic !important;
                font-size: 11px !important;
            }
            
            .scraper-main-actions {
                display: flex !important;
                gap: 8px !important;
                margin-top: 20px !important;
                padding-top: 16px !important;
                border-top: 1px solid #ddd !important;
            }
            
            .scraper-main-actions .scraper-btn {
                flex: 1 !important;
            }
            
            .scraper-highlight {
                outline: 3px solid #ff9800 !important;
                outline-offset: 2px !important;
                background-color: rgba(255, 152, 0, 0.1) !important;
            }
            
            .scraper-modal {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background: rgba(0,0,0,0.5) !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                z-index: ${CONFIG.MODAL_Z_INDEX} !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            }
            
            .scraper-modal-content {
                background: white !important;
                padding: 24px !important;
                border-radius: 8px !important;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
                max-width: 500px !important;
                width: 90% !important;
                max-height: 80vh !important;
                overflow-y: auto !important;
            }
            
            .scraper-modal-title {
                font-size: 18px !important;
                font-weight: 600 !important;
                margin-bottom: 16px !important;
                color: #333 !important;
            }
            
            .scraper-modal-message {
                margin-bottom: 16px !important;
                color: #555 !important;
                line-height: 1.5 !important;
            }
            
            .scraper-modal-input {
                width: 100% !important;
                padding: 8px 12px !important;
                border: 1px solid #ddd !important;
                border-radius: 4px !important;
                font-size: 14px !important;
                margin-bottom: 16px !important;
                box-sizing: border-box !important;
            }
            
            .scraper-modal-input:focus {
                outline: none !important;
                border-color: #007bff !important;
                box-shadow: 0 0 0 2px rgba(0,123,255,0.25) !important;
            }
            
            .scraper-modal-buttons {
                display: flex !important;
                gap: 8px !important;
                justify-content: flex-end !important;
            }
            
            .scraper-modal-btn {
                padding: 8px 16px !important;
                border: 1px solid #ddd !important;
                border-radius: 4px !important;
                cursor: pointer !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                transition: all 0.2s !important;
            }
            
            .scraper-modal-btn-primary {
                background: #007bff !important;
                color: white !important;
                border-color: #007bff !important;
            }
            
            .scraper-modal-btn-primary:hover {
                background: #0056b3 !important;
                border-color: #004085 !important;
            }
            
            .scraper-modal-btn-secondary {
                background: #6c757d !important;
                color: white !important;
                border-color: #6c757d !important;
            }
            
            .scraper-modal-btn-secondary:hover {
                background: #545b62 !important;
                border-color: #4e555b !important;
            }
            
            pre {
                background: #f8f9fa !important;
                padding: 12px !important;
                border-radius: 4px !important;
                overflow-x: auto !important;
                font-size: 12px !important;
                max-height: 400px !important;
                color: #333 !important;
            }
            
            .scraper-preview-section {
                margin: 16px 0 !important;
                padding: 12px !important;
                background: #f8f9fa !important;
                border-radius: 6px !important;
                border: 1px solid #e9ecef !important;
            }
            
            .scraper-preview-text {
                margin: 8px 0 !important;
                padding: 8px !important;
                background: white !important;
                border-radius: 4px !important;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
                font-size: 12px !important;
                color: #333 !important;
                border: 1px solid #ddd !important;
                max-height: 80px !important;
                overflow-y: auto !important;
                word-break: break-word !important;
            }
            
            .scraper-preview-info {
                font-size: 11px !important;
                color: #6c757d !important;
                margin-top: 8px !important;
                font-family: monospace !important;
            }
        `;
        
        document.head.appendChild(style);
    }
    
    // =============================================================================
    // NAVIGATION STATE PERSISTENCE MODULE
    // =============================================================================
    
    const NavigationState = {
        save: function(state) {
            try {
                const navigationState = {
                    selectedElements: state.selectedElements,
                    containers: state.containers,
                    actions: state.actions,
                    scrollConfig: state.scrollConfig,
                    currentTool: state.currentTool,
                    currentContainer: state.currentContainer,
                    selectorMode: state.selectorMode, // Preserve selector mode
                    timestamp: Date.now()
                };
                
                sessionStorage.setItem('scraperNavigationState', JSON.stringify(navigationState));
                console.log("💾 Navigation state saved");
                
            } catch (error) {
                console.error("❌ Error saving navigation state:", error);
            }
        },
        
        restore: function() {
            try {
                const savedState = sessionStorage.getItem('scraperNavigationState');
                if (!savedState) return null;
                
                const state = JSON.parse(savedState);
                
                // Check if state is recent (within last 5 minutes)
                if (Date.now() - state.timestamp > 5 * 60 * 1000) {
                    sessionStorage.removeItem('scraperNavigationState');
                    return null;
                }
                
                console.log(`🔄 Navigation state restored: ${state.selectedElements?.length || 0} elements, ${state.containers?.length || 0} containers, ${state.actions?.length || 0} actions`);
                
                return {
                    selectedElements: state.selectedElements || [],
                    containers: state.containers || [],
                    actions: state.actions || [],
                    scrollConfig: state.scrollConfig || null,
                    currentTool: state.currentTool || 'element',
                    currentContainer: state.currentContainer || null,
                    selectorMode: state.selectorMode || 'css' // Restore selector mode
                };
                
            } catch (error) {
                console.error("❌ Error restoring navigation state:", error);
                sessionStorage.removeItem('scraperNavigationState');
                return null;
            }
        },
        
        clear: function() {
            try {
                sessionStorage.removeItem('scraperNavigationState');
                console.log("🗑️ Navigation state cleared");
            } catch (error) {
                console.error("❌ Error clearing navigation state:", error);
            }
        }
    };
    
    // =============================================================================
    // MAIN INITIALIZATION
    // =============================================================================
    
    class InteractiveScraper {
        constructor() {
            console.log("🚀 Initializing Interactive Scraper...");
            
            // Restore navigation state if available
            const restoredState = NavigationState.restore();
            if (restoredState) {
                // Merge restored state into global state
                Object.assign(ScraperState, restoredState);
                console.log("✅ Navigation state restored successfully");
            }
            
            // Initialize state manager subscription
            StateManager.subscribe(this.handleStateChange.bind(this));
            
            // Set up event delegation
            EventManager.setupDelegation();
            
            // Inject styles and create UI
            injectStyles();
            ControlPanel.create();
            
            // Restore UI state if we had restored data
            if (restoredState) {
                ControlPanel.updateDisplay();
                // Set the correct tool
                ControlPanel.switchTool(restoredState.currentTool || 'element');
                
                // Restore selector mode UI
                if (restoredState.selectorMode === 'xpath') {
                    // Update toggle switch to XPath mode
                    const toggleSwitch = document.getElementById('selector-mode-toggle');
                    const slider = toggleSwitch?.querySelector('.scraper-toggle-slider');
                    if (toggleSwitch && slider) {
                        toggleSwitch.classList.add('scraper-toggle-active');
                        slider.style.transform = 'translateX(20px)';
                    }
                    
                    // Update status to show XPath mode
                    const status = document.querySelector('.scraper-status');
                    if (status) {
                        status.textContent = `Ready (${restoredState.selectorMode.toUpperCase()} mode)`;
                    }
                }
                
                // Restore visual overlays after a brief delay to ensure page is loaded
                setTimeout(() => {
                    VisualManager.restoreVisuals();
                }, 1000);
            } else {
                // Activate default tool
                ElementTool.activate();
            }
            
            // Set up navigation state saving on page unload
            this.setupNavigationStateSaving();
            
            // Test Python callback functions
            this.testPythonCallbacks();
            
            console.log("✅ Interactive Scraper initialized successfully");
        }
        
        setupNavigationStateSaving() {
            // Save state before page navigation
            window.addEventListener('beforeunload', () => {
                NavigationState.save(ScraperState);
            });
            
            // Also save state periodically
            setInterval(() => {
                if (ScraperState.selectedElements.length > 0 || 
                    ScraperState.containers.length > 0 || 
                    ScraperState.actions.length > 0) {
                    NavigationState.save(ScraperState);
                }
            }, 10000); // Save every 10 seconds if there's data
        }
        
        handleStateChange(newState, oldState) {
            // Update UI when state changes
            ControlPanel.updateDisplay();
        }
        
        testPythonCallbacks() {
            const callbacks = ['save_template_py', 'add_element_py', 'add_action_py', 'log_message_py', 'navigate_to_py'];
            const available = callbacks.filter(cb => typeof window[cb] === 'function');
            
            console.log(`✅ Python callbacks available: ${available.join(', ')}`);
            
            if (typeof window.log_message_py === 'function') {
                window.log_message_py("Interactive overlay initialized successfully");
            }
        }
    }
    
    // Initialize when DOM is ready
    function initializeScraper() {
        new InteractiveScraper();
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeScraper);
    } else {
        initializeScraper();
    }
    
    console.log("🕷️ Interactive Scraper overlay ready!");

})();