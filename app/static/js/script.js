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
 * Handles searching QR codes
 * @param {Event} event - The input event
 */
function handleSearch(event) {
    const searchInput = event.target;
    const searchValue = searchInput.value.trim();
    searchTerm = searchValue || null;
    
    // Debug output
    console.log(`Search term: "${searchTerm}"`);
    
    // Show/hide clear button based on search input
    const clearButton = document.querySelector('.clear-search');
    if (clearButton) {
        if (searchValue) {
            clearButton.classList.remove('d-none');
        } else {
            clearButton.classList.add('d-none');
        }
    }
    
    refreshQRList(1); // Reset to first page when search changes
}

/**
 * Clears the search input
 */
function clearSearch() {
    const searchInput = document.getElementById('qr-search');
    if (searchInput) {
        searchInput.value = '';
        searchTerm = null;
        
        // Hide clear button
        const clearButton = document.querySelector('.clear-search');
        if (clearButton) {
            clearButton.classList.add('d-none');
        }
        
        refreshQRList(1);
        searchInput.focus();
    }
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
 * Handles form submission for creating a new QR code
 * @param {Event} event - The submit event
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const formId = form.id;
    
    // Determine QR type based on form ID
    const isStatic = formId === 'create-static-qr-form';
    const isDynamic = formId === 'create-dynamic-qr-form';
    
    // Common validation
    let isValid = form.checkValidity();
    if (!isValid) {
        event.stopPropagation();
        form.classList.add('was-validated');
        return;
    }
    
    // Prepare data object
    const data = {
        size: parseInt(formData.get('size') || config.DEFAULT_VALUES.SIZE, 10),
        fill_color: formData.get('fill_color') || config.DEFAULT_VALUES.FILL_COLOR,
        back_color: formData.get('back_color') || config.DEFAULT_VALUES.BACK_COLOR,
        border: parseInt(formData.get('border') || config.DEFAULT_VALUES.BORDER, 10),
        title: formData.get('title') || '',
        description: formData.get('description') || ''
    };
    
    // Add type-specific fields
    if (isStatic) {
        const content = formData.get('content')?.trim();
        if (!content) {
            showError('Please enter content for your QR code');
            return;
        }
        data.content = content;
    } else if (isDynamic) {
        const redirectUrl = formatUrl(formData.get('redirect_url') || '');
        if (!isValidUrl(redirectUrl)) {
            showError('Please enter a valid URL (e.g., https://example.com)');
            return;
        }
        data.redirect_url = redirectUrl;
    }
    
    try {
        ui.setFormLoading(form, true);
        
        // Call the appropriate API based on form type
        let response;
        if (isDynamic) {
            response = await api.createDynamicQR(data);
        } else {
            response = await api.createStaticQR(data);
        }
        
        showSuccess(`${isStatic ? 'Static' : 'Dynamic'} QR code created successfully!`);
        ui.resetForm(form);
        form.classList.remove('was-validated');
        
        // Update QR list and preview
        refreshQRList(1); // Reset to first page after creation
        ui.updateQRPreview(response.id);
        
        // Switch to view tab - direct approach without Bootstrap Tab API
        try {
            // Get the tab element that should be shown
            const viewTab = document.querySelector('a[href="#qr-list"]');
            if (viewTab) {
                // Find parent tab container
                const tabContainer = viewTab.closest('.nav-tabs, [role="tablist"]');
                if (tabContainer) {
                    // Deactivate all tabs first
                    tabContainer.querySelectorAll('.nav-link').forEach(tab => {
                        tab.classList.remove('active');
                        tab.setAttribute('aria-selected', 'false');
                    });
                    
                    // Activate our tab
                    viewTab.classList.add('active');
                    viewTab.setAttribute('aria-selected', 'true');
                    
                    // Hide all tab panes
                    const tabContentContainer = document.querySelector('.tab-content');
                    if (tabContentContainer) {
                        tabContentContainer.querySelectorAll('.tab-pane').forEach(pane => {
                            pane.classList.remove('show', 'active');
                        });
                        
                        // Show our pane
                        const targetPane = document.querySelector(viewTab.getAttribute('href'));
                        if (targetPane) {
                            targetPane.classList.add('show', 'active');
                        }
                    }
                    
                    // Optional: Scroll to the top of the tab content
                    tabContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        } catch (tabError) {
            console.warn("Error switching tabs:", tabError);
            // Last resort - try direct click
            try {
                document.querySelector('a[href="#qr-list"]')?.click();
            } catch (clickError) {
                console.error("Failed to switch tabs:", clickError);
            }
        }
    } catch (error) {
        console.error(`Error creating ${isStatic ? 'static' : 'dynamic'} QR code:`, error);
        showError(`Failed to create ${isStatic ? 'static' : 'dynamic'} QR code. Please try again.`);
    } finally {
        ui.setFormLoading(form, false);
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
 * Initializes the application
 */
function init() {
    // Initialize table sorting - set initial sort state
    const initialSortHeader = document.querySelector(`th[data-sort="${currentSortBy}"]`);
    if (initialSortHeader) {
        initialSortHeader.classList.add(currentSortDesc ? 'sort-desc' : 'sort-asc');
    }
    
    // Initialize QR list
    refreshQRList();
    
    // Add event listeners for QR code actions with better delegation
    const qrList = document.querySelector(config.SELECTORS.QR_LIST);
    if (qrList) {
        qrList.addEventListener('click', event => {
            // Find all possible buttons the click might be targeting
            const viewButton = event.target.closest('.view-btn');
            const updateButton = event.target.closest('.update-btn');
            const deleteButton = event.target.closest('.delete-btn');
            
            // Call appropriate handler based on which button was clicked
            if (viewButton) {
                event.preventDefault(); // Prevent default modal behavior
                handleViewImage(event);
            } else if (updateButton) {
                handleUpdate(event);
            } else if (deleteButton) {
                handleDelete(event);
            }
        });
        
        // Add event listeners for table header sorting
        const tableHeaders = qrList.querySelectorAll('th[data-sort]');
        tableHeaders.forEach(header => {
            header.addEventListener('click', handleSort);
        });
    }
    
    // Add event listeners for form submissions
    const staticForm = document.querySelector(config.SELECTORS.STATIC_FORM);
    const dynamicForm = document.querySelector(config.SELECTORS.DYNAMIC_FORM);
    
    if (staticForm) {
        staticForm.addEventListener('submit', handleFormSubmit);
        initFormValidation(staticForm);
    }
    
    if (dynamicForm) {
        dynamicForm.addEventListener('submit', handleFormSubmit);
        initFormValidation(dynamicForm);
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
    
    // Add event listener for refresh button
    const refreshButton = document.getElementById('refresh-list');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => refreshQRList(currentPage));
    }
    
    // Add event listeners for search box
    const searchBox = document.getElementById('qr-search');
    if (searchBox) {
        searchBox.addEventListener('input', debounce(handleSearch, 500));
        searchBox.addEventListener('keydown', event => {
            if (event.key === 'Escape') {
                searchBox.value = '';
                clearSearch();
            }
        });
    }
    
    // Add event listeners for pagination
    const prevButton = document.querySelector(config.SELECTORS.PAGINATION_PREV);
    const nextButton = document.querySelector(config.SELECTORS.PAGINATION_NEXT);
    
    if (prevButton) {
        prevButton.addEventListener('click', () => handlePagination('prev'));
    }
    
    if (nextButton) {
        nextButton.addEventListener('click', () => handlePagination('next'));
    }
    
    // Add event listeners for QR type filter buttons
    const filterButtons = document.querySelectorAll('button[data-qr-filter]');
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Update active state visual indication
                filterButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Get filter value from the clicked button
                const filterType = button.dataset.qrFilter;
                handleQRTypeFilter(filterType);
            });
        });
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
        input.addEventListener('input', () => {
            if (input.checkValidity()) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }
        });
    });
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
    // Add a small delay to ensure all components are fully loaded
    setTimeout(function() {
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