/**
 * Control Panel UI Component
 */

export class ControlPanel {
    constructor(stateManager, eventManager, statusManager) {
        this.stateManager = stateManager;
        this.eventManager = eventManager;
        this.statusManager = statusManager;
        this.panel = null;
    }
    
    create() {
        const panel = document.createElement('div');
        panel.className = 'scraper-control-panel';
        panel.innerHTML = `
            <div class="scraper-panel-header">
                <h3 class="scraper-panel-title">🕷️ Interactive Scraper</h3>
                <button class="scraper-minimize-btn" id="toggle-panel-btn">−</button>
            </div>
            <div class="scraper-panel-body" id="scraper-panel-body">
                <div class="scraper-tool-selector">
                    <button class="scraper-tool-btn active" data-tool="element">
                        📌 Element
                    </button>
                    <button class="scraper-tool-btn" data-tool="action">
                        🔗 Action
                    </button>
                    <button class="scraper-tool-btn" data-tool="scroll">
                        📜 Scroll
                    </button>
                    <button class="scraper-tool-btn" data-tool="container">
                        📦 Container
                    </button>
                </div>
                
                <div class="scraper-status">
                    <div id="scraper-mode-indicator">
                        📌 Click on elements to tag them for scraping
                    </div>
                </div>
                
                <div id="scraper-element-section">
                    <div class="scraper-element-list" id="selected-elements">
                        <!-- Selected elements will appear here -->
                    </div>
                    <button class="scraper-action-btn" id="start-element-btn">
                        📌 Select Element
                    </button>
                    <button class="scraper-action-btn scraper-secondary-btn" id="clear-elements-btn">
                        🗑️ Clear Elements
                    </button>
                </div>
                
                <div id="scraper-action-section" style="display: none;">
                    <div class="scraper-element-list" id="selected-actions">
                        <!-- Selected actions will appear here -->
                    </div>
                    <button class="scraper-action-btn" id="start-action-btn">
                        🔗 Select Action
                    </button>
                    <button class="scraper-action-btn scraper-secondary-btn" id="clear-actions-btn">
                        🗑️ Clear Actions
                    </button>
                </div>
                
                <div id="scraper-scroll-section" style="display: none;">
                    <div class="scraper-element-list" id="scroll-config">
                        <!-- Scroll configuration will appear here -->
                    </div>
                    <button class="scraper-action-btn" id="detect-scroll-btn">
                        🔍 Auto-Detect Scroll
                    </button>
                    <button class="scraper-action-btn" id="add-load-more-btn">
                        ➕ Load More Button
                    </button>
                    <button class="scraper-action-btn" id="add-infinite-scroll-btn">
                        📜 Infinite Scroll
                    </button>
                    <button class="scraper-action-btn scraper-secondary-btn" id="clear-scroll-btn">
                        🗑️ Clear Scroll
                    </button>
                </div>
                
                <div id="scraper-container-section" style="display: none;">
                    <div class="scraper-element-list" id="selected-containers">
                        <!-- Selected containers will appear here -->
                    </div>
                    <button class="scraper-action-btn" id="start-container-btn">
                        📦 Select Container
                    </button>
                    <button class="scraper-action-btn" id="add-sub-element-btn" style="display: none;">
                        ➕ Add Sub-Element
                    </button>
                    <button class="scraper-action-btn scraper-secondary-btn" id="clear-containers-btn">
                        🗑️ Clear Containers
                    </button>
                </div>
                
                <div style="margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                    <button class="scraper-action-btn" id="save-template-btn" style="background: linear-gradient(45deg, #4ecdc4, #44a08d);">
                        💾 Save Template
                    </button>
                    <button class="scraper-action-btn scraper-secondary-btn" id="preview-template-btn">
                        👁️ Preview Template
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
        this.panel = panel;
        this.stateManager.setControlPanel(panel);
        
        // Initialize status manager
        this.statusManager.initialize();
        
        console.log("✅ Control panel created");
        return panel;
    }
    
    showSection(sectionName) {
        // Hide all sections
        const sections = ['element', 'action', 'scroll', 'container'];
        sections.forEach(section => {
            const element = document.getElementById(`scraper-${section}-section`);
            if (element) {
                element.style.display = 'none';
            }
        });
        
        // Show selected section
        const targetSection = document.getElementById(`scraper-${sectionName}-section`);
        if (targetSection) {
            targetSection.style.display = 'block';
        }
        
        // Update tool button states
        document.querySelectorAll('.scraper-tool-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.tool === sectionName) {
                btn.classList.add('active');
            }
        });
    }
    
    updateElementsList(elements) {
        const container = document.getElementById('selected-elements');
        if (!container) return;
        
        container.innerHTML = '';
        
        elements.forEach((element, index) => {
            const item = document.createElement('div');
            item.className = 'scraper-element-item';
            item.innerHTML = `
                <div>
                    <div class="scraper-element-label">${element.label}</div>
                    <div class="scraper-element-selector">${element.selector}</div>
                </div>
                <button class="remove-element-btn" data-index="${index}" style="background: #ff6b6b; border: none; color: white; border-radius: 3px; padding: 2px 6px; cursor: pointer;">×</button>
            `;
            container.appendChild(item);
        });
        
        if (elements.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: rgba(255,255,255,0.6); font-size: 12px; padding: 20px;">No elements selected yet</div>';
        }
    }
    
    updateActionsList(actions) {
        const container = document.getElementById('selected-actions');
        if (!container) return;
        
        container.innerHTML = '';
        
        actions.forEach((action, index) => {
            const item = document.createElement('div');
            item.className = 'scraper-element-item';
            
            const hasUrl = action.target_url && action.target_url !== window.location.href;
            const urlDisplay = hasUrl ? `<div style="font-size: 10px; color: rgba(255,255,255,0.5); margin-top: 2px;">→ ${action.target_url}</div>` : '';
            const navigateButton = hasUrl ? `<button class="navigate-action-btn" data-index="${index}" style="background: #4ecdc4; border: none; color: white; border-radius: 3px; padding: 2px 6px; cursor: pointer; margin-right: 5px; font-size: 10px;">Go</button>` : '';
            
            item.innerHTML = `
                <div style="flex: 1;">
                    <div class="scraper-element-label">⚡ ${action.label}</div>
                    <div class="scraper-element-selector">${action.selector}</div>
                    ${urlDisplay}
                </div>
                <div style="display: flex; align-items: center;">
                    ${navigateButton}
                    <button class="remove-action-btn" data-index="${index}" style="background: #ff6b6b; border: none; color: white; border-radius: 3px; padding: 2px 6px; cursor: pointer;">×</button>
                </div>
            `;
            container.appendChild(item);
        });
        
        if (actions.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: rgba(255,255,255,0.6); font-size: 12px; padding: 20px;">No actions selected yet</div>';
        }
    }
    
    updateContainersList(containers) {
        const container = document.getElementById('selected-containers');
        if (!container) return;
        
        container.innerHTML = '';
        
        containers.forEach((containerData, index) => {
            const item = document.createElement('div');
            item.className = 'scraper-element-item';
            
            const subElementsCount = containerData.sub_elements ? containerData.sub_elements.length : 0;
            const subElementsText = subElementsCount > 0 ? `${subElementsCount} sub-elements` : 'No sub-elements';
            
            item.innerHTML = `
                <div>
                    <div class="scraper-element-label">📦 ${containerData.label}</div>
                    <div class="scraper-element-selector">${containerData.selector}</div>
                    <div style="font-size: 10px; color: rgba(255,255,255,0.5); margin-top: 2px;">${subElementsText}</div>
                </div>
                <button class="remove-container-btn" data-index="${index}" style="background: #ff6b6b; border: none; color: white; border-radius: 3px; padding: 2px 6px; cursor: pointer;">×</button>
            `;
            container.appendChild(item);
        });
        
        if (containers.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: rgba(255,255,255,0.6); font-size: 12px; padding: 20px;">No containers selected yet</div>';
        }
        
        // Show/hide add sub-element button
        const addSubBtn = document.getElementById('add-sub-element-btn');
        if (addSubBtn) {
            addSubBtn.style.display = containers.length > 0 ? 'block' : 'none';
        }
    }
    
    updateScrollDisplay(scrollConfig) {
        const container = document.getElementById('scroll-config');
        if (!container) return;
        
        if (!scrollConfig) {
            container.innerHTML = '<div style="text-align: center; color: rgba(255,255,255,0.6); font-size: 12px; padding: 20px;">No scroll configuration</div>';
            return;
        }
        
        const item = document.createElement('div');
        item.className = 'scraper-element-item';
        
        let configDetails = '';
        if (scrollConfig.pattern_type === 'load_more') {
            configDetails = `Load More Button: ${scrollConfig.load_more_selector}`;
            if (scrollConfig.max_pages) {
                configDetails += `\\nMax clicks: ${scrollConfig.max_pages}`;
            }
        } else if (scrollConfig.pattern_type === 'infinite_scroll') {
            configDetails = `Infinite Scroll\\nPause: ${scrollConfig.scroll_pause_time}s`;
        } else if (scrollConfig.pattern_type === 'button') {
            configDetails = `Next Button: ${scrollConfig.next_selector}`;
        }
        
        item.innerHTML = `
            <div>
                <div class="scraper-element-label">🔄 ${scrollConfig.pattern_type}</div>
                <div class="scraper-element-selector">${configDetails}</div>
            </div>
            <button class="remove-scroll-btn" style="background: #ff6b6b; border: none; color: white; border-radius: 3px; padding: 2px 6px; cursor: pointer;">×</button>
        `;
        
        container.innerHTML = '';
        container.appendChild(item);
    }
    
    toggle() {
        const body = document.getElementById('scraper-panel-body');
        const btn = document.getElementById('toggle-panel-btn');
        
        if (body && btn) {
            if (body.style.display === 'none') {
                body.style.display = 'block';
                btn.textContent = '−';
                console.log("✅ Panel expanded");
            } else {
                body.style.display = 'none';
                btn.textContent = '+';
                console.log("✅ Panel minimized");
            }
        }
    }
}