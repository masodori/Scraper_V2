/**
 * Container Selection Tool
 */

import { BaseTool } from './base-tool.js';
import { ModalManager } from '../ui/modal-manager.js';
import { generateOptimalSelector, determineElementType } from '../selectors/selector-generator.js';
import { markElementAsContainer, markElementAsSubElement, isControlPanelElement } from '../utils/dom-utils.js';

export class ContainerTool extends BaseTool {
    constructor(stateManager, eventManager, statusManager) {
        super('container', stateManager, eventManager, statusManager);
        this.setupEventListeners();
    }
    
    async handleClick(event) {
        if (!this.stateManager.getState().isSelectionMode || isControlPanelElement(event.target)) {
            return;
        }
        
        event.preventDefault();
        event.stopPropagation();
        
        const element = event.target;
        const state = this.stateManager.getState();
        
        // Check if we're selecting a sub-element within a container
        if (state.selectingSubElement && state.currentContainer) {
            await this.handleSubElementSelection(element);
            return;
        }
        
        // Regular container selection
        await this.handleContainerSelection(element);
    }
    
    async handleContainerSelection(element) {
        this.stopSelection();
        element.classList.remove('scraper-highlight');
        
        try {
            const label = await ModalManager.prompt('Container Label', 'Enter a label for this container:');
            
            if (!label || label.trim() === '') {
                this.statusManager.setErrorStatus('Label is required');
                return;
            }
            
            // Check for duplicate labels
            const existingLabels = this.stateManager.getState().containers.map(container => container.label);
            if (existingLabels.includes(label.trim())) {
                await ModalManager.alert('A container with this label already exists. Please choose a different label.');
                return;
            }
            
            const selector = generateOptimalSelector(element);
            
            // Find similar elements
            const similarElements = document.querySelectorAll(selector);
            
            const confirmed = await ModalManager.confirm(
                'Container Confirmation',
                `Found ${similarElements.length} similar elements. Continue with this container pattern?`
            );
            
            if (!confirmed) {
                return;
            }
            
            const containerData = {
                label: label.trim(),
                selector: selector,
                selector_type: 'css',
                element_type: 'container',
                attribute_name: null,
                is_multiple: true,
                is_required: true,
                is_container: true,
                use_find_similar: true,
                sub_elements: [],
                follow_links: false,
                subpage_elements: []
            };
            
            // Add to state
            this.stateManager.addContainer(containerData);
            this.stateManager.setState({ currentContainer: containerData });
            
            // Mark all similar elements visually
            similarElements.forEach(el => markElementAsContainer(el));
            
            this.statusManager.setSuccessStatus(`Container "${label.trim()}" added. Now add sub-elements by clicking inside containers.`);
            
            console.log(`✅ Container added: ${label.trim()} -> ${selector} (${similarElements.length} instances)`);
            
        } catch (error) {
            console.error('❌ Error adding container:', error);
            this.statusManager.setErrorStatus('Failed to add container');
        }
    }
    
    async handleSubElementSelection(element) {
        this.stopSelection();
        element.classList.remove('scraper-highlight');
        
        try {
            const label = await ModalManager.prompt('Sub-Element Label', 'Enter a label for this sub-element:');
            
            if (!label || label.trim() === '') {
                this.statusManager.setErrorStatus('Label is required');
                return;
            }
            
            const selector = generateOptimalSelector(element);
            const elementType = determineElementType(element);
            
            const subElementData = {
                label: label.trim(),
                selector: selector,
                element_type: elementType,
                attribute_name: elementType === 'attribute' ? this.getAttributeName(element) : null,
                is_required: true
            };
            
            // Add to current container
            const state = this.stateManager.getState();
            const containers = [...state.containers];
            const currentContainerIndex = containers.findIndex(c => c.label === state.currentContainer.label);
            
            if (currentContainerIndex >= 0) {
                containers[currentContainerIndex].sub_elements.push(subElementData);
                this.stateManager.setState({ containers });
            }
            
            // Mark element visually
            markElementAsSubElement(element, label.trim());
            
            this.statusManager.setSuccessStatus(`Sub-element "${label.trim()}" added to container`);
            
            console.log(`✅ Sub-element added: ${label.trim()} -> ${selector}`);
            
        } catch (error) {
            console.error('❌ Error adding sub-element:', error);
            this.statusManager.setErrorStatus('Failed to add sub-element');
        }
    }
    
    startSubElementSelection() {
        const state = this.stateManager.getState();
        if (!state.currentContainer) {
            this.statusManager.setErrorStatus('Please select a container first');
            return;
        }
        
        this.stateManager.setState({ selectingSubElement: true });
        this.startSelection();
        this.statusManager.setSelectionStatus('Click inside containers to add sub-elements');
    }
    
    getAttributeName(element) {
        const tagName = element.tagName.toLowerCase();
        if (tagName === 'img') return 'src';
        if (tagName === 'input' || tagName === 'textarea') return 'value';
        if (tagName === 'a') return 'href';
        return null;
    }
}