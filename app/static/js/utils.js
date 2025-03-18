/**
 * Utility functions for the QR Code Generator application
 */

/**
 * Creates a debounced function that delays invoking func until after wait milliseconds
 * @param {Function} func - The function to debounce
 * @param {number} wait - The number of milliseconds to delay
 * @return {Function} - The debounced function
 */
export function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Validates if a string is a valid URL
 * @param {string} string - The string to validate
 * @returns {boolean} - True if valid URL, false otherwise
 */
export function isValidUrl(string) {
    try {
        // First try to format the URL if it doesn't have a protocol
        const urlToCheck = !string.startsWith('http://') && !string.startsWith('https://')
            ? `https://${string}`
            : string;

        const url = new URL(urlToCheck);
        
        // Ensure URL has a valid protocol (http or https)
        if (!url.protocol || !['http:', 'https:'].includes(url.protocol)) {
            return false;
        }
        
        // Ensure URL has a valid hostname
        if (!url.hostname) {
            return false;
        }
        
        // Prevent localhost and private IP redirects in production
        // Note: We're checking window.location.protocol instead of process.env
        if (window.location.protocol === 'https:') {
            const hostname = url.hostname.toLowerCase();
            if (hostname === 'localhost' || hostname === '127.0.0.1' || 
                /^192\.168\.|^10\.|^172\.(1[6-9]|2[0-9]|3[0-1])\./.test(hostname)) {
                return false;
            }
        }
        
        // Ensure reasonable URL length
        if (string.length > 2048) {
            return false;
        }
        
        return true;
    } catch (_) {
        return false;
    }
}

/**
 * Shows an error message to the user
 * @param {string} message - The error message to display
 * @param {number} [duration=5000] - How long to show the message in milliseconds
 */
export function showError(message, duration = 5000) {
    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap not available for alert:', message);
        alert(message);
        return;
    }

    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.className = 'position-fixed top-0 start-50 translate-middle-x p-3';
        alertContainer.style.zIndex = '9999';
        document.body.appendChild(alertContainer);
    }
    
    // Create the alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show rounded-0';
    alert.role = 'alert';
    
    // Add the icon and message
    alert.innerHTML = `
        <i class="bi bi-exclamation-triangle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    alertContainer.appendChild(alert);
    
    try {
        // Initialize Bootstrap alert
        const bsAlert = new bootstrap.Alert(alert);
        
        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                bsAlert.close();
            }, duration);
        }
        
        // Remove from DOM after closed
        alert.addEventListener('closed.bs.alert', () => {
            alert.remove();
        });
    } catch (error) {
        console.error('Error initializing Bootstrap alert:', error);
        // Fallback if Bootstrap fails
        setTimeout(() => {
            alert.remove();
        }, duration);
    }
}

/**
 * Shows a success message to the user
 * @param {string} message - The success message to display
 * @param {number} [duration=5000] - How long to show the message in milliseconds
 */
export function showSuccess(message, duration = 5000) {
    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap not available for alert:', message);
        alert(message);
        return;
    }

    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.className = 'position-fixed top-0 start-50 translate-middle-x p-3';
        alertContainer.style.zIndex = '9999';
        document.body.appendChild(alertContainer);
    }
    
    // Create the alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show rounded-0';
    alert.role = 'alert';
    
    // Add the icon and message
    alert.innerHTML = `
        <i class="bi bi-check-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    alertContainer.appendChild(alert);
    
    try {
        // Initialize Bootstrap alert
        const bsAlert = new bootstrap.Alert(alert);
        
        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                bsAlert.close();
            }, duration);
        }
        
        // Remove from DOM after closed
        alert.addEventListener('closed.bs.alert', () => {
            alert.remove();
        });
    } catch (error) {
        console.error('Error initializing Bootstrap alert:', error);
        // Fallback if Bootstrap fails
        setTimeout(() => {
            alert.remove();
        }, duration);
    }
}

/**
 * Formats a URL by ensuring it has a proper protocol
 * @param {string} url - The URL to format
 * @returns {string} - Formatted URL
 */
export function formatUrl(url) {
    if (!url) return url;
    
    // Add https:// if no protocol is specified
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        return `https://${url}`;
    }
    
    // Force HTTPS when the page is served over HTTPS
    if (window.location.protocol === 'https:' && url.startsWith('http://')) {
        return `https://${url.substring(7)}`;
    }
    
    return url;
}

/**
 * Sets loading state on an element
 * @param {HTMLElement} element - The element to set loading state on
 * @param {boolean} isLoading - Whether to set or remove loading state
 */
export function setLoading(element, isLoading) {
    if (isLoading) {
        element.classList.add('loading');
    } else {
        element.classList.remove('loading');
    }
} 