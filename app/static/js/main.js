/**
 * Main Application Entry Point
 * 
 * This file imports all modules and initializes the application.
 * The modular design facilitates future migration to HTMX + Hyperscript.
 */
import { init } from './event-initializer.js';

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

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('QR Generator application loaded');
    
    // Initialize the application
    init();
    
    // Setup auto-dismissing alerts
    setupAlerts();
});

// Also make init available globally for explicit calls
window.initQRApp = init;

// Export functions for testing (if using a test framework)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        setupAlerts
    };
} 