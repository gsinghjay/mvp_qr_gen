/**
 * List Manager Module for QR Code Generator Application
 * Manages QR code list operations, including pagination, sorting, filtering, and search
 */
import { config } from './config.js';
import { api } from './api.js';
import { ui } from './ui.js';
import { debounce } from './utils.js';

// State variables for list management
let currentPage = 1;
let qrTypeFilter = null;
let searchTerm = null;
let currentSortBy = 'created_at'; // Default sort by creation date
let currentSortDesc = true; // Default sort newest first

/**
 * Refreshes the QR code list with pagination
 * @param {number} page - The page number to fetch
 */
export async function refreshQRList(page = 1) {
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
export function handlePagination(direction) {
    const totalPages = Math.ceil(document.getElementById('qr-count').textContent / config.DEFAULT_VALUES.PAGE_SIZE);
    
    if (direction === 'prev' && currentPage > 1) {
        refreshQRList(currentPage - 1);
    } else if (direction === 'next' && currentPage < totalPages) {
        refreshQRList(currentPage + 1);
    }
}

/**
 * Handles search input changes
 */
export function handleSearch(event) {
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
export function clearSearch() {
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
export function handleSort(event) {
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
 * Handles toggling QR type filter
 * @param {string} type - QR code type filter ('static', 'dynamic', or 'all' for all)
 */
export function handleQRTypeFilter(type) {
    console.log(`Filtering QR codes by type: ${type}`);
    qrTypeFilter = type === 'all' ? null : type;
    refreshQRList(1); // Reset to first page when filter changes
}

/**
 * Initialize table sorting
 */
export function initTableSorting() {
    // Set initial sort state
    const initialSortHeader = document.querySelector(`th[data-sort="${currentSortBy}"]`);
    if (initialSortHeader) {
        initialSortHeader.classList.add(currentSortDesc ? 'sort-desc' : 'sort-asc');
    }
}

/**
 * Set up list search functionality
 */
export function setupSearch() {
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
}

/**
 * Get the current page
 * @returns {number} - The current page number
 */
export function getCurrentPage() {
    return currentPage;
}

/**
 * Export state variables for external access
 */
export const listState = {
    get currentPage() { return currentPage; },
    get qrTypeFilter() { return qrTypeFilter; },
    get searchTerm() { return searchTerm; },
    get currentSortBy() { return currentSortBy; },
    get currentSortDesc() { return currentSortDesc; }
}; 