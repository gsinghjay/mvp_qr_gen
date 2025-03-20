/**
 * Main application script for the QR Code Generator
 */
import { config } from './config.js';
import { api } from './api.js';
import { ui } from './ui.js';
import { isValidUrl, formatUrl, showSuccess, showError, debounce } from './utils.js';

// Current state
let currentPage = 1;
let qrTypeFilter = null;
let searchTerm = null;
let currentSortBy = 'created_at'; // Default sort by creation date
let currentSortDesc = true; // Default sort newest first

// Track the last QR code ID used for preview
let lastPreviewQrId = null;
let previewTimer = null;
let previewInProgress = false;

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
async function handleViewImage(event) {
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
 * Safely initializes and shows a bootstrap modal
 * @param {HTMLElement} modalElement - The modal element to show
 */
function showModal(modalElement) {
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
 * Populates the QR details modal with data
 * @param {Object} qrData - The QR code data
 */
function populateQRModal(qrData) {
    if (!qrData) return;
    
    // Get modal element
    const modalElement = document.getElementById('qrDetailsModal');
    if (!modalElement) {
        console.error('QR details modal element not found');
        return;
    }
    
    // Set QR image
    const modalImage = document.getElementById('modal-qr-image');
    if (modalImage) {
        const img = new Image();
        img.src = api.getQRImageUrl(qrData.id);
        
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
 * Sets up download buttons for different formats
 * @param {string} qrId - The QR code ID
 */
function setupDownloadButtons(qrId) {
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
async function downloadQRCode(qrId, format) {
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
 * Sets up action buttons for editing and deleting QR codes
 * @param {Object} qrData - The QR code data
 */
function setupActionButtons(qrData) {
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

/**
 * Safely hides a bootstrap modal
 * @param {string} modalId - The ID of the modal to hide
 */
function hideModal(modalId) {
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
 * Handles updating a QR code
 * @param {Event} event - The click event
 */
async function handleUpdate(event) {
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
        refreshQRList(currentPage);
    } catch (error) {
        console.error('Error updating QR code:', error);
        showError('Failed to update QR code. Please try again.');
    }
}

/**
 * Handles deleting a QR code
 * @param {Event} event - The click event
 */
async function handleDelete(event) {
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
        refreshQRList(currentPage);
    } catch (error) {
        console.error('Error deleting QR code:', error);
        showError('Failed to delete QR code. Please try again.');
    }
}

/**
 * Handles search input changes
 */
function handleSearch(event) {
    console.log('Search input changed');
    const searchInput = event.target;
    const searchValue = searchInput.value.trim();
    const clearButton = document.getElementById('clear-search-btn');
    
    // Update search term
    searchTerm = searchValue;
    
    // Show/hide clear button
    if (clearButton) {
        if (searchValue) {
            clearButton.classList.remove('d-none');
        } else {
            clearButton.classList.add('d-none');
        }
    }
    
    // Reset to first page and refresh
    refreshQRList(1);
}

/**
 * Clears the search input and resets the QR list
 */
function clearSearch() {
    console.log('Clearing search');
    searchTerm = '';
    
    // Clear search input if it exists
    const searchInput = document.getElementById('qr-search');
    if (searchInput) {
        searchInput.value = '';
    }
    
    // Hide clear button
    const clearButton = document.getElementById('clear-search-btn');
    if (clearButton) {
        clearButton.classList.add('d-none');
    }
    
    // Reset to first page and refresh
    refreshQRList(1);
}

/**
 * Handles table header sorting
 * @param {Event} event - The click event
 */
function handleSort(event) {
    const header = event.target.closest('th[data-sort]');
    if (!header) return;
    
    const sortField = header.dataset.sort;
    
    // Toggle sort direction if clicking on the same column
    if (sortField === currentSortBy) {
        currentSortDesc = !currentSortDesc;
    } else {
        currentSortBy = sortField;
        // Default sort direction based on field
        if (sortField === 'scan_count') {
            currentSortDesc = true; // Higher values first
        } else if (sortField === 'created_at') {
            currentSortDesc = true; // Newest first
        } else {
            currentSortDesc = false; // A-Z for other fields
        }
    }
    
    // Update UI to show sort direction
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    if (currentSortDesc) {
        header.classList.add('sort-desc');
    } else {
        header.classList.add('sort-asc');
    }
    
    // Debug output
    console.log(`Sorting by ${currentSortBy} in ${currentSortDesc ? 'descending' : 'ascending'} order`);
    
    refreshQRList(1); // Reset to first page when sort changes
}

/**
 * Refreshes the QR code list with pagination
 * @param {number} page - The page number to fetch
 */
async function refreshQRList(page = 1) {
    const pageSize = config.DEFAULT_VALUES.PAGE_SIZE;
    const skip = (page - 1) * pageSize;
    
    try {
        const refreshButton = document.getElementById('refresh-list');
        const searchInput = document.getElementById('qr-search');
        const searchSpinner = document.querySelector('.search-spinner');
        
        // Show loading indicators
        if (refreshButton) {
            refreshButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
            refreshButton.disabled = true;
        }
        
        if (searchInput) {
            searchInput.disabled = true;
        }
        
        if (searchSpinner) {
            searchSpinner.classList.remove('d-none');
        }
        
        const response = await api.fetchQRCodes({
            skip,
            limit: pageSize,
            qr_type: qrTypeFilter,
            search: searchTerm,
            sort_by: currentSortBy,
            sort_desc: currentSortDesc
        });
        
        // Update pagination state
        currentPage = Math.max(1, page);
        
        // Render QR codes with pagination info
        ui.renderQRList(response.items, {
            page: currentPage,
            total: response.total,
            page_size: pageSize
        });
    } catch (error) {
        console.error('Error refreshing QR codes:', error);
        ui.renderQRList([], { page: 1, total: 0, page_size: pageSize });
    } finally {
        const refreshButton = document.getElementById('refresh-list');
        const searchInput = document.getElementById('qr-search');
        const searchSpinner = document.querySelector('.search-spinner');
        
        // Hide loading indicators
        if (refreshButton) {
            refreshButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i>';
            refreshButton.disabled = false;
        }
        
        if (searchInput) {
            searchInput.disabled = false;
        }
        
        if (searchSpinner) {
            searchSpinner.classList.add('d-none');
        }
    }
}

/**
 * Handles pagination navigation
 * @param {string} direction - The direction to navigate ('prev' or 'next')
 */
function handlePagination(direction) {
    const totalPages = Math.ceil(document.getElementById('qr-count').textContent / config.DEFAULT_VALUES.PAGE_SIZE);
    
    if (direction === 'prev' && currentPage > 1) {
        refreshQRList(currentPage - 1);
    } else if (direction === 'next' && currentPage < totalPages) {
        refreshQRList(currentPage + 1);
    }
}

/**
 * Marks a form as processing or not processing
 * @param {HTMLFormElement} form - The form to mark
 * @param {boolean} isProcessing - Whether the form is processing
 */
function markFormProcessing(form, isProcessing) {
    if (isProcessing) {
        form.dataset.processing = 'true';
        form.querySelectorAll('button[type="submit"]').forEach(btn => {
            btn.disabled = true;
        });
    } else {
        form.dataset.processing = 'false';
        form.querySelectorAll('button[type="submit"]').forEach(btn => {
            btn.disabled = false;
        });
    }
}

/**
 * Handles form submission for QR code creation
 * @param {Event} event - The form submission event
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    const form = event.target;
    
    console.log('Form submission triggered', {
        formId: form.id,
        formAction: form.action,
        formMethod: form.method,
        formElements: form.elements.length
    });
    
    // Check if form is already processing
    if (form.dataset.processing === 'true') {
        console.log('Form submission already in progress');
        return;
    }
    
    // Mark form as processing
    markFormProcessing(form, true);
    
    const formData = new FormData(form);
    const formId = form.id;
    
    // Determine QR type based on form ID
    const isStatic = formId === 'create-static-qr-form';
    const isDynamic = formId === 'create-dynamic-qr-form';
    
    // Create an object to log form field values
    const formDataObj = {};
    for (const [key, value] of formData.entries()) {
        formDataObj[key] = value;
    }
    
    // Debug log form submission
    console.log('Form submission data:', {
        isStatic,
        isDynamic,
        formId,
        formData: formDataObj
    });
    
    // Common validation
    let isValid = form.checkValidity();
    console.log('Form validation result:', { isValid });
    
    if (!isValid) {
        console.log('Form validation failed, showing validation feedback');
        event.stopPropagation();
        form.classList.add('was-validated');
        markFormProcessing(form, false);
        return;
    }
    
    // Prepare data object
    const data = {
        size: parseInt(formData.get('size') || config.DEFAULT_VALUES.SIZE, 10),
        fill_color: formData.get('fill_color') || config.DEFAULT_VALUES.FILL_COLOR,
        back_color: formData.get('back_color') || config.DEFAULT_VALUES.BACK_COLOR,
        border: parseInt(formData.get('border') || config.DEFAULT_VALUES.BORDER, 10)
    };
    
    // Add title and description if provided
    const title = formData.get('title')?.trim();
    if (title) data.title = title;
    
    const description = formData.get('description')?.trim();
    if (description) data.description = description;
    
    // Add type-specific fields
    if (isStatic) {
        const content = formData.get('content')?.trim();
        if (!content) {
            console.error('Content is required for static QR codes but is missing');
            showError('Please enter content for your QR code');
            markFormProcessing(form, false);
            return;
        }
        data.content = content;
    } else if (isDynamic) {
        const redirectUrl = formatUrl(formData.get('redirect_url') || '');
        if (!isValidUrl(redirectUrl)) {
            console.error('Invalid redirect URL for dynamic QR code:', redirectUrl);
            showError('Please enter a valid URL (e.g., https://example.com)');
            markFormProcessing(form, false);
            return;
        }
        data.redirect_url = redirectUrl;
    } else {
        console.error('Unknown form type, neither static nor dynamic:', formId);
        showError('Unknown form type, please try again');
        markFormProcessing(form, false);
        return;
    }
    
    console.log('Processed form data ready for API call:', data);
    
    try {
        ui.setFormLoading(form, true);
        
        // Disable buttons to prevent multiple submissions
        form.querySelectorAll('button[type="submit"]').forEach(button => {
            button.disabled = true;
            // Add spinner to button if it exists
            const spinner = button.querySelector('.spinner-border');
            if (spinner) spinner.classList.remove('d-none');
        });
        
        // Call the appropriate API based on form type
        let response;
        
        if (isDynamic) {
            console.log('Making API request to create dynamic QR code with data:', data);
            console.log('API endpoint:', config.API.BASE_URL + config.API.ENDPOINTS.QR_DYNAMIC);
            response = await api.createDynamicQR(data);
        } else {
            console.log('Making API request to create static QR code with data:', data);
            console.log('API endpoint:', config.API.BASE_URL + config.API.ENDPOINTS.QR_STATIC);
            response = await api.createStaticQR(data);
        }
        
        console.log('QR code created successfully, API response:', response);
        
        // Store success message in localStorage to show after redirect
        const successMessage = `${isStatic ? 'Static' : 'Dynamic'} QR code created successfully!`;
        localStorage.setItem('qr_success_message', successMessage);
        
        // Reset form state
        ui.resetForm(form);
        form.classList.remove('was-validated');
        
        // Force hard navigation to the list page
        console.log('Redirecting to QR list page...');
        window.location.replace('/qr-list');
    } catch (error) {
        console.error(`Error creating ${isStatic ? 'static' : 'dynamic'} QR code:`, error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            name: error.name
        });
        showError(`Failed to create ${isStatic ? 'static' : 'dynamic'} QR code: ${error.message}`);
        
        // Re-enable the submit button
        form.querySelectorAll('button[type="submit"]').forEach(button => {
            button.disabled = false;
            // Hide spinner
            const spinner = button.querySelector('.spinner-border');
            if (spinner) spinner.classList.add('d-none');
        });
    } finally {
        ui.setFormLoading(form, false);
        markFormProcessing(form, false);
    }
}

/**
 * Handles toggling QR type filter
 * @param {string} type - QR code type filter ('static', 'dynamic', or 'all' for all)
 */
function handleQRTypeFilter(type) {
    console.log(`Filtering QR codes by type: ${type}`);
    qrTypeFilter = type === 'all' ? null : type;
    refreshQRList(1); // Reset to first page when filter changes
}

/**
 * Hides the preview and shows the placeholder
 */
function hidePreviewShowPlaceholder() {
    const previewPlaceholder = document.getElementById('qr-preview-placeholder');
    const previewContainer = document.getElementById('qr-preview');
    const loadingElement = document.getElementById('qr-preview-loading');
    
    if (previewPlaceholder) previewPlaceholder.classList.remove('d-none');
    if (previewContainer) previewContainer.classList.add('d-none');
    if (loadingElement) loadingElement.classList.add('d-none');
}

/**
 * Shows the preview with the given QR ID and hides the placeholder
 * @param {string} qrId - The QR code ID
 */
function showPreviewHidePlaceholder(qrId) {
    // IMPORTANT: This function is no longer used to prevent duplicate QR codes
    console.log('Preview functionality is disabled to prevent duplicate QR codes');
}

/**
 * Creates or updates live QR code preview from form data
 * @param {HTMLFormElement} form - The form containing QR code data
 */
async function updateLivePreview(form) {
    if (!form) return;
    
    // Skip if form is being submitted
    if (form.dataset.processing === 'true') {
        console.log('Skipping preview during form submission');
        return;
    }
    
    // Skip if preview update is already in progress
    if (previewInProgress) {
        console.log('Preview update already in progress, skipping');
        return;
    }
    
    // Clear existing timer
    if (previewTimer) {
        clearTimeout(previewTimer);
        previewTimer = null;
    }
    
    // IMPORTANT: Live preview functionality is disabled to prevent duplicate QR codes
    // Show placeholder with message
    const previewPlaceholder = document.getElementById('qr-preview-placeholder');
    const previewContainer = document.getElementById('qr-preview');
    const loadingElement = document.getElementById('qr-preview-loading');
    
    if (previewContainer) previewContainer.classList.add('d-none');
    if (loadingElement) loadingElement.classList.add('d-none');
    
    if (previewPlaceholder) {
        previewPlaceholder.classList.remove('d-none');
        const placeholderText = previewPlaceholder.querySelector('.placeholder-text');
        if (placeholderText) {
            placeholderText.textContent = 'Preview disabled - QR code will be generated upon submission';
        }
    }
    
    // Disable the download buttons since there's no QR to download yet
    const downloadButtons = [
        document.getElementById('download-qr-png'),
        document.getElementById('download-qr-svg'),
        document.getElementById('download-qr-pdf')
    ];
    
    downloadButtons.forEach(button => {
        if (button) {
            button.disabled = true;
            button.title = 'Submit the form to create and download a QR code';
        }
    });
}

/**
 * Generates a preview URL for a QR code based on form data without creating a database entry
 * @param {Object} data - The QR code data
 * @param {boolean} isStatic - Whether this is a static QR code
 * @returns {string} - The preview URL
 */
function generatePreviewUrl(data, isStatic) {
    // IMPORTANT: This function is no longer used to prevent duplicate QR codes
    console.log('Preview functionality is disabled to prevent duplicate QR codes');
    return '';
}

/**
 * Shows the preview with the given image URL
 * @param {string} imageUrl - The image URL for the preview
 */
function showPreviewWithUrl(imageUrl) {
    // IMPORTANT: This function is no longer used to prevent duplicate QR codes
    console.log('Preview functionality is disabled to prevent duplicate QR codes');
}

/**
 * Sets up download buttons for QR preview without having a real QR ID
 * @param {Object} data - The QR code data
 * @param {boolean} isStatic - Whether this is a static QR code
 */
function setupPreviewDownloadButtonsForLivePreview(data, isStatic) {
    // IMPORTANT: This function is no longer used to prevent duplicate QR codes
    console.log('Preview functionality is disabled to prevent duplicate QR codes');
}

/**
 * Initializes the application
 */
function init() {
    // Prevent multiple initialization
    if (window.isScriptInitialized) {
        console.log('Script already initialized, skipping duplicate initialization');
        return;
    }
    window.isScriptInitialized = true;
    
    // Check for stored success/error messages and display them
    const successMessage = localStorage.getItem('qr_success_message');
    if (successMessage) {
        showSuccess(successMessage);
        localStorage.removeItem('qr_success_message');
    }
    
    const errorMessage = localStorage.getItem('qr_error_message');
    if (errorMessage) {
        showError(errorMessage);
        localStorage.removeItem('qr_error_message');
    }
    
    // Initialize event listeners
    
    // Set up QR form actions - check for forms directly regardless of page
    const staticForm = document.getElementById('create-static-qr-form');
    const dynamicForm = document.getElementById('create-dynamic-qr-form');
    
    if (staticForm) {
        console.log('Static QR form found, attaching submit handler');
        staticForm.addEventListener('submit', handleFormSubmit);
        initFormValidation(staticForm);
    }
    
    if (dynamicForm) {
        console.log('Dynamic QR form found, attaching submit handler');
        dynamicForm.addEventListener('submit', handleFormSubmit);
        initFormValidation(dynamicForm);
    }
    
    // Set up QR type tab switching if tabs exist
    const qrTypeTabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    qrTypeTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            // Update the active form based on the tab
            const targetId = event.target.getAttribute('data-bs-target');
            const isStatic = targetId === '#static-qr' || targetId === '#static-qr-tab-pane';
            
            // Toggle form display if both forms exist
            if (staticForm && dynamicForm) {
                staticForm.style.display = isStatic ? 'block' : 'none';
                dynamicForm.style.display = isStatic ? 'none' : 'block';
            }
        });
    });
    
    // Check if we're on the dashboard page
    const dashboardSection = document.getElementById('dashboard-section');
    if (dashboardSection) {
        console.log('Dashboard section found, initializing dashboard-specific features');
        // Dashboard-specific initialization can go here
    }
    
    // Check if we're on the QR list page
    const qrListSection = document.getElementById('qr-list');
    if (qrListSection) {
        // Load initial QR codes
        refreshQRList();
        
        // Set up search functionality
        const searchInput = document.getElementById('qr-search');
        if (searchInput) {
            // Debounce search to avoid too many requests while typing
            searchInput.addEventListener('input', debounce(handleSearch, 500));
            
            // Clear search button
            const clearSearchBtn = document.getElementById('clear-search-btn');
            if (clearSearchBtn) {
                clearSearchBtn.addEventListener('click', clearSearch);
            }
        }
        
        // Set up refresh button
        const refreshButton = document.getElementById('refresh-list');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => refreshQRList(currentPage));
        }
        
        // Set up pagination
        const prevButton = document.getElementById('pagination-prev');
        const nextButton = document.getElementById('pagination-next');
        
        if (prevButton) {
            prevButton.addEventListener('click', () => handlePagination('prev'));
        }
        
        if (nextButton) {
            nextButton.addEventListener('click', () => handlePagination('next'));
        }
        
        // Set up sorting
        const sortableHeaders = document.querySelectorAll('[data-sort]');
        sortableHeaders.forEach(header => {
            header.addEventListener('click', handleSort);
        });
        
        // Set up QR type filter buttons
        const filterButtons = document.querySelectorAll('[data-qr-filter]');
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                filterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Set filter and refresh list
                const filterType = this.getAttribute('data-qr-filter');
                handleQRTypeFilter(filterType);
            });
        });
        
        // Handle table actions (delegate to table)
        const qrTable = document.getElementById('qr-code-list');
        if (qrTable) {
            qrTable.addEventListener('click', function(event) {
                // Note: View buttons are now direct links to detail page
                
                const updateButton = event.target.closest('.update-btn');
                if (updateButton) {
                    handleUpdate(event);
                }
                
                const deleteButton = event.target.closest('.delete-btn');
                if (deleteButton) {
                    handleDelete(event);
                }
            });
        }
    }
    
    // Initialize table sorting - set initial sort state
    const initialSortHeader = document.querySelector(`th[data-sort="${currentSortBy}"]`);
    if (initialSortHeader) {
        initialSortHeader.classList.add(currentSortDesc ? 'sort-desc' : 'sort-asc');
    }
    
    // Add event listener for URL edit save button
    const saveUrlBtn = document.getElementById('save-url-btn');
    if (saveUrlBtn) {
        saveUrlBtn.addEventListener('click', handleEditUrlSave);
    }
    
    // Add event listener for delete confirmation button
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', handleConfirmDelete);
    }
    
    // Initialize form validation for edit URL form
    const editUrlForm = document.getElementById('edit-url-form');
    if (editUrlForm) {
        initFormValidation(editUrlForm);
    }
    
    // Check if we're on the create QR page
    const qrCreatePage = document.getElementById('qr-preview-container');
    if (qrCreatePage) {
        console.log('QR preview container found, setting up live preview');
        // Create a debounced version of updateLivePreview
        const debouncedUpdatePreview = debounce(updateLivePreview, 500);
        
        if (staticForm) {
            // Add event listeners ONLY to critical fields that should trigger a preview
            // Essential field for static QR codes
            const contentField = staticForm.querySelector('#content');
            if (contentField) {
                contentField.addEventListener('input', () => debouncedUpdatePreview(staticForm));
            }
            
            // Advanced options that affect appearance
            staticForm.querySelectorAll('#staticAdvancedOptions input[type="range"], #staticAdvancedOptions input[type="color"]').forEach(input => {
                input.addEventListener('input', () => debouncedUpdatePreview(staticForm));
            });
        }
        
        if (dynamicForm) {
            // Add event listeners ONLY to critical fields that should trigger a preview
            // Essential field for dynamic QR codes
            const redirectUrlField = dynamicForm.querySelector('#redirect_url');
            if (redirectUrlField) {
                redirectUrlField.addEventListener('input', () => debouncedUpdatePreview(dynamicForm));
            }
            
            // Advanced options that affect appearance
            dynamicForm.querySelectorAll('#dynamicAdvancedOptions input[type="range"], #dynamicAdvancedOptions input[type="color"]').forEach(input => {
                input.addEventListener('input', () => debouncedUpdatePreview(dynamicForm));
            });
        }
    }
}

