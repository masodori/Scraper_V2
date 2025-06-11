/**
 * Scroll/Pagination Tool
 */

import { BaseTool } from './base-tool.js';
import { ModalManager } from '../ui/modal-manager.js';
import { generateOptimalSelector } from '../selectors/selector-generator.js';
import { isControlPanelElement } from '../utils/dom-utils.js';

export class ScrollTool extends BaseTool {
    constructor(stateManager, eventManager, statusManager) {
        super('scroll', stateManager, eventManager, statusManager);
        this.setupEventListeners();
    }
    
    async handleClick(event) {
        const state = this.stateManager.getState();
        
        if (!state.isSelectionMode || isControlPanelElement(event.target)) {
            return;
        }
        
        event.preventDefault();
        event.stopPropagation();
        
        const element = event.target;
        
        if (state.selectingScrollType === 'load_more') {
            await this.handleLoadMoreSelection(element);
        }
    }
    
    async handleLoadMoreSelection(element) {
        this.stopSelection();
        element.classList.remove('scraper-highlight');
        
        try {
            const elementText = element.textContent.trim();
            const selector = generateOptimalSelector(element);
            
            const maxClicks = await ModalManager.prompt(
                'Load More Configuration',
                `Selected: "${elementText}"\\n\\nMaximum clicks (enter number or leave blank for unlimited):`
            );
            
            const config = {
                pattern_type: 'load_more',
                load_more_selector: selector,
                max_pages: (maxClicks && !isNaN(maxClicks)) ? parseInt(maxClicks) : null
            };
            
            this.stateManager.setState({ 
                scrollConfig: config,
                selectingScrollType: null
            });
            
            await ModalManager.alert(`Scroll button configured!\\n\\nElement: "${elementText}"\\nThis will enable scraping ALL data, not just the current page.`);
            
            this.statusManager.setSuccessStatus('Load More button configured');
            
        } catch (error) {
            console.error('❌ Error selecting scroll element:', error);
            this.statusManager.setErrorStatus('Failed to configure scroll');
        }
    }
    
    async addLoadMoreButton() {
        this.statusManager.setSelectionStatus('Click on the "Load More" or "Show More" button');
        this.stateManager.setState({ 
            isSelectionMode: true,
            selectingScrollType: 'load_more'
        });
        document.body.style.cursor = 'crosshair';
    }
    
    async addInfiniteScroll() {
        try {
            const pauseTime = await ModalManager.prompt(
                'Infinite Scroll Configuration',
                'Pause time between scrolls (seconds, default 2):'
            );
            
            const scrollPause = (pauseTime && !isNaN(pauseTime)) ? parseFloat(pauseTime) : 2.0;
            
            this.stateManager.setState({
                scrollConfig: {
                    pattern_type: 'infinite_scroll',
                    scroll_pause_time: scrollPause,
                    end_condition_selector: null
                }
            });
            
            await ModalManager.alert('Infinite scroll configured!\\n\\nThis will automatically scroll to load all content during scraping.');
            this.statusManager.setSuccessStatus('Infinite scroll configured');
            
        } catch (error) {
            console.error('❌ Error adding infinite scroll:', error);
            this.statusManager.setErrorStatus('Failed to configure infinite scroll');
        }
    }
    
    autoDetectScroll() {
        console.log("🔍 Auto-detecting scroll patterns...");
        
        try {
            const detectedPatterns = [];
            
            // Simple text search for load more buttons
            const buttons = document.querySelectorAll('button, a');
            buttons.forEach(el => {
                const text = el.textContent.toLowerCase();
                if (text.includes('load') || text.includes('more') || text.includes('show')) {
                    detectedPatterns.push({
                        type: 'load_more',
                        element: el,
                        selector: generateOptimalSelector(el),
                        text: el.textContent.trim()
                    });
                }
            });
            
            if (detectedPatterns.length === 0) {
                ModalManager.alert('No scroll patterns detected on this page.\\n\\nTry manually adding scroll configuration using the buttons below.');
                return;
            }
            
            // Use first detected pattern
            if (detectedPatterns.length > 0) {
                this.configureDetectedPattern(detectedPatterns[0]);
            }
            
        } catch (error) {
            console.error('❌ Error detecting scroll:', error);
            ModalManager.alert('Error detecting scroll patterns. Try manual configuration.');
        }
    }
    
    async configureDetectedPattern(pattern) {
        try {
            const config = {
                pattern_type: pattern.type,
                selector: pattern.selector,
                max_pages: null,
                scroll_pause_time: 2.0,
                end_condition_selector: null
            };
            
            if (pattern.type === 'load_more') {
                const maxClicks = await ModalManager.prompt(
                    'Load More Configuration',
                    'Maximum clicks (enter number or leave blank for unlimited):'
                );
                
                if (maxClicks && !isNaN(maxClicks)) {
                    config.max_pages = parseInt(maxClicks);
                }
                
                config.load_more_selector = pattern.selector;
            }
            
            this.stateManager.setState({ scrollConfig: config });
            
            await ModalManager.alert(`Scroll configured!\\n\\nType: ${pattern.type}\\nThis will scrape ALL available data, not just what's currently visible.`);
            this.statusManager.setSuccessStatus('Auto-detected scroll pattern configured');
            
        } catch (error) {
            console.error('❌ Error configuring scroll:', error);
            this.statusManager.setErrorStatus('Failed to configure detected scroll pattern');
        }
    }
    
    clearScroll() {
        this.stateManager.setState({ scrollConfig: null });
        this.statusManager.setSuccessStatus('Scroll configuration cleared');
    }
}