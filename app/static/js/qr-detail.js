/**
 * QR Detail page script
 * This script handles the functionality of the QR code detail view page
 */
import { api } from './api.js';
import { showSuccess, showError } from './utils.js';
import { config } from './config.js';

// Get QR ID from URL path
const pathParts = window.location.pathname.split('/');
const qrId = pathParts[pathParts.length - 1];

/**
 * Initialize the page
 */
async function init() {
    if (!qrId) {
        showError('QR code ID not found in URL');
        return;
    }

    try {
        // Show loading indicator
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }

        // Fetch QR code data
        let qrData;
        try {
            qrData = await api.getQR(qrId);
            if (!qrData) {
                throw new Error('QR code not found');
            }
        } catch (apiError) {
            console.error('Error fetching QR code:', apiError);
            showError('QR code not found or unable to access data');
            return;
        }

        // Populate QR code data
        try {
            populateQRData(qrData);
        } catch (populateError) {
            console.error('Error populating QR data:', populateError);
            // Continue with other operations even if populating data fails
        }

        // Set up event listeners for buttons
        try {
            setupEventListeners(qrData);
        } catch (eventError) {
            console.error('Error setting up event listeners:', eventError);
        }

        // Update basic scan stats
        try {
            updateBasicScanStats(qrData);
        } catch (statsError) {
            console.error('Error updating scan stats:', statsError);
        }

    } catch (error) {
        console.error('Error loading QR code details:', error);
        showError('Failed to load QR code details');
    } finally {
        // Hide loading indicator
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
    }
}

/**
 * Extract short ID from the dynamic QR content
 * @param {string} content - QR code content
 * @returns {string} - Short ID for the QR code
 */
function extractShortIdFromContent(content) {
    if (!content) return '';
    
    // Try to match patterns like "/r/{shortId}" or "https://example.com/r/{shortId}"
    const match = content.match(/\/r\/([a-zA-Z0-9_-]+)(?:\?|$)/);
    if (match && match[1]) {
        return match[1];
    }
    
    // Fallback to just using the last part of the path
    const parts = content.split('/');
    return parts[parts.length - 1];
}

/**
 * Populate the page with QR code data
 * @param {Object} qrData - The QR code data
 */
function populateQRData(qrData) {
    if (!qrData) return;

    // Set QR image with logo
    const qrImage = document.getElementById('qr-image');
    if (qrImage) {
        qrImage.src = api.getQRImageUrl(qrData.id, { include_logo: true });
        qrImage.alt = `QR Code: ${qrData.id}`;
    }

    // Set basic information
    const qrIdElement = document.getElementById('qr-id');
    const qrTypeElement = document.getElementById('qr-type');
    const qrCreatedDateElement = document.getElementById('qr-created-date');
    
    if (qrIdElement) qrIdElement.value = qrData.id || '';
    if (qrTypeElement) qrTypeElement.textContent = qrData.qr_type === 'dynamic' ? 'Dynamic' : 'Static';
    if (qrCreatedDateElement) qrCreatedDateElement.textContent = new Date(qrData.created_at).toLocaleString();

    // Set content based on QR type
    const staticContentContainer = document.getElementById('static-content-container');
    const dynamicContentContainer = document.getElementById('dynamic-content-container');
    const qrContent = document.getElementById('qr-content');
    const qrRedirectUrl = document.getElementById('qr-redirect-url');
    const qrShortUrl = document.getElementById('qr-short-url');
    const dynamicActionsCard = document.getElementById('dynamic-qr-actions-card');

    if (qrData.qr_type === 'static') {
        // Show static content
        if (staticContentContainer) staticContentContainer.classList.remove('d-none');
        if (dynamicContentContainer) dynamicContentContainer.classList.add('d-none');
        if (dynamicActionsCard) dynamicActionsCard.classList.add('d-none');

        if (qrContent) {
            qrContent.value = qrData.content || '';
        }
    } else if (qrData.qr_type === 'dynamic') {
        // Show dynamic content
        if (staticContentContainer) staticContentContainer.classList.add('d-none');
        if (dynamicContentContainer) dynamicContentContainer.classList.remove('d-none');
        if (dynamicActionsCard) dynamicActionsCard.classList.remove('d-none');

        if (qrRedirectUrl) {
            qrRedirectUrl.value = qrData.redirect_url || '';
        }

        // Set visit URL button
        const visitUrlBtn = document.getElementById('visit-url-btn');
        if (visitUrlBtn && qrData.redirect_url) {
            visitUrlBtn.href = qrData.redirect_url;
        }

        // Extract short ID from content and construct short URL
        const shortId = extractShortIdFromContent(qrData.content);
        
        // Set short URL
        if (qrShortUrl) {
            const shortUrl = `${config.API.PUBLIC_URL}/r/${shortId}`;
            qrShortUrl.value = shortUrl;

            // Set visit short URL button
            const visitShortUrlBtn = document.getElementById('visit-short-url-btn');
            if (visitShortUrlBtn) {
                visitShortUrlBtn.href = shortUrl;
            }
        }
    }

    // Set document title with ID instead of title
    document.title = `QR Code: ${qrData.id}`;
}

