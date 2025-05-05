/**
 * QR Operations Module for QR Code Generator Application
 * Handles core QR code operations (view, update, delete, download)
 */
import { api } from './api.js';
import { showError, showSuccess, isValidUrl, formatUrl } from './utils.js';
import { populateQRModal, showModal, hideModal, setupActionButtons } from './modal-handler.js';

/**
 * Handles viewing a QR code image
 * @param {Event} event - The click event
 */
export async function handleViewImage(event) {
    event.preventDefault();
    
    // Get QR ID from the clicked button
    const button = event.target.closest('.view-btn');
    if (!button || !button.dataset.id) {
        console.error('Invalid view button or missing data-id attribute');
        return;
    }
    
    const qrId = button.dataset.id;
    
    try {
        // Get the modal element
        const modalElement = document.getElementById('qrDetailsModal');
        if (!modalElement) {
            console.error('QR details modal element not found');
            return;
        }
        
        // Show loading state on the image with pure CSS approach
        const modalImage = document.getElementById('modal-qr-image');
        if (modalImage) {
            // Clear current src and add placeholder/loading classes
            modalImage.src = '';
            modalImage.classList.add('placeholder-qr', 'loading-spinner');
        }
        
        // Fetch QR code details
        const qrDetails = await api.getQR(qrId);
        
        // Populate modal with QR data
        populateQRModal(qrDetails);
        
        // Set up download buttons
        setupDownloadButtons(qrId);
        
        // Set up action buttons for dynamic QR codes
        setupActionButtons(qrDetails);
        
        // Show the modal after data is loaded
        showModal(modalElement);
    } catch (error) {
        console.error('Error viewing QR code:', error);
        showError('Failed to load QR code details. Please try again.');
    }
}

/**
 * Sets up download buttons for different formats
 * @param {string} qrId - The QR code ID
 */
export function setupDownloadButtons(qrId) {
    const downloadFormats = ['png', 'svg', 'pdf'];
    
    downloadFormats.forEach(format => {
        const button = document.getElementById(`download-${format}`);
        if (button) {
            button.onclick = function(e) {
                e.preventDefault();
                downloadQRCode(qrId, format);
            };
        }
    });
}

/**
 * Downloads a QR code in the specified format
 * @param {string} qrId - The QR code ID
 * @param {string} format - The format (png, svg, pdf)
 */
export async function downloadQRCode(qrId, format) {
    try {
        // Get the download URL
        const url = api.getQRImageUrl(qrId, { format });
        
        // For PDF, we need to create a hidden link
        const a = document.createElement('a');
        a.href = url;
        a.download = `qrcode-${qrId}.${format}`;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        showSuccess(`QR code downloaded as ${format.toUpperCase()}`);
    } catch (error) {
        console.error(`Error downloading QR code as ${format}:`, error);
        showError(`Failed to download QR code as ${format}`);
    }
}

/**
 * Handles updating a QR code
 * @param {Event} event - The click event
 */
export async function handleUpdate(event) {
    const button = event.target.closest('.update-btn');
    if (!button || !button.dataset.qrId) {
        console.error('Invalid update button or missing data-qr-id attribute');
        return;
    }
    
    const qrId = button.dataset.qrId;
    let newUrl = prompt('Enter the new destination URL (must start with http:// or https://):');
    
    if (!newUrl) return;

    newUrl = formatUrl(newUrl);

    if (!isValidUrl(newUrl)) {
        showError('Please enter a valid URL (e.g., https://example.com)');
        return;
    }

    try {
        await api.updateQR(qrId, { redirect_url: newUrl });
        showSuccess('QR code updated successfully!');
        
        // If refreshQRList is available, use it to refresh the list
        if (typeof window.refreshQRList === 'function') {
            window.refreshQRList(window.currentPage);
        } else {
            // Otherwise, reload the page
            window.location.reload();
        }
    } catch (error) {
        console.error('Error updating QR code:', error);
        showError('Failed to update QR code. Please try again.');
    }
}

/**
 * Handles deleting a QR code
 * @param {Event} event - The click event
 */
export async function handleDelete(event) {
    const button = event.target.closest('.delete-btn');
    if (!button || !button.dataset.qrId) {
        console.error('Invalid delete button or missing data-qr-id attribute');
        return;
    }
    
    const qrId = button.dataset.qrId;
    if (!confirm('Are you sure you want to delete this QR code? This action cannot be undone.')) return;
    
    try {
        await api.deleteQR(qrId);
        showSuccess('QR code deleted successfully!');
        
        // If refreshQRList is available, use it to refresh the list
        if (typeof window.refreshQRList === 'function') {
            window.refreshQRList(window.currentPage);
        } else {
            // Otherwise, reload the page
            window.location.reload();
        }
    } catch (error) {
        console.error('Error deleting QR code:', error);
        showError('Failed to delete QR code. Please try again.');
    }
} 