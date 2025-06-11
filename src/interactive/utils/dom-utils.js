/**
 * DOM Utility Functions
 */

export function isControlPanelElement(element) {
    return element.closest('.scraper-control-panel') !== null || element.closest('.scraper-modal') !== null;
}

export function removeElementVisuals(element) {
    const domElements = document.querySelectorAll('.scraper-selected');
    domElements.forEach(el => {
        if (el.getAttribute('data-scraper-label') === element.label) {
            el.classList.remove('scraper-selected');
            el.removeAttribute('data-scraper-label');
        }
    });
}

export function removeActionVisuals(action) {
    const domElements = document.querySelectorAll('.scraper-action-element');
    domElements.forEach(el => {
        if (el.getAttribute('data-scraper-action') === action.label) {
            el.classList.remove('scraper-action-element');
            el.removeAttribute('data-scraper-action');
        }
    });
}

export function clearAllVisuals() {
    // Remove all visual feedback
    document.querySelectorAll('.scraper-selected').forEach(el => {
        el.classList.remove('scraper-selected');
        el.removeAttribute('data-scraper-label');
    });
    
    document.querySelectorAll('.scraper-action-element').forEach(el => {
        el.classList.remove('scraper-action-element');
        el.removeAttribute('data-scraper-action');
    });
    
    document.querySelectorAll('.scraper-highlight').forEach(el => {
        el.classList.remove('scraper-highlight');
    });
    
    document.querySelectorAll('.scraper-container-context').forEach(el => {
        el.classList.remove('scraper-container-context');
    });
    
    document.querySelectorAll('.scraper-sub-element').forEach(el => {
        el.classList.remove('scraper-sub-element');
        el.removeAttribute('data-sub-label');
    });
}

export function highlightElement(element) {
    // Remove previous highlights
    document.querySelectorAll('.scraper-highlight').forEach(el => {
        el.classList.remove('scraper-highlight');
    });
    
    // Add highlight to current element
    if (element && !isControlPanelElement(element)) {
        element.classList.add('scraper-highlight');
    }
}

export function removeHighlight(element) {
    if (element) {
        element.classList.remove('scraper-highlight');
    }
}

export function markElementAsSelected(element, label) {
    element.classList.add('scraper-selected');
    element.setAttribute('data-scraper-label', label);
}

export function markElementAsAction(element, label) {
    element.classList.add('scraper-action-element');
    element.setAttribute('data-scraper-action', label);
}

export function markElementAsContainer(element) {
    element.classList.add('scraper-container-context');
}

export function markElementAsSubElement(element, label) {
    element.classList.add('scraper-sub-element');
    element.setAttribute('data-sub-label', label);
}