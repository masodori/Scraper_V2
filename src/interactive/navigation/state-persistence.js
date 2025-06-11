/**
 * Navigation State Persistence
 */

export function saveNavigationState(state) {
    try {
        const navigationState = {
            selectedElements: state.selectedElements,
            containers: state.containers,
            actions: state.actions,
            scrollConfig: state.scrollConfig,
            currentTool: state.currentTool,
            currentContainer: state.currentContainer,
            timestamp: Date.now()
        };
        
        sessionStorage.setItem('scraperNavigationState', JSON.stringify(navigationState));
        console.log("💾 Navigation state saved");
        
    } catch (error) {
        console.error("❌ Error saving navigation state:", error);
    }
}

export function restoreNavigationState() {
    try {
        const savedState = sessionStorage.getItem('scraperNavigationState');
        if (!savedState) return null;
        
        const state = JSON.parse(savedState);
        
        // Check if state is recent (within last 5 minutes)
        if (Date.now() - state.timestamp > 5 * 60 * 1000) {
            sessionStorage.removeItem('scraperNavigationState');
            return null;
        }
        
        console.log(`🔄 Navigation state restored: ${state.selectedElements?.length || 0} elements, ${state.containers?.length || 0} containers, ${state.actions?.length || 0} actions`);
        
        return {
            selectedElements: state.selectedElements || [],
            containers: state.containers || [],
            actions: state.actions || [],
            scrollConfig: state.scrollConfig || null,
            currentTool: state.currentTool || 'element',
            currentContainer: state.currentContainer || null
        };
        
    } catch (error) {
        console.error("❌ Error restoring navigation state:", error);
        sessionStorage.removeItem('scraperNavigationState');
        return null;
    }
}

export function clearNavigationState() {
    try {
        sessionStorage.removeItem('scraperNavigationState');
        console.log("🗑️ Navigation state cleared");
    } catch (error) {
        console.error("❌ Error clearing navigation state:", error);
    }
}