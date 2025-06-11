/**
 * CSS Styles for Interactive Scraper
 */

export function injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Scraper Overlay Styles */
        .scraper-highlight {
            outline: 3px solid #ff6b6b !important;
            outline-offset: 2px !important;
            background-color: rgba(255, 107, 107, 0.1) !important;
            cursor: crosshair !important;
            transition: all 0.2s ease !important;
        }
        
        .scraper-selected {
            outline: 3px solid #4ecdc4 !important;
            outline-offset: 2px !important;
            background-color: rgba(78, 205, 196, 0.2) !important;
            position: relative !important;
        }
        
        .scraper-selected::after {
            content: attr(data-scraper-label);
            position: absolute;
            top: -25px;
            left: 0;
            background: #4ecdc4;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-family: Arial, sans-serif;
            font-weight: bold;
            z-index: 999999;
            white-space: nowrap;
        }
        
        .scraper-action-element {
            outline: 3px solid #ffd93d !important;
            outline-offset: 2px !important;
            background-color: rgba(255, 217, 61, 0.2) !important;
        }
        
        .scraper-action-element::after {
            content: "⚡ " attr(data-scraper-action);
            position: absolute;
            top: -25px;
            left: 0;
            background: #ffd93d;
            color: #333;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-family: Arial, sans-serif;
            font-weight: bold;
            z-index: 999999;
            white-space: nowrap;
        }
        
        .scraper-container-context {
            outline: 4px dashed #ff6b6b !important;
            background-color: rgba(255, 107, 107, 0.1) !important;
        }
        
        .scraper-sub-element {
            outline: 2px solid #4ecdc4 !important;
            background-color: rgba(78, 205, 196, 0.2) !important;
        }
        
        .scraper-sub-element::after {
            content: "📦 " attr(data-sub-label);
            position: absolute;
            top: -25px;
            right: 0;
            background: #4ecdc4;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-family: Arial, sans-serif;
            font-weight: bold;
            z-index: 999999;
            white-space: nowrap;
        }
        
        .scraper-control-panel {
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            width: 300px !important;
            max-width: calc(100vw - 30px) !important;
            max-height: calc(100vh - 30px) !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3) !important;
            z-index: 999999 !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            color: white !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            overflow: visible !important;
            transform: translateZ(0) !important;
            resize: none !important;
            user-select: none !important;
        }
        
        .scraper-panel-header {
            padding: 15px 20px !important;
            border-bottom: 1px solid rgba(255,255,255,0.1) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
        }
        
        .scraper-panel-title {
            font-size: 16px !important;
            font-weight: 600 !important;
            margin: 0 !important;
        }
        
        .scraper-panel-body {
            padding: 20px !important;
        }
        
        .scraper-tool-selector {
            display: flex !important;
            gap: 10px !important;
            margin-bottom: 20px !important;
        }
        
        .scraper-tool-btn {
            flex: 1 !important;
            padding: 12px 8px !important;
            border: 2px solid rgba(255,255,255,0.2) !important;
            background: rgba(255,255,255,0.05) !important;
            color: white !important;
            border-radius: 8px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            text-align: center !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            gap: 4px !important;
        }
        
        .scraper-tool-btn:hover {
            background: rgba(255,255,255,0.2) !important;
            border-color: rgba(255,255,255,0.6) !important;
        }
        
        .scraper-tool-btn.active {
            background: rgba(255,255,255,0.3) !important;
            border-color: white !important;
            box-shadow: 0 0 10px rgba(255,255,255,0.3) !important;
        }
        
        .scraper-element-list {
            max-height: 150px !important;
            overflow-y: auto !important;
            margin: 15px 0 !important;
            padding: 0 !important;
            scrollbar-width: thin !important;
            scrollbar-color: rgba(255,255,255,0.3) transparent !important;
        }
        
        .scraper-element-list::-webkit-scrollbar {
            width: 6px !important;
        }
        
        .scraper-element-list::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.1) !important;
            border-radius: 3px !important;
        }
        
        .scraper-element-list::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.3) !important;
            border-radius: 3px !important;
        }
        
        .scraper-element-list::-webkit-scrollbar-thumb:hover {
            background: rgba(255,255,255,0.5) !important;
        }
        
        .scraper-element-item {
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            padding: 8px 12px !important;
            margin: 5px 0 !important;
            background: rgba(255,255,255,0.1) !important;
            border-radius: 6px !important;
            font-size: 12px !important;
        }
        
        .scraper-element-label {
            font-weight: 500 !important;
            color: #4ecdc4 !important;
        }
        
        .scraper-element-selector {
            font-family: 'Courier New', monospace !important;
            font-size: 10px !important;
            color: rgba(255,255,255,0.7) !important;
            max-width: 150px !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
        }
        
        .scraper-action-btn {
            padding: 10px 16px !important;
            background: linear-gradient(45deg, #667eea, #764ba2) !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            cursor: pointer !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            width: 100% !important;
            margin: 8px 0 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2) !important;
        }
        
        .scraper-action-btn:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
        }
        
        .scraper-secondary-btn {
            background: rgba(255,255,255,0.1) !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            box-shadow: none !important;
        }
        
        .scraper-secondary-btn:hover {
            background: rgba(255,255,255,0.15) !important;
            border-color: rgba(255,255,255,0.3) !important;
            transform: translateY(0) !important;
        }
        
        .scraper-minimize-btn {
            background: rgba(255,255,255,0.2) !important;
            border: none !important;
            color: white !important;
            border-radius: 50% !important;
            width: 30px !important;
            height: 30px !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.3s ease !important;
        }
        
        .scraper-minimize-btn:hover {
            background: rgba(255,255,255,0.3) !important;
        }
        
        .scraper-status {
            padding: 10px !important;
            background: rgba(255,255,255,0.1) !important;
            border-radius: 6px !important;
            margin: 10px 0 !important;
            font-size: 12px !important;
            text-align: center !important;
        }
        
        .scraper-input {
            width: 100% !important;
            padding: 8px 12px !important;
            border: 2px solid rgba(255,255,255,0.3) !important;
            background: rgba(255,255,255,0.1) !important;
            color: white !important;
            border-radius: 6px !important;
            font-size: 14px !important;
            margin: 5px 0 !important;
        }
        
        .scraper-input::placeholder {
            color: rgba(255,255,255,0.6) !important;
        }
        
        .scraper-input:focus {
            outline: none !important;
            border-color: white !important;
            box-shadow: 0 0 10px rgba(255,255,255,0.3) !important;
        }
        
        .scraper-modal {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: rgba(0,0,0,0.5) !important;
            z-index: 999999999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }
        
        .scraper-modal-content {
            background: white !important;
            border-radius: 12px !important;
            padding: 24px !important;
            min-width: 300px !important;
            max-width: 500px !important;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3) !important;
            text-align: center !important;
        }
        
        .scraper-modal-title {
            font-size: 18px !important;
            font-weight: 600 !important;
            margin-bottom: 12px !important;
            color: #333 !important;
        }
        
        .scraper-modal-message {
            font-size: 14px !important;
            color: #666 !important;
            margin-bottom: 20px !important;
            line-height: 1.5 !important;
            white-space: pre-line !important;
        }
        
        .scraper-modal-input {
            width: 100% !important;
            padding: 12px !important;
            border: 2px solid #ddd !important;
            border-radius: 6px !important;
            font-size: 14px !important;
            margin-bottom: 20px !important;
            box-sizing: border-box !important;
        }
        
        .scraper-modal-input:focus {
            outline: none !important;
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        }
        
        .scraper-modal-buttons {
            display: flex !important;
            gap: 12px !important;
            justify-content: center !important;
        }
        
        .scraper-modal-btn {
            padding: 12px 24px !important;
            border: none !important;
            border-radius: 6px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            min-width: 80px !important;
        }
        
        .scraper-modal-btn-primary {
            background: #667eea !important;
            color: white !important;
        }
        
        .scraper-modal-btn-primary:hover {
            background: #5a6fd8 !important;
            transform: translateY(-1px) !important;
        }
        
        .scraper-modal-btn-secondary {
            background: #f8f9fa !important;
            color: #333 !important;
            border: 1px solid #ddd !important;
        }
        
        .scraper-modal-btn-secondary:hover {
            background: #e9ecef !important;
            transform: translateY(-1px) !important;
        }
    `;
    document.head.appendChild(style);
}