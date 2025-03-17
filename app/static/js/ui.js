/**
 * UI module for the QR Code Generator application
 */
import { config } from './config.js';
import { api } from './api.js';
import { setLoading } from './utils.js';

export const ui = {
    /**
     * Updates the QR code image preview
     * @param {string} qrId - QR code ID
     */
    updateQRPreview(qrId) {
        const qrCodeImage = document.querySelector(config.SELECTORS.QR_IMAGE);
        if (qrCodeImage) {
            qrCodeImage.src = api.getQRImageUrl(qrId);
        }
    },

    /**
     * Renders the QR code list
     * @param {Array} qrCodes - Array of QR codes to render
     */
    renderQRList(qrCodes) {
        const tableBody = document.querySelector(config.SELECTORS.QR_TABLE_BODY);
        const emptyState = document.getElementById('empty-state');
        const footerElement = document.querySelector(`${config.SELECTORS.QR_LIST} tfoot`);
        const qrCountElement = document.getElementById('qr-count');
        
        if (!tableBody) return;
        
        // Clear existing rows except empty state
        Array.from(tableBody.children).forEach(child => {
            if (child.id !== 'empty-state') {
                tableBody.removeChild(child);
            }
        });
        
        // Show/hide empty state based on QR codes count
        if (qrCodes.length === 0) {
            emptyState.classList.remove('d-none');
            if (footerElement) footerElement.classList.add('d-none');
        } else {
            emptyState.classList.add('d-none');
            if (footerElement) {
                footerElement.classList.remove('d-none');
                if (qrCountElement) qrCountElement.textContent = qrCodes.length;
            }
            
            // Add QR code rows
            qrCodes.forEach(qrCode => {
                const row = document.createElement('tr');
                row.setAttribute('data-qr-id', qrCode.id);
                
                // Format created date if available
                const createdDate = qrCode.created_at 
                    ? new Date(qrCode.created_at).toLocaleDateString() 
                    : 'N/A';
                
                // Truncate long URLs for display
                const displayUrl = (qrCode.redirect_url || qrCode.destination_url || 'N/A').length > 50
                    ? (qrCode.redirect_url || qrCode.destination_url || 'N/A').substring(0, 50) + '...'
                    : (qrCode.redirect_url || qrCode.destination_url || 'N/A');
                
                row.innerHTML = `
                    <td class="text-nowrap">${qrCode.id}</td>
                    <td>
                        <span title="${qrCode.redirect_url || qrCode.destination_url || 'N/A'}">${displayUrl}</span>
                    </td>
                    <td class="text-nowrap">${createdDate}</td>
                    <td class="text-nowrap">${qrCode.scan_count || 0}</td>
                    <td class="text-end">
                        <div class="btn-group" role="group" aria-label="QR code actions">
                            <button type="button" class="btn btn-sm btn-outline-primary rounded-0 view-image-btn" 
                                    data-qr-id="${qrCode.id}" aria-label="View QR code">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-secondary rounded-0 update-btn" 
                                    data-qr-id="${qrCode.id}" aria-label="Edit QR code">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-danger rounded-0 delete-btn" 
                                    data-qr-id="${qrCode.id}" aria-label="Delete QR code">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
    },

    /**
     * Resets the create form
     * @param {HTMLFormElement} form - The form to reset
     */
    resetForm(form) {
        form.reset();
        const qrCodeImage = document.querySelector(config.SELECTORS.QR_IMAGE);
        if (qrCodeImage) {
            qrCodeImage.src = '';
        }
    },

    /**
     * Sets loading state on the form
     * @param {HTMLFormElement} form - The form to set loading state on
     * @param {boolean} isLoading - Whether to set or remove loading state
     */
    setFormLoading(form, isLoading) {
        setLoading(form, isLoading);
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = isLoading;
        }
    }
}; 