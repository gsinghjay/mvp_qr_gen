/**
 * Utility functions for the QR Code Generator application
 */

/**
 * Validates if a string is a valid URL
 * @param {string} string - The string to validate
 * @returns {boolean} - True if valid URL, false otherwise
 */
export function isValidUrl(string) {
    try {
        const url = new URL(string);
        
        // Ensure URL has a valid protocol (http or https)
        if (!url.protocol || !['http:', 'https:'].includes(url.protocol)) {
            return false;
        }
        
        // Ensure URL has a valid hostname
        if (!url.hostname) {
            return false;
        }
        
        // Optional: Check against allowed domains
        // const allowedDomains = ['example.com', 'yourdomain.com'];
        // if (!allowedDomains.some(domain => url.hostname.endsWith(domain))) {
        //     return false;
        // }
        
        // Prevent localhost and private IP redirects in production
        if (process.env.NODE_ENV === 'production') {
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
 */
export function showError(message) {
    alert(message);
}

/**
 * Shows a success message to the user
 * @param {string} message - The success message to display
 */
export function showSuccess(message) {
    alert(message);
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
    
    // Force HTTPS in production
    if (process.env.NODE_ENV === 'production' && url.startsWith('http://')) {
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