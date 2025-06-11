/**
 * Modal Management System
 */

export class ModalManager {
    static show(config) {
        return new Promise((resolve) => {
            const { type, title, message, buttons = [], input = null, content = null } = config;
            
            const modal = document.createElement('div');
            modal.className = 'scraper-modal';
            
            let inputHtml = '';
            if (input) {
                inputHtml = `<input type="text" class="scraper-modal-input" placeholder="${input.placeholder || ''}" ${input.autofocus ? 'autofocus' : ''}>`;
            }
            
            let messageHtml = '';
            if (message) {
                messageHtml = `<div class="scraper-modal-message">${message}</div>`;
            }
            
            let customContentHtml = '';
            if (content) {
                customContentHtml = content;
            }
            
            const buttonsHtml = buttons.map((btn, index) => {
                const isPrimary = btn.primary || index === buttons.length - 1;
                const buttonClass = isPrimary ? 'scraper-modal-btn-primary' : 'scraper-modal-btn-secondary';
                return `<button class="scraper-modal-btn ${buttonClass}" data-action="${btn.action || btn.toLowerCase()}">${btn.text || btn}</button>`;
            }).join('');
            
            modal.innerHTML = `
                <div class="scraper-modal-content">
                    <div class="scraper-modal-title">${title}</div>
                    ${messageHtml}
                    ${customContentHtml}
                    ${inputHtml}
                    <div class="scraper-modal-buttons">
                        ${buttonsHtml}
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            const inputElement = modal.querySelector('.scraper-modal-input');
            const buttonElements = modal.querySelectorAll('.scraper-modal-btn');
            
            // Focus input if present
            if (inputElement && input && input.autofocus) {
                setTimeout(() => inputElement.focus(), 100);
            }
            
            // Handle button clicks
            buttonElements.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const action = e.target.dataset.action;
                    let result = action;
                    
                    if (type === 'prompt' && action === 'ok') {
                        result = inputElement ? inputElement.value : null;
                    } else if (type === 'confirm') {
                        result = action === 'ok';
                    } else if (action === 'cancel') {
                        result = type === 'confirm' ? false : null;
                    }
                    
                    ModalManager.cleanup(modal);
                    resolve(result);
                });
            });
            
            // Handle keyboard events
            const keyHandler = (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (type === 'prompt' && inputElement) {
                        ModalManager.cleanup(modal);
                        resolve(inputElement.value);
                    } else if (type === 'confirm') {
                        ModalManager.cleanup(modal);
                        resolve(true);
                    } else {
                        ModalManager.cleanup(modal);
                        resolve(undefined);
                    }
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    ModalManager.cleanup(modal);
                    resolve(type === 'confirm' ? false : null);
                }
            };
            
            if (inputElement) {
                inputElement.addEventListener('keydown', keyHandler);
            } else {
                document.addEventListener('keydown', keyHandler);
                modal._keyHandler = keyHandler; // Store for cleanup
            }
            
            // Handle background click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    ModalManager.cleanup(modal);
                    resolve(type === 'confirm' ? false : null);
                }
            });
        });
    }
    
    static cleanup(modal) {
        if (modal._keyHandler) {
            document.removeEventListener('keydown', modal._keyHandler);
        }
        if (document.body.contains(modal)) {
            document.body.removeChild(modal);
        }
    }
    
    static alert(message, title = 'Notice') {
        return this.show({
            type: 'alert',
            title,
            message,
            buttons: ['OK']
        });
    }
    
    static confirm(title, message) {
        return this.show({
            type: 'confirm',
            title,
            message,
            buttons: ['Cancel', { text: 'OK', primary: true }]
        });
    }
    
    static prompt(title, placeholder = '') {
        return this.show({
            type: 'prompt',
            title,
            input: { placeholder, autofocus: true },
            buttons: ['Cancel', { text: 'OK', primary: true }]
        });
    }
}