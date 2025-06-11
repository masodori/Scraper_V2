/**
 * Configuration constants for the Interactive Scraper
 */

export const CONFIG = {
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