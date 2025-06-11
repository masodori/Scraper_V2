/**
 * Element Selection Tool
 */

import { BaseTool } from './base-tool.js';
import { ModalManager } from '../ui/modal-manager.js';
import { generateOptimalSelector, determineElementType } from '../selectors/selector-generator.js';
import { markElementAsSelected, isControlPanelElement } from '../utils/dom-utils.js';

export class ElementTool extends BaseTool {
    constructor(stateManager, eventManager, statusManager) {
        super('element', stateManager, eventManager, statusManager);
        this.setupEventListeners();
    }
    
    async handleClick(event) {
        if (!this.stateManager.getState().isSelectionMode || isControlPanelElement(event.target)) {
            return;
        }
        
        event.preventDefault();
        event.stopPropagation();
        
        const element = event.target;
        this.stopSelection();
        element.classList.remove('scraper-highlight');
        
        try {
            const label = await ModalManager.prompt('Element Label', 'Enter a label for this element:');
            
            if (!label || label.trim() === '') {
                this.statusManager.setErrorStatus('Label is required');
                return;
            }
            
            // Check for duplicate labels
            const existingLabels = this.stateManager.getState().selectedElements.map(el => el.label);
            if (existingLabels.includes(label.trim())) {
                await ModalManager.alert('An element with this label already exists. Please choose a different label.');
                return;
            }
            
            const selector = generateOptimalSelector(element);
            const elementType = determineElementType(element);
            
            const elementData = {
                label: label.trim(),
                selector: selector,
                selector_type: 'css',
                element_type: elementType,
                attribute_name: elementType === 'attribute' ? this.getAttributeName(element) : null,
                is_multiple: false,
                is_required: true,
                is_container: false,
                use_find_similar: false,
                sub_elements: [],
                follow_links: false,
                subpage_elements: []
            };
            
            // Add to state
            this.stateManager.addElement(elementData);
            
            // Mark element visually
            markElementAsSelected(element, label.trim());
            
            this.statusManager.setSuccessStatus(`Element "${label.trim()}" added successfully`);
            
            console.log(`✅ Element added: ${label.trim()} -> ${selector}`);
            
        } catch (error) {
            console.error('❌ Error adding element:', error);
            this.statusManager.setErrorStatus('Failed to add element');
        }
    }
    
    getAttributeName(element) {
        const tagName = element.tagName.toLowerCase();
        if (tagName === 'img') return 'src';
        if (tagName === 'input' || tagName === 'textarea') return 'value';
        if (tagName === 'a') return 'href';
        return null;
    }
}