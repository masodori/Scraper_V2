/**
 * Template Building Utilities
 */

export function buildTemplate(state) {
    // Combine regular elements and containers
    const allElements = [...state.selectedElements, ...state.containers];
    
    const template = {
        url: window.originalScrapingUrl || window.location.href,
        name: 'interactive_template',
        description: `Template created for ${window.location.hostname}`,
        elements: allElements,
        actions: state.actions,
        pagination: state.scrollConfig,
        cookies: [],  // Will be handled by Python
        stealth_mode: true,
        created_at: new Date().toISOString()
    };
    
    return template;
}

export function previewTemplate(state) {
    const template = buildTemplate(state);
    
    try {
        // Create a preview window
        const preview = window.open('', '_blank', 'width=800,height=600');
        preview.document.write(`
            <html>
                <head>
                    <title>Template Preview</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
                        .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        pre { background: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }
                        h1 { color: #333; }
                        .summary { background: #e3f2fd; padding: 15px; border-left: 4px solid #2196f3; margin: 20px 0; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🕷️ Scraping Template Preview</h1>
                        <div class="summary">
                            <strong>Summary:</strong><br>
                            • URL: ${template.url}<br>
                            • Elements: ${template.elements.length}<br>
                            • Actions: ${template.actions.length}
                        </div>
                        <h2>Template JSON:</h2>
                        <pre>${JSON.stringify(template, null, 2)}</pre>
                    </div>
                </body>
            </html>
        `);
        
        console.log("✅ Template preview opened");
        return true;
    } catch (error) {
        console.error("❌ Error opening preview:", error);
        return false;
    }
}