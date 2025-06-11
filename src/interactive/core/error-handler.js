/**
 * Error Handling System
 */

export class ErrorHandler {
    static async handle(operation, fallback = null) {
        try {
            return await operation();
        } catch (error) {
            console.error(`Operation failed: ${error.message}`, error);

            if (typeof window.log_message_py === 'function') {
                window.log_message_py(`Error: ${error.message}`);
            }

            if (fallback) {
                return await fallback(error);
            }

            // Import ModalManager dynamically to avoid circular dependencies
            const { ModalManager } = await import('../ui/modal-manager.js');
            await ModalManager.alert(`Operation failed: ${error.message}`);
            return null;
        }
    }
    
    static handleSync(operation, fallback = null) {
        try {
            return operation();
        } catch (error) {
            console.error(`Operation failed: ${error.message}`, error);

            if (typeof window.log_message_py === 'function') {
                window.log_message_py(`Error: ${error.message}`);
            }

            if (fallback) {
                return fallback(error);
            }

            // For sync operations, we can't show modal alerts
            console.error('Unhandled sync error:', error);
            return null;
        }
    }
}