/**
 * Form Handler Module for QR Code Generator Application
 * Manages form submissions and validation
 */
import { config } from './config.js';
import { api } from './api.js';
import { ui } from './ui.js';
import { isValidUrl, formatUrl, showSuccess, showError } from './utils.js';

/**
 * Initialize form validation for a form
 * @param {HTMLFormElement} form - The form to initialize validation for
 */
export function initFormValidation(form) {
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
 * Marks a form as processing or not processing
 * @param {HTMLFormElement} form - The form to mark
 * @param {boolean} isProcessing - Whether the form is processing
 */
export function markFormProcessing(form, isProcessing) {
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
export async function handleFormSubmit(event) {
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
 * Handles saving the updated redirect URL
 */
export async function handleEditUrlSave() {
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
        if (typeof hideModal === 'function') {
            hideModal('editUrlModal');
        } else {
            // Fallback if modal handler not available
            const modalElement = document.getElementById('editUrlModal');
            if (modalElement && bootstrap) {
                const modalInstance = bootstrap.Modal.getInstance(modalElement);
                if (modalInstance) modalInstance.hide();
            }
        }
        
        showSuccess('Redirect URL updated successfully');
        
        // Refresh QR list to show updated data
        if (typeof refreshQRList === 'function') {
            refreshQRList(currentPage);
        } else {
            // Fallback if refreshQRList not available
            window.location.reload();
        }
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
export async function handleConfirmDelete() {
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
        if (typeof hideModal === 'function') {
            hideModal('deleteConfirmModal');
        } else {
            // Fallback if modal handler not available
            const modalElement = document.getElementById('deleteConfirmModal');
            if (modalElement && bootstrap) {
                const modalInstance = bootstrap.Modal.getInstance(modalElement);
                if (modalInstance) modalInstance.hide();
            }
        }
        
        showSuccess('QR code deleted successfully');
        
        // Refresh QR list to show updated data
        if (typeof refreshQRList === 'function') {
            refreshQRList(currentPage);
        } else {
            // Fallback if refreshQRList not available
            window.location.reload();
        }
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