/**
 * Centralized State Management for Interactive Scraper
 */

export class StateManager {
    constructor() {
        this.state = {
            isSelectionMode: false,
            selectedElements: [],
            containers: [],
            actions: [],
            currentTool: 'element',
            scrollConfig: null,
            currentContainer: null,
            currentContainerElements: [],
            pageNavigationState: null,
            highlightedElement: null,
            overlay: null,
            controlPanel: null,
            selectingSubElement: false,
            selectingForSubpage: false,
            currentContainerElement: null,
            paginationConfig: null,
            selectingPaginationType: null,
            selectingScrollType: null
        };
        this.listeners = [];
    }
    
    setState(updates) {
        const oldState = { ...this.state };
        this.state = { ...this.state, ...updates };
        
        // Notify listeners of state changes
        this.notifyListeners(oldState, this.state);
        
        console.log(`🔄 State updated:`, Object.keys(updates));
    }
    
    getState() {
        return { ...this.state };
    }
    
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            const index = this.listeners.indexOf(listener);
            if (index > -1) {
                this.listeners.splice(index, 1);
            }
        };
    }
    
    notifyListeners(oldState, newState) {
        this.listeners.forEach(listener => {
            try {
                listener(newState, oldState);
            } catch (error) {
                console.error('State listener error:', error);
            }
        });
    }
    
    // Convenience methods for common state operations
    setSelectionMode(isActive) {
        this.setState({ isSelectionMode: isActive });
    }
    
    addElement(element) {
        const elements = [...this.state.selectedElements, element];
        this.setState({ selectedElements: elements });
    }
    
    removeElement(index) {
        const elements = this.state.selectedElements.filter((_, i) => i !== index);
        this.setState({ selectedElements: elements });
    }
    
    clearElements() {
        this.setState({ selectedElements: [] });
    }
    
    addContainer(container) {
        const containers = [...this.state.containers, container];
        this.setState({ containers: containers });
    }
    
    clearContainers() {
        this.setState({ containers: [] });
    }
    
    addAction(action) {
        const actions = [...this.state.actions, action];
        this.setState({ actions: actions });
    }
    
    clearActions() {
        this.setState({ actions: [] });
    }
    
    setCurrentTool(tool) {
        this.setState({ currentTool: tool });
    }
    
    setHighlightedElement(element) {
        this.setState({ highlightedElement: element });
    }
    
    setControlPanel(panel) {
        this.setState({ controlPanel: panel });
    }
}