/**
 * Main JavaScript file for the QR Generator application
 */

// Import script.js init function if available
import { init as scriptInit } from './script.js';

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('QR Generator application loaded');
    
    // Initialize script.js functionality if available
    if (typeof scriptInit === 'function') {
        console.log('Initializing script.js functions');
        scriptInit();
    } else {
        console.warn('script.js init function not available');
    }
    
    // Setup alerts (auto-dismiss after a few seconds)
    setupAlerts();
});

/**
 * Setup auto-dismissing alerts
 */
function setupAlerts() {
    // Find all alert elements
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    // Auto dismiss alerts after 5 seconds
    alerts.forEach(alert => {
        setTimeout(() => {
            // Check if Bootstrap is available
            if (typeof bootstrap !== 'undefined') {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                // Fallback if Bootstrap JS is not loaded
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 500);
            }
        }, 5000);
    });
}

/**
 * Handle the session timeout and redirection
 */
function checkSessionStatus() {
    // This function could be expanded in the future to check session status
    // and show warnings before session timeout
    return true;
}

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        setupAlerts,
        checkSessionStatus
    };
} 