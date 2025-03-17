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
    const button = event.target.closest('button');
    if (!button) return;
    
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
    
    // Prepare data object
    const data = {
        content: formData.get('content') || '',
        size: parseInt(formData.get('size') || config.DEFAULT_VALUES.SIZE, 10),
        fill_color: formData.get('fill_color') || config.DEFAULT_VALUES.FILL_COLOR,
        back_color: formData.get('back_color') || config.DEFAULT_VALUES.BACK_COLOR,
        border: parseInt(formData.get('border') || config.DEFAULT_VALUES.BORDER, 10)
    };
    
    // Add redirect_url for dynamic QR codes
    if (formData.get('qr_type') === 'dynamic') {
        const redirectUrl = formatUrl(formData.get('redirect_url') || '');
        if (!isValidUrl(redirectUrl)) {
            showError('Please enter a valid URL (e.g., https://example.com)');
            return;
        }
        data.redirect_url = redirectUrl;
    }
    
    try {
        ui.setFormLoading(form, true);
        
        // Call the appropriate API based on QR type
        let response;
        if (formData.get('qr_type') === 'dynamic') {
            response = await api.createDynamicQR(data);
        } else {
            response = await api.createStaticQR(data);
        }
        
        showSuccess('QR code created successfully!');
        ui.resetForm(form);
        
        // Update QR list and preview
        refreshQRList(1); // Reset to first page after creation
        ui.updateQRPreview(response.id);
        
        // Switch to view tab
        const viewTab = document.querySelector('a[href="#qr-list"]');
        if (viewTab) {
            const tab = new bootstrap.Tab(viewTab);
            tab.show();
        }
    } catch (error) {
        console.error('Error creating QR code:', error);
        showError('Failed to create QR code. Please try again.');
    } finally {
        ui.setFormLoading(form, false);
    }
}

/**
 * Handles toggling QR type filter
 * @param {string} type - QR code type filter ('static', 'dynamic', or null for all)
 */
function handleQRTypeFilter(type) {
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
    
    // Add event listeners for QR code actions
    const qrList = document.querySelector(config.SELECTORS.QR_LIST);
    if (qrList) {
        qrList.addEventListener('click', event => {
            const viewButton = event.target.closest('.view-btn');
            const updateButton = event.target.closest('.update-btn');
            const deleteButton = event.target.closest('.delete-btn');
            
            if (viewButton) handleViewImage(event);
            if (updateButton) handleUpdate(event);
            if (deleteButton) handleDelete(event);
        });
        
        // Add event listeners for table header sorting
        const tableHeaders = qrList.querySelectorAll('th[data-sort]');
        tableHeaders.forEach(header => {
            header.addEventListener('click', handleSort);
        });
    }
    
    // Add event listener for form submission
    const form = document.querySelector(config.SELECTORS.FORM);
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
    
    // Add event listener for refresh button
    const refreshButton = document.getElementById('refresh-list');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => refreshQRList(currentPage));
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
    
    // Add event listeners for QR type filter
    document.querySelectorAll('[data-qr-filter]').forEach(button => {
        button.addEventListener('click', () => {
            const type = button.dataset.qrFilter;
            handleQRTypeFilter(type);
            
            // Update active state
            document.querySelectorAll('[data-qr-filter]').forEach(btn => {
                btn.classList.remove('active');
            });
            button.classList.add('active');
        });
    });
    
    // Add event listener for search input with debounce
    const searchInput = document.getElementById('qr-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 500));
        
        // Add clear search functionality with "x" button or Escape key
        searchInput.addEventListener('keyup', event => {
            if (event.key === 'Escape') {
                clearSearch();
            }
        });
    }
    
    // Add event listener for clear search button
    const clearSearchButton = document.querySelector('.clear-search');
    if (clearSearchButton) {
        clearSearchButton.addEventListener('click', clearSearch);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', init); 