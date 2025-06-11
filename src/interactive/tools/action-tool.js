/**
 * Action Selection Tool
 */

import { BaseTool } from './base-tool.js';
import { ModalManager } from '../ui/modal-manager.js';
import { generateOptimalSelector, determineActionType } from '../selectors/selector-generator.js';
import { markElementAsAction, isControlPanelElement } from '../utils/dom-utils.js';

export class ActionTool extends BaseTool {
    constructor(stateManager, eventManager, statusManager) {
        super('action', stateManager, eventManager, statusManager);
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
            const label = await ModalManager.prompt('Action Label', 'Enter a label for this action:');
            
            if (!label || label.trim() === '') {
                this.statusManager.setErrorStatus('Label is required');
                return;
            }
            
            // Check for duplicate labels
            const existingLabels = this.stateManager.getState().actions.map(action => action.label);
            if (existingLabels.includes(label.trim())) {
                await ModalManager.alert('An action with this label already exists. Please choose a different label.');
                return;
            }
            
            const selector = generateOptimalSelector(element);
            const actionType = determineActionType(element);
            
            // Determine target URL for navigation
            let targetUrl = window.location.href;
            if (element.tagName.toLowerCase() === 'a' && element.href) {
                targetUrl = element.href;
            }
            
            const actionData = {
                label: label.trim(),
                selector: selector,
                action_type: actionType,
                target_url: targetUrl,
                wait_after: 2.0,
                required: true
            };
            
            // Add to state
            this.stateManager.addAction(actionData);
            
            // Mark element visually
            markElementAsAction(element, label.trim());
            
            this.statusManager.setSuccessStatus(`Action "${label.trim()}" added successfully`);
            
            console.log(`✅ Action added: ${label.trim()} -> ${selector}`);
            
        } catch (error) {
            console.error('❌ Error adding action:', error);
            this.statusManager.setErrorStatus('Failed to add action');
        }
    }
}