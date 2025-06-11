/**
 * Centralized Event Management System
 */

export class EventManager {
    constructor() {
        this.handlers = new Map();
        this.delegatedEvents = new Set();
    }
    
    on(event, handler) {
        if (!this.handlers.has(event)) {
            this.handlers.set(event, []);
        }
        this.handlers.get(event).push(handler);
    }
    
    off(event, handler) {
        if (this.handlers.has(event)) {
            const handlers = this.handlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        const handlers = this.handlers.get(event) || [];
        handlers.forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`Event handler error for ${event}:`, error);
            }
        });
    }
    
    setupDelegation() {
        // Set up delegated event handlers to avoid duplicate listeners
        if (!this.delegatedEvents.has('click')) {
            document.addEventListener('click', this.handleDelegatedClick.bind(this), true);
            this.delegatedEvents.add('click');
        }
        
        if (!this.delegatedEvents.has('mouseover')) {
            document.addEventListener('mouseover', this.handleDelegatedMouseOver.bind(this), true);
            this.delegatedEvents.add('mouseover');
        }
        
        if (!this.delegatedEvents.has('mouseout')) {
            document.addEventListener('mouseout', this.handleDelegatedMouseOut.bind(this), true);
            this.delegatedEvents.add('mouseout');
        }
    }
    
    handleDelegatedClick(event) {
        this.emit('element-click', event);
    }
    
    handleDelegatedMouseOver(event) {
        this.emit('element-mouseover', event);
    }
    
    handleDelegatedMouseOut(event) {
        this.emit('element-mouseout', event);
    }
    
    attachButtonHandler(buttonId, handler) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', handler);
            return true;
        }
        return false;
    }
    
    attachMultipleHandlers(handlers) {
        const results = {};
        for (const [buttonId, handler] of Object.entries(handlers)) {
            results[buttonId] = this.attachButtonHandler(buttonId, handler);
        }
        return results;
    }
}