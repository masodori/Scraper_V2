/**
 * Base Tool Class for Interactive Tools
 */

import { highlightElement, removeHighlight, isControlPanelElement } from '../utils/dom-utils.js';

export class BaseTool {
    constructor(name, stateManager, eventManager, statusManager) {
        this.name = name;
        this.stateManager = stateManager;
        this.eventManager = eventManager;
        this.statusManager = statusManager;
        this.isActive = false;
    }
    
    activate() {
        this.isActive = true;
        this.stateManager.setCurrentTool(this.name);
        this.statusManager.setToolStatus(this.name);
        console.log(`🔧 ${this.name} tool activated`);
    }
    
    deactivate() {
        this.isActive = false;
        this.stateManager.setSelectionMode(false);
        document.body.style.cursor = '';
        console.log(`🔧 ${this.name} tool deactivated`);
    }
    
    startSelection() {
        if (!this.isActive) return;
        
        this.stateManager.setSelectionMode(true);
        document.body.style.cursor = 'crosshair';
        this.statusManager.setSelectionStatus(`${this.name} selection mode active - click to select`);
    }
    
    stopSelection() {
        this.stateManager.setSelectionMode(false);
        document.body.style.cursor = '';
    }
    
    handleMouseOver(event) {
        if (!this.stateManager.getState().isSelectionMode || isControlPanelElement(event.target)) {
            return;
        }
        
        highlightElement(event.target);
        this.stateManager.setHighlightedElement(event.target);
    }
    
    handleMouseOut(event) {
        if (!this.stateManager.getState().isSelectionMode) {
            return;
        }
        
        removeHighlight(event.target);
        if (this.stateManager.getState().highlightedElement === event.target) {
            this.stateManager.setHighlightedElement(null);
        }
    }
    
    handleClick(event) {
        // Override in subclasses
        console.log(`${this.name} tool click handler not implemented`);
    }
    
    setupEventListeners() {
        this.eventManager.on('element-mouseover', this.handleMouseOver.bind(this));
        this.eventManager.on('element-mouseout', this.handleMouseOut.bind(this));
        this.eventManager.on('element-click', this.handleClick.bind(this));
    }
}