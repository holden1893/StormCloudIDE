// Nexus Nebula Universe - Main JavaScript

// Global namespace
window.NexusNebula = window.NexusNebula || {};

// API helper
NexusNebula.api = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('auth_token');
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            }
        };

        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'API request failed');
        }

        return data;
    },

    get(endpoint) {
        return this.request(endpoint);
    },

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// UI helpers
NexusNebula.showNotification = function(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, duration);
};

NexusNebula.copyToClipboard = async function(text) {
    try {
        await navigator.clipboard.writeText(text);
        this.showNotification('Copied to clipboard!', 'success');
    } catch (error) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        this.showNotification('Copied to clipboard!', 'success');
    }
};

NexusNebula.confirm = function(message) {
    return window.confirm(message);
};

NexusNebula.loading = {
    show(element = document.body) {
        const loader = document.createElement('div');
        loader.className = 'loading-overlay';
        loader.innerHTML = `
            <div class="loading-spinner"></div>
            <div class="loading-text">Loading...</div>
        `;
        element.appendChild(loader);
    },

    hide(element = document.body) {
        const loader = element.querySelector('.loading-overlay');
        if (loader) {
            loader.remove();
        }
    }
};

// Form helpers
NexusNebula.forms = {
    serialize(form) {
        const data = new FormData(form);
        const result = {};
        for (let [key, value] of data.entries()) {
            result[key] = value;
        }
        return result;
    },

    validate(form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        let isValid = true;

        inputs.forEach(input => {
            if (input.hasAttribute('required') && !input.value.trim()) {
                this.showError(input, 'This field is required');
                isValid = false;
            } else if (input.type === 'email' && input.value && !this.isValidEmail(input.value)) {
                this.showError(input, 'Please enter a valid email address');
                isValid = false;
            } else {
                this.clearError(input);
            }
        });

        return isValid;
    },

    showError(input, message) {
        this.clearError(input);
        input.classList.add('error');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        input.parentNode.appendChild(errorDiv);
    },

    clearError(input) {
        input.classList.remove('error');
        const errorDiv = input.parentNode.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
    },

    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
};

// Modal helpers
NexusNebula.modal = {
    show(content, options = {}) {
        const modal = document.createElement('div');
        modal.className = 'modal-backdrop';
        modal.innerHTML = `
            <div class="modal-content">
                ${content}
            </div>
        `;

        // Add close button if requested
        if (options.closable !== false) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'modal-close';
            closeBtn.innerHTML = '×';
            closeBtn.onclick = () => this.hide(modal);
            modal.querySelector('.modal-content').prepend(closeBtn);
        }

        // Close on backdrop click
        modal.onclick = (e) => {
            if (e.target === modal) {
                this.hide(modal);
            }
        };

        document.body.appendChild(modal);
        return modal;
    },

    hide(modal) {
        if (modal && modal.parentNode) {
            modal.parentNode.removeChild(modal);
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add loading styles
    const style = document.createElement('style');
    style.textContent = `
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        .loading-text {
            color: white;
            margin-top: 10px;
            font-size: 16px;
        }
        .error {
            border-color: #ef4444 !important;
        }
        .error-message {
            color: #ef4444;
            font-size: 12px;
            margin-top: 4px;
        }
        .modal-close {
            position: absolute;
            top: 10px;
            right: 10px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        }
    `;
    document.head.appendChild(style);

    // Check for auth token on page load
    const token = localStorage.getItem('auth_token');
    if (token && window.location.pathname === '/') {
        // Redirect to dashboard if logged in and on home page
        window.location.href = '/dashboard';
    }
});