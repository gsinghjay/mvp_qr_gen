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
     * @param {Object} pagination - Pagination data
     * @param {number} pagination.page - Current page number
     * @param {number} pagination.total - Total number of QR codes
     * @param {number} pagination.page_size - Number of QR codes per page
     */
    renderQRList(qrCodes, pagination = { page: 1, total: 0, page_size: config.DEFAULT_VALUES.PAGE_SIZE }) {
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
                if (qrCountElement) qrCountElement.textContent = pagination.total;
            }
            
            // Add QR code rows
            qrCodes.forEach(qrCode => {
                const row = document.createElement('tr');
                row.setAttribute('data-qr-id', qrCode.id);
                row.innerHTML = `
                    <td class="text-nowrap">
                        <small class="text-muted">${qrCode.id.substring(0, 8)}...</small>
                    </td>
                    <td>
                        <div class="d-flex align-items-center">
                            <span class="badge rounded-0 me-2 ${qrCode.qr_type === 'dynamic' ? 'bg-primary' : 'bg-secondary'}">
                                ${qrCode.qr_type}
                            </span>
                            <span class="text-truncate">${qrCode.qr_type === 'dynamic' ? qrCode.redirect_url : qrCode.content}</span>
                        </div>
                    </td>
                    <td class="text-nowrap">
                        <small>${new Date(qrCode.created_at).toLocaleString()}</small>
                    </td>
                    <td>
                        <span class="badge bg-dark rounded-0">${qrCode.scan_count}</span>
                    </td>
                    <td class="text-end">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-secondary rounded-0 view-btn" data-qr-id="${qrCode.id}" data-bs-toggle="modal" data-bs-target="#previewModal">
                                <i class="bi bi-eye"></i>
                            </button>
                            ${qrCode.qr_type === 'dynamic' ? `
                            <button class="btn btn-outline-primary rounded-0 update-btn" data-qr-id="${qrCode.id}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            ` : ''}
                            <button class="btn btn-outline-danger rounded-0 delete-btn" data-qr-id="${qrCode.id}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
        
        // Update pagination
        this.updatePagination(pagination);
    },
    
    /**
     * Updates the pagination controls
     * @param {Object} pagination - Pagination data
     * @param {number} pagination.page - Current page number
     * @param {number} pagination.total - Total number of QR codes
     * @param {number} pagination.page_size - Number of QR codes per page
     */
    updatePagination(pagination = { page: 1, total: 0, page_size: config.DEFAULT_VALUES.PAGE_SIZE }) {
        const currentPageElement = document.getElementById('current-page');
        const totalPagesElement = document.getElementById('total-pages');
        const prevButton = document.querySelector(config.SELECTORS.PAGINATION_PREV);
        const nextButton = document.querySelector(config.SELECTORS.PAGINATION_NEXT);
        
        if (!currentPageElement || !totalPagesElement || !prevButton || !nextButton) return;
        
        // Calculate total pages
        const totalPages = Math.max(1, Math.ceil(pagination.total / pagination.page_size));
        
        // Update page info
        currentPageElement.textContent = pagination.page;
        totalPagesElement.textContent = totalPages;
        
        // Update button states
        const prevPageItem = prevButton.closest('.page-item');
        const nextPageItem = nextButton.closest('.page-item');
        
        if (pagination.page <= 1) {
            prevPageItem.classList.add('disabled');
        } else {
            prevPageItem.classList.remove('disabled');
        }
        
        if (pagination.page >= totalPages) {
            nextPageItem.classList.add('disabled');
        } else {
            nextPageItem.classList.remove('disabled');
        }
    },

    /**
     * Resets a form to its initial state
     * @param {HTMLFormElement} form - The form to reset
     */
    resetForm(form) {
        if (!form) return;
        form.reset();
        // Reset custom select elements or other complex form fields if needed
    },
    
    /**
     * Sets the loading state of a form
     * @param {HTMLFormElement} form - The form to set loading state
     * @param {boolean} isLoading - Whether the form is loading
     */
    setFormLoading(form, isLoading) {
        if (!form) return;
        setLoading(form, isLoading);
    }
}; 