/**
 * Initialize form validation for a form
 * @param {HTMLFormElement} form - The form to initialize validation for
 */
function initFormValidation(form) {
    // Add class to disable browser default validation
    form.classList.add('needs-validation');
    
    // Add validation styles on input/change rather than submit only
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        // For URL fields, validate only when the user leaves the field to avoid disrupting typing
        if (input.name === 'redirect_url') {
            input.addEventListener('blur', () => {
                validateInput(input);
            });
            
            // Clear error styling when user is typing to allow input
            input.addEventListener('input', () => {
                input.classList.remove('is-invalid');
            });
        } else {
            // For other fields, validate on input as before
            input.addEventListener('input', () => {
                validateInput(input);
            });
        }
    });
    
    // Helper function to validate an input
    function validateInput(input) {
        if (input.checkValidity()) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
        }
    }
}

/**
 * Handles saving the updated redirect URL
 */
async function handleEditUrlSave() {
    const qrId = document.getElementById('edit-qr-id').value;
    const newUrl = document.getElementById('edit-redirect-url').value;
    const saveBtn = document.getElementById('save-url-btn');
    
    if (!qrId || !newUrl) {
        showError('Missing QR ID or redirect URL');
        return;
    }
    
    // Validate URL
    const formattedUrl = formatUrl(newUrl);
    if (!isValidUrl(formattedUrl)) {
        showError('Please enter a valid URL');
        return;
    }
    
    try {
        // Show loading state
        if (saveBtn) {
            const spinner = saveBtn.querySelector('.spinner-border');
            if (spinner) spinner.classList.remove('d-none');
            saveBtn.disabled = true;
        }
        
        // Call API to update URL
        await api.updateDynamicQR(qrId, formattedUrl);
        
        // Hide modal and show success message
        hideModal('editUrlModal');
        
        showSuccess('Redirect URL updated successfully');
        
        // Refresh QR list to show updated data
        refreshQRList(currentPage);
    } catch (error) {
        console.error('Error updating redirect URL:', error);
        showError('Failed to update redirect URL');
    } finally {
        // Reset loading state
        if (saveBtn) {
            const spinner = saveBtn.querySelector('.spinner-border');
            if (spinner) spinner.classList.add('d-none');
            saveBtn.disabled = false;
        }
    }
}

