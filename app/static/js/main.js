/**
 * Main JavaScript file for the myHudson Portal pages
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('myHudson Portal login page loaded');
    
    // Handle login buttons
    setupLoginButtons();
    
    // Setup alerts (auto-dismiss after a few seconds)
    setupAlerts();
});

/**
 * Setup login button event listeners and enhance UI
 */
function setupLoginButtons() {
    // Get all login buttons
    const loginButtons = document.querySelectorAll('a[href="/auth/login"]');
    
    // Add hover effects and transition animations to login buttons
    loginButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.classList.add('btn-hover-effect');
        });
        
        button.addEventListener('mouseleave', function() {
            this.classList.remove('btn-hover-effect');
        });
        
        // Add a click animation
        button.addEventListener('click', function(e) {
            // Add loading state
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Redirecting...';
            this.classList.add('disabled');
        });
    });
}

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
        setupLoginButtons,
        setupAlerts,
        checkSessionStatus
    };
} 