/**
 * Update basic scan statistics from QR data
 * @param {Object} qrData - The QR code data
 */
function updateBasicScanStats(qrData) {
    // Display only the information we have from the API response
    const totalScans = document.getElementById('total-scans');
    const lastScan = document.getElementById('last-scan');
    
    if (totalScans) totalScans.textContent = qrData.scan_count || 0;
    
    if (lastScan) {
        if (qrData.last_scan_at) {
            lastScan.textContent = new Date(qrData.last_scan_at).toLocaleString();
        } else {
            lastScan.textContent = 'Never';
        }
    }
}

/**
 * Set up event listeners for buttons
 * @param {Object} qrData - The QR code data
 */
function setupEventListeners(qrData) {
    // Logo toggle switch
    const logoToggle = document.getElementById('logo-toggle');
    const qrImage = document.getElementById('qr-image');
    
    if (logoToggle && qrImage) {
        logoToggle.addEventListener('change', function() {
            // Update the QR image based on logo toggle state
            qrImage.src = api.getQRImageUrl(qrData.id, { include_logo: this.checked });
        });
    }
    
    // Copy buttons
    const copyButtons = [
        { buttonId: 'copy-id-btn', inputId: 'qr-id' },
        { buttonId: 'copy-content-btn', inputId: 'qr-content' },
        { buttonId: 'copy-url-btn', inputId: 'qr-redirect-url' },
        { buttonId: 'copy-short-url-btn', inputId: 'qr-short-url' }
    ];

    copyButtons.forEach(({ buttonId, inputId }) => {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', () => {
                const input = document.getElementById(inputId);
                if (input) {
                    input.select();
                    document.execCommand('copy');
                    showSuccess('Copied to clipboard');
                }
            });
        }
    });

    // Print button
    const printBtn = document.getElementById('print-qr-btn');
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }

    // Share button
    const shareBtn = document.getElementById('share-qr-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', () => {
            const shareModal = new bootstrap.Modal(document.getElementById('shareQrModal'));
            
            // Set share link
            const shareLink = document.getElementById('share-link');
            if (shareLink) {
                if (qrData.qr_type === 'dynamic') {
                    // For dynamic QR codes, use the short URL
                    const shortId = extractShortIdFromContent(qrData.content);
                    const shortUrl = `${config.API.PUBLIC_URL}/r/${shortId}`;
                    shareLink.value = shortUrl;
                } else {
                    // For static QR codes, use the detail page URL
                    shareLink.value = `${config.API.PUBLIC_URL}/qr-detail/${qrData.id}`;
                }
            }
            
            shareModal.show();
        });
    }

    // Copy share link button
    const copyShareLinkBtn = document.getElementById('copy-share-link-btn');
    if (copyShareLinkBtn) {
        copyShareLinkBtn.addEventListener('click', () => {
            const shareLink = document.getElementById('share-link');
            if (shareLink) {
                shareLink.select();
                document.execCommand('copy');
                showSuccess('Copied to clipboard');
            }
        });
    }

    // Social share buttons
    setupSocialShareButtons(qrData);

    // Download buttons
    setupDownloadButtons(qrData.id);

    // Edit redirect URL button (for dynamic QR codes)
    const editRedirectBtn = document.getElementById('edit-redirect-btn');
    if (editRedirectBtn && qrData.qr_type === 'dynamic') {
        editRedirectBtn.addEventListener('click', () => {
            const editModal = new bootstrap.Modal(document.getElementById('editUrlModal'));
            
            // Set current redirect URL
            const editRedirectUrl = document.getElementById('edit_redirect_url');
            if (editRedirectUrl) {
                editRedirectUrl.value = qrData.redirect_url || '';
            }
            
            editModal.show();
        });
    }

    // Save URL button
    const saveUrlBtn = document.getElementById('save-url-btn');
    if (saveUrlBtn) {
        saveUrlBtn.addEventListener('click', async () => {
            const editRedirectUrl = document.getElementById('edit_redirect_url');
            if (!editRedirectUrl) return;

            const newUrl = editRedirectUrl.value.trim();
            if (!newUrl) {
                showError('Please enter a valid URL');
                return;
            }

            try {
                // Show loading spinner
                saveUrlBtn.disabled = true;
                const spinner = saveUrlBtn.querySelector('.spinner-border');
                if (spinner) spinner.classList.remove('d-none');

                // Update the redirect URL
                await api.updateQR(qrData.id, { redirect_url: newUrl });
                
                // Update the UI
                const qrRedirectUrl = document.getElementById('qr-redirect-url');
                if (qrRedirectUrl) {
                    qrRedirectUrl.value = newUrl;
                }

                // Update the visit URL button
                const visitUrlBtn = document.getElementById('visit-url-btn');
                if (visitUrlBtn) {
                    visitUrlBtn.href = newUrl;
                }

                // Hide the modal
                const editModal = bootstrap.Modal.getInstance(document.getElementById('editUrlModal'));
                if (editModal) {
                    editModal.hide();
                }

                showSuccess('Redirect URL updated successfully');
            } catch (error) {
                console.error('Error updating redirect URL:', error);
                showError('Failed to update redirect URL');
            } finally {
                // Hide loading spinner
                saveUrlBtn.disabled = false;
                const spinner = saveUrlBtn.querySelector('.spinner-border');
                if (spinner) spinner.classList.add('d-none');
            }
        });
    }

    // Delete button
    const deleteBtn = document.getElementById('delete-qr-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
            deleteModal.show();
        });
    }

    // Confirm delete button
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            try {
                // Show loading spinner
                confirmDeleteBtn.disabled = true;
                const spinner = confirmDeleteBtn.querySelector('.spinner-border');
                if (spinner) spinner.classList.remove('d-none');

                // Delete the QR code
                await api.deleteQR(qrData.id);
                
                // Redirect to QR list page
                window.location.href = '/qr-list';
                
                showSuccess('QR code deleted successfully');
            } catch (error) {
                console.error('Error deleting QR code:', error);
                showError('Failed to delete QR code');
                
                // Hide loading spinner
                confirmDeleteBtn.disabled = false;
                const spinner = confirmDeleteBtn.querySelector('.spinner-border');
                if (spinner) spinner.classList.add('d-none');
                
                // Hide the modal
                const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
                if (deleteModal) {
                    deleteModal.hide();
                }
            }
        });
    }
}