/**
 * Handles confirming QR code deletion
 */
async function handleConfirmDelete() {
    const qrId = document.getElementById('delete-qr-id').value;
    const deleteBtn = document.getElementById('confirm-delete-btn');
    
    if (!qrId) {
        showError('Missing QR ID');
        return;
    }
    
    try {
        // Show loading state
        if (deleteBtn) {
            const spinner = deleteBtn.querySelector('.spinner-border');
            if (spinner) spinner.classList.remove('d-none');
            deleteBtn.disabled = true;
        }
        
        // Call API to delete QR code
        await api.deleteQR(qrId);
        
        // Hide modal and show success message
        hideModal('deleteConfirmModal');
        
        showSuccess('QR code deleted successfully');
        
        // Refresh QR list to show updated data
        refreshQRList(currentPage);
    } catch (error) {
        console.error('Error deleting QR code:', error);
        showError('Failed to delete QR code');
    } finally {
        // Reset loading state
        if (deleteBtn) {
            const spinner = deleteBtn.querySelector('.spinner-border');
            if (spinner) spinner.classList.add('d-none');
            deleteBtn.disabled = false;
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if already initialized
    if (window.isScriptInitialized) {
        console.log('Script already initialized via DOMContentLoaded, skipping');
        return;
    }
    
    // Add a small delay to ensure all components are fully loaded
    setTimeout(function() {
        // Check if already initialized (in case init was called during the timeout)
        if (window.isScriptInitialized) {
            console.log('Script already initialized during timeout, skipping');
            return;
        }
        
        // Check that Bootstrap is loaded
        if (typeof bootstrap === 'undefined') {
            console.error('Bootstrap is not loaded. Check your script includes.');
            
            // Try to load Bootstrap again if missing
            const bootstrapScript = document.createElement('script');
            bootstrapScript.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js';
            bootstrapScript.integrity = 'sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz';
            bootstrapScript.crossOrigin = 'anonymous';
            bootstrapScript.onload = function() {
                console.log('Bootstrap loaded dynamically, initializing application');
                window.bootstrap = bootstrap;
                init();
            };
            document.body.appendChild(bootstrapScript);
        } else {
            console.log('Bootstrap loaded, initializing application');
            // Ensure bootstrap is globally accessible
            window.bootstrap = bootstrap;
            init();
        }
    }, 300); // Small delay to ensure everything is loaded
});

// Call init function when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', init);

// Export init function so it can be used by other modules
export { init }; 