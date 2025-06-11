/**
 * Bridge to Python Functions
 */

export function logMessage(message) {
    if (typeof window.log_message_py === 'function') {
        window.log_message_py(message);
    } else {
        console.log(`Python bridge not available: ${message}`);
    }
}

export function saveTemplate(templateData) {
    if (typeof window.save_template_py === 'function') {
        window.save_template_py(JSON.stringify(templateData));
        return true;
    } else {
        console.error("Python save_template_py callback not available");
        return false;
    }
}

export function checkPythonCallbacks() {
    const callbacks = {
        log_message_py: typeof window.log_message_py === 'function',
        save_template_py: typeof window.save_template_py === 'function'
    };
    
    console.log("Python callbacks status:", callbacks);
    return callbacks;
}