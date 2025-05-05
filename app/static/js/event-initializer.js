/**
 * Event Initializer Module for QR Code Generator Application
 * Handles initialization and binding of event handlers
 */
import { handleFormSubmit, initFormValidation, handleEditUrlSave, handleConfirmDelete } from './form-handler.js';
import { handleViewImage, handleUpdate, handleDelete } from './qr-operations.js';
import { refreshQRList, handlePagination, handleQRTypeFilter, handleSort, initTableSorting, setupSearch } from './list-manager.js';
import { showError, showSuccess } from './utils.js';
import { config } from './config.js';

/**
 * Handles sidebar toggle
 */
export function handleSidebarToggle() {
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    sidebar.classList.toggle('active');
    content.classList.toggle('active');
}

/**
 * Initializes the application
 */
export function init() {
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
        setupSearch();
        
        // Set up refresh button
        const refreshButton = document.getElementById('refresh-list');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => refreshQRList(window.currentPage));
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
        
        // Initialize table sorting
        initTableSorting();
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
    
    // Set up sidebar toggle if sidebar exists
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', handleSidebarToggle);
    }
}

// Make refreshQRList globally available for external use
window.refreshQRList = refreshQRList; 