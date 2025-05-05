/**
 * Modal Handler Module for QR Code Generator Application
 * Handles all modal dialog operations
 */
import { showError, showSuccess } from './utils.js';
import { isValidUrl } from './utils.js';
import { api } from './api.js';

/**
 * Safely initializes and shows a bootstrap modal
 * @param {HTMLElement} modalElement - The modal element to show
 */
export function showModal(modalElement) {
    if (!modalElement) {
        console.error('Modal element is null or undefined');
        return;
    }
    
    try {
        // Ensure Bootstrap is loaded and available
        if (typeof bootstrap === 'undefined') {
            console.error('Bootstrap is not available. Make sure bootstrap.bundle.min.js is loaded');
            return;
        }
        
        // Get existing modal instance or create a new one
        const modalInstance = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
        
        // Show the modal
        modalInstance.show();
    } catch (error) {
        console.error('Error showing modal:', error);
        
        // Fallback: try using jQuery modal if available
        try {
            if (typeof $ !== 'undefined') {
                $(modalElement).modal('show');
            }
        } catch (fallbackError) {
            console.error('Fallback modal approach also failed:', fallbackError);
        }
    }
}

/**
 * Safely hides a bootstrap modal
 * @param {string} modalId - The ID of the modal to hide
 */
export function hideModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) {
        console.error(`Modal element with ID ${modalId} not found`);
        return;
    }
    
    try {
        // Ensure Bootstrap is loaded and available
        if (typeof bootstrap === 'undefined') {
            console.error('Bootstrap is not available. Make sure bootstrap.bundle.min.js is loaded');
            return;
        }
        
        // Get existing modal instance 
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            modalInstance.hide();
        }
    } catch (error) {
        console.error(`Error hiding modal ${modalId}:`, error);
        
        // Fallback: try using jQuery modal if available
        try {
            if (typeof $ !== 'undefined') {
                $(modalElement).modal('hide');
            }
        } catch (fallbackError) {
            console.error('Fallback modal approach also failed:', fallbackError);
        }
    }
}

/**
 * Populates the QR details modal with data
 * @param {Object} qrData - The QR code data
 */
export function populateQRModal(qrData) {
    if (!qrData) return;
    
    // Get modal element
    const modalElement = document.getElementById('qrDetailsModal');
    if (!modalElement) {
        console.error('QR details modal element not found');
        return;
    }
    
    // Set QR image (including logo if it exists)
    const modalImage = document.getElementById('modal-qr-image');
    if (modalImage) {
        const img = new Image();
        img.src = api.getQRImageUrl(qrData.id, { include_logo: true });
        
        // Handle successful load
        img.onload = function() {
            modalImage.src = img.src;
            // Remove both placeholder and spinner classes
            modalImage.classList.remove('loading-spinner', 'placeholder-qr');
        };
        
        // Handle load error
        img.onerror = function() {
            console.warn('Failed to load QR image, using placeholder');
            // Keep the placeholder but remove spinner
            modalImage.classList.remove('loading-spinner');
            // Add error indication
            modalImage.classList.add('placeholder-error');
        };
        
        modalImage.alt = `QR Code: ${qrData.title || qrData.id}`;
    }
    
    // Set basic info
    document.getElementById('modal-qr-id').textContent = qrData.id || '';
    document.getElementById('modal-qr-title').textContent = qrData.title || '-';
    document.getElementById('modal-qr-type').textContent = qrData.qr_type === 'dynamic' ? 'Dynamic' : 'Static';
    document.getElementById('modal-qr-created').textContent = new Date(qrData.created_at).toLocaleString();
    document.getElementById('modal-qr-description').textContent = qrData.description || '-';
    
    // Set QR code content
    const contentRow = document.getElementById('modal-content-row');
    const contentElement = document.getElementById('modal-qr-content');
    
    if (qrData.content) {
        contentElement.textContent = qrData.content;
        contentRow.classList.remove('d-none');
    } else {
        contentRow.classList.add('d-none');
    }
    
    // Set statistics
    document.getElementById('modal-qr-scans').textContent = qrData.scan_count || 0;
    
    const lastScanRow = document.getElementById('modal-last-scan-row');
    const lastScanEl = document.getElementById('modal-qr-last-scan');
    
    if (qrData.last_scan_at) {
        lastScanEl.textContent = new Date(qrData.last_scan_at).toLocaleString();
        lastScanRow.classList.remove('d-none');
    } else {
        lastScanEl.textContent = 'Never';
        lastScanRow.classList.remove('d-none');
    }
    
    // Handle redirect URL for dynamic QR codes
    const redirectRow = document.getElementById('modal-redirect-row');
    const redirectLink = document.getElementById('modal-qr-redirect');
    
    if (qrData.qr_type === 'dynamic' && qrData.redirect_url) {
        redirectLink.href = qrData.redirect_url;
        redirectLink.textContent = qrData.redirect_url;
        redirectRow.classList.remove('d-none');
    } else if (qrData.qr_type === 'static' && qrData.content && isValidUrl(qrData.content)) {
        redirectLink.href = qrData.content;
        redirectLink.textContent = qrData.content;
        redirectRow.classList.remove('d-none');
    } else {
        redirectRow.classList.add('d-none');
    }
    
    // Show/hide dynamic QR actions
    const actionsDiv = document.getElementById('modal-dynamic-actions');
    if (qrData.qr_type === 'dynamic') {
        actionsDiv.classList.remove('d-none');
    } else {
        actionsDiv.classList.add('d-none');
    }
}

/**
 * Sets up action buttons for editing and deleting QR codes
 * @param {Object} qrData - The QR code data
 */
export function setupActionButtons(qrData) {
    if (!qrData || qrData.qr_type !== 'dynamic') return;
    
    // Set up edit button
    const editButton = document.getElementById('modal-edit-btn');
    if (editButton) {
        editButton.onclick = function() {
            // Hide the details modal
            hideModal('qrDetailsModal');
            
            // Populate and show edit URL modal
            document.getElementById('edit-qr-id').value = qrData.id;
            document.getElementById('edit-redirect-url').value = qrData.redirect_url || '';
            
            // Show edit modal
            const editModalElement = document.getElementById('editUrlModal');
            showModal(editModalElement);
        };
    }
    
    // Set up delete button
    const deleteButton = document.getElementById('modal-delete-btn');
    if (deleteButton) {
        deleteButton.onclick = function() {
            // Hide the details modal
            hideModal('qrDetailsModal');
            
            // Populate and show delete confirmation modal
            document.getElementById('delete-qr-id').value = qrData.id;
            
            const deleteModalElement = document.getElementById('deleteConfirmModal');
            showModal(deleteModalElement);
        };
    }
} 