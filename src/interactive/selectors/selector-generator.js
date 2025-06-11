/**
 * CSS Selector Generation Utilities
 */

export function generateOptimalSelector(element) {
    // Try different selector strategies in order of preference
    
    // 1. ID selector (most reliable)
    if (element.id && document.querySelectorAll('#' + element.id).length === 1) {
        return '#' + element.id;
    }
    
    // 2. Class selector (if unique)
    if (element.className) {
        const classes = element.className.split(' ').filter(c => c.trim() !== '');
        for (const cls of classes) {
            const selector = '.' + cls;
            if (document.querySelectorAll(selector).length === 1) {
                return selector;
            }
        }
        
        // Try combination of classes
        if (classes.length > 1) {
            const selector = '.' + classes.join('.');
            if (document.querySelectorAll(selector).length === 1) {
                return selector;
            }
        }
    }
    
    // 3. Attribute selectors
    const attributes = ['data-testid', 'data-cy', 'data-test', 'aria-label', 'name'];
    for (const attr of attributes) {
        const value = element.getAttribute(attr);
        if (value) {
            const selector = `[${attr}="${value}"]`;
            if (document.querySelectorAll(selector).length === 1) {
                return selector;
            }
        }
    }
    
    // 4. Text-based selectors for links and buttons
    if (element.tagName === 'A' || element.tagName === 'BUTTON') {
        const text = element.textContent.trim();
        if (text && text.length < 50) {
            const selector = `${element.tagName.toLowerCase()}:contains("${text}")`;
            // Note: :contains is not standard CSS, but many tools support it
            return selector;
        }
    }
    
    // 5. nth-child selector (fallback)
    return generateNthChildSelector(element);
}

export function generateNthChildSelector(element) {
    const path = [];
    let current = element;
    
    while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.body) {
        let selector = current.tagName.toLowerCase();
        
        if (current.id) {
            selector += '#' + current.id;
            path.unshift(selector);
            break;
        }
        
        const parent = current.parentElement;
        if (parent) {
            const siblings = Array.from(parent.children);
            const index = siblings.indexOf(current) + 1;
            selector += `:nth-child(${index})`;
        }
        
        path.unshift(selector);
        current = parent;
    }
    
    return path.join(' > ');
}

export function determineElementType(element) {
    const tagName = element.tagName.toLowerCase();
    
    if (tagName === 'a') return 'link';
    if (tagName === 'img') return 'attribute'; // Will extract src
    if (tagName === 'input' || tagName === 'textarea') return 'attribute'; // Will extract value
    
    return 'text'; // Default to text content
}

export function determineActionType(element) {
    const tagName = element.tagName.toLowerCase();
    
    if (tagName === 'button' || tagName === 'a' || element.getAttribute('role') === 'button') {
        return 'click';
    }
    
    return 'click'; // Default to click
}