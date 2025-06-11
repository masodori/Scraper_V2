/**
 * Status Management for UI Updates
 */

export class StatusManager {
    constructor() {
        this.statusElement = null;
    }
    
    initialize() {
        this.statusElement = document.getElementById('scraper-mode-indicator');
    }
    
    updateStatus(message) {
        if (this.statusElement) {
            this.statusElement.textContent = message;
        }
        console.log(`📱 Status: ${message}`);
    }
    
    setToolStatus(toolName) {
        const statusMessages = {
            'element': '📌 Click on elements to tag them for scraping',
            'action': '🔗 Click on buttons/links to define actions',
            'scroll': '📜 Configure scroll/pagination patterns',
            'container': '📦 Click on repeating containers for bulk extraction'
        };
        
        this.updateStatus(statusMessages[toolName] || `${toolName} tool selected`);
    }
    
    setSelectionStatus(message) {
        this.updateStatus(`🎯 ${message}`);
    }
    
    setSuccessStatus(message) {
        this.updateStatus(`✅ ${message}`);
    }
    
    setErrorStatus(message) {
        this.updateStatus(`❌ ${message}`);
    }
}