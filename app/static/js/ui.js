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
        if (!tableBody) return;
        
        tableBody.innerHTML = '';

        qrCodes.forEach(qrCode => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${qrCode.id}</td>
                <td>${qrCode.redirect_url || qrCode.destination_url || 'N/A'}</td>
                <td>
                    <button class="btn btn-primary btn-action view-image-btn" data-qr-id="${qrCode.id}">
                        <i class="bi bi-eye"></i> View
                    </button>
                    <button class="btn btn-secondary btn-action update-btn" data-qr-id="${qrCode.id}">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="btn btn-danger btn-action delete-btn" data-qr-id="${qrCode.id}">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
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