/**
 * Set up social share buttons
 * @param {Object} qrData - The QR code data
 */
function setupSocialShareButtons(qrData) {
    let shareUrl;
    
    if (qrData.qr_type === 'dynamic') {
        // For dynamic QR codes, use the short URL
        const shortId = extractShortIdFromContent(qrData.content);
        shareUrl = `${config.API.PUBLIC_URL}/r/${shortId}`;
    } else {
        // For static QR codes, use the detail page URL
        shareUrl = `${config.API.PUBLIC_URL}/qr-detail/${qrData.id}`;
    }
    
    const shareTitle = `Check out this QR code: ${qrData.title || 'QR Code'}`;

    // Email share
    const emailBtn = document.getElementById('share-email-btn');
    if (emailBtn) {
        emailBtn.addEventListener('click', () => {
            const subject = encodeURIComponent(shareTitle);
            const body = encodeURIComponent(`I wanted to share this QR code with you: ${shareUrl}`);
            window.location.href = `mailto:?subject=${subject}&body=${body}`;
        });
    }

    // Twitter share
    const twitterBtn = document.getElementById('share-twitter-btn');
    if (twitterBtn) {
        twitterBtn.addEventListener('click', () => {
            const text = encodeURIComponent(`${shareTitle} ${shareUrl}`);
            window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
        });
    }

    // LinkedIn share
    const linkedinBtn = document.getElementById('share-linkedin-btn');
    if (linkedinBtn) {
        linkedinBtn.addEventListener('click', () => {
            const title = encodeURIComponent(shareTitle);
            const url = encodeURIComponent(shareUrl);
            window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}&title=${title}`, '_blank');
        });
    }
}

/**
 * Set up download buttons
 * @param {string} qrId - The QR code ID
 */
function setupDownloadButtons(qrId) {
    // Handle download buttons
    const downloadButtons = document.querySelectorAll('[data-format]');
    
    downloadButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const format = this.dataset.format;
            
            // Show a helpful message about logo inclusion
            const logoToggle = document.getElementById('logo-toggle');
            const message = logoToggle && logoToggle.checked ? 
                `Downloading QR code with logo as ${format.toUpperCase()}...` : 
                `Downloading QR code as ${format.toUpperCase()}...`;
            
            showSuccess(message);
            downloadQRCode(qrId, format);
        });
    });
}

/**
 * Download a QR code in different formats
 * @param {string} qrId - The QR code ID
 * @param {string} format - The format to download (png, svg, pdf)
 */
async function downloadQRCode(qrId, format) {
    try {
        // Check if logo toggle is enabled
        const logoToggle = document.getElementById('logo-toggle');
        const includeLogo = logoToggle ? logoToggle.checked : false;
        
        // Generate URL with format and logo setting
        const imageUrl = api.getQRImageUrl(qrId, { 
            format: format,
            include_logo: includeLogo
        });
        
        // Create a link and trigger download
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = `qr-code-${qrId}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
    } catch (error) {
        console.error('Error downloading QR code:', error);
        showError('Failed to download QR code');
    }
}

// Initialize the page when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', init); 