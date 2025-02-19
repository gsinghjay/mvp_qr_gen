/**
 * Main application script for the QR Code Generator
 */
import { config } from './config.js';
import { api } from './api.js';
import { ui } from './ui.js';
import { isValidUrl, formatUrl, showSuccess, showError } from './utils.js';

/**
 * Handles sidebar toggle
 */
function handleSidebarToggle() {
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}

/**
 * Handles viewing a QR code image
 * @param {Event} event - The click event
 */
function handleViewImage(event) {
    const button = event.target.closest('button');
    if (!button) return;
    
    const qrId = button.dataset.qrId;
    ui.updateQRPreview(qrId);
}

/**
 * Handles updating a QR code
 * @param {Event} event - The click event
 */
async function handleUpdate(event) {
    const button = event.target.closest('button');
    if (!button) return;
    
    const qrId = button.dataset.qrId;
    let newUrl = prompt('Enter the new destination URL (must start with http:// or https://):');
    
    if (!newUrl) return;

    newUrl = formatUrl(newUrl);

    if (!isValidUrl(newUrl)) {
        showError('Please enter a valid URL (e.g., https://example.com)');
        return;
    }

    try {
        await api.updateQR(qrId, newUrl);
        await refreshQRList();
        showSuccess('QR code updated successfully!');
    } catch (error) {
        console.error('Error updating QR code:', error);
    }
}

/**
 * Handles deleting a QR code
 * @param {Event} event - The click event
 */
async function handleDelete(event) {
    const button = event.target.closest('button');
    if (!button) return;
    
    const qrId = button.dataset.qrId;
    if (confirm('Are you sure you want to delete this QR code?')) {
        try {
            await api.deleteQR(qrId);
            await refreshQRList();
        } catch (error) {
            console.error('Error deleting QR code:', error);
        }
    }
}

/**
 * Refreshes the QR code list
 */
async function refreshQRList() {
    try {
        const qrCodes = await api.fetchQRCodes();
        ui.renderQRList(qrCodes);
    } catch (error) {
        console.error('Error refreshing QR codes:', error);
    }
}

/**
 * Handles form submission for creating a new QR code
 * @param {Event} event - The submit event
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const url = formData.get('redirect_url');

    if (!isValidUrl(url)) {
        showError('Please enter a valid URL (e.g., https://example.com)');
        return;
    }

    const data = {
        content: url,
        qr_type: 'dynamic',
        redirect_url: url,
        fill_color: formData.get('fill_color') || config.DEFAULT_VALUES.FILL_COLOR,
        back_color: formData.get('back_color') || config.DEFAULT_VALUES.BACK_COLOR,
        size: parseInt(formData.get('size')) || config.DEFAULT_VALUES.SIZE,
        border: parseInt(formData.get('border')) || config.DEFAULT_VALUES.BORDER,
        title: formData.get('title') || undefined,
        description: formData.get('description') || undefined,
        image_format: config.DEFAULT_VALUES.IMAGE_FORMAT
    };

    try {
        ui.setFormLoading(form, true);
        const newQrCode = await api.createDynamicQR(data);
        await refreshQRList();
        ui.updateQRPreview(newQrCode.id);
        ui.resetForm(form);
        showSuccess('QR code created successfully!');
    } catch (error) {
        console.error('Error creating QR code:', error);
    } finally {
        ui.setFormLoading(form, false);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Set up sidebar toggle
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', handleSidebarToggle);
    }

    // Set up event delegation for the table
    const qrCodeList = document.querySelector(config.SELECTORS.QR_LIST);
    if (qrCodeList) {
        qrCodeList.addEventListener('click', (event) => {
            const button = event.target.closest('button');
            if (!button) return;

            if (button.classList.contains('view-image-btn')) {
                handleViewImage(event);
            } else if (button.classList.contains('update-btn')) {
                handleUpdate(event);
            } else if (button.classList.contains('delete-btn')) {
                handleDelete(event);
            }
        });
    }

    // Set up form submission handler
    const createForm = document.querySelector(config.SELECTORS.FORM);
    if (createForm) {
        createForm.addEventListener('submit', handleFormSubmit);
    }

    // Initial fetch of QR codes
    refreshQRList();
}); 