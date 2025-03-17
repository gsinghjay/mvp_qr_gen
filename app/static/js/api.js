/**
 * API service module for the QR Code Generator application
 * @typedef {Object} QRCodeCreate
 * @property {string} content - Content for the QR code (max 2048 chars)
 * @property {string} [fill_color='#000000'] - Fill color in hex format
 * @property {string} [back_color='#FFFFFF'] - Background color in hex format
 * @property {number} [size=10] - Size of QR code (1-100)
 * @property {number} [border=4] - Border size (0-20)
 * @property {string} [redirect_url] - Redirect URL for dynamic QR codes
 */

/**
 * @typedef {Object} QRCodeUpdate
 * @property {string} redirect_url - New redirect URL
 */

/**
 * @typedef {Object} QRCodeResponse
 * @property {string} id - QR code ID
 * @property {string} content - QR code content
 * @property {string} qr_type - Type of QR code (static/dynamic)
 * @property {string} created_at - Creation timestamp
 * @property {number} scan_count - Number of scans
 * @property {string} [redirect_url] - Redirect URL for dynamic QR codes
 * @property {string} [last_scan_at] - Last scan timestamp
 */

import { config } from './config.js';
import { showError } from './utils.js';

/**
 * Handles API errors and returns JSON response
 * @param {Response} response - The fetch response object
 * @returns {Promise} - JSON response or throws error
 */
async function handleResponse(response) {
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || 'API request failed');
    }
    return data;
}

/**
 * Creates fetch options with proper configuration for development/production
 * @param {Object} options - Fetch options to extend
 * @returns {Object} - Extended fetch options
 */
function createFetchOptions(options = {}) {
    // In development, we need to accept self-signed certificates
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return {
            ...options,
            mode: 'cors',
            credentials: 'same-origin',
        };
    }
    return options;
}

export const api = {
    /**
     * Fetches QR codes with pagination and optional filtering
     * @param {Object} options - Query options
     * @param {number} [options.skip=0] - Number of records to skip
     * @param {number} [options.limit=10] - Number of records to return
     * @param {string} [options.qr_type] - Filter by QR type (static/dynamic)
     * @param {string} [options.search] - Search term for filtering by content or URL
     * @param {string} [options.sort_by] - Field to sort by (created_at, scan_count, etc.)
     * @param {boolean} [options.sort_desc=false] - Sort in descending order if true
     * @returns {Promise<{items: QRCodeResponse[], total: number, page: number, page_size: number}>}
     */
    async fetchQRCodes({ skip = 0, limit = 10, qr_type = null, search = null, sort_by = null, sort_desc = false } = {}) {
        try {
            const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() });
            if (qr_type) params.append('qr_type', qr_type);
            if (search) params.append('search', search);
            if (sort_by) {
                params.append('sort_by', sort_by);
                if (sort_desc) {
                    params.append('sort_desc', 'true');
                }
            }
            
            // Debug output
            console.log('API Request:', {
                endpoint: `${config.API.BASE_URL}${config.API.ENDPOINTS.QR_LIST}?${params}`,
                params: {
                    skip,
                    limit,
                    qr_type,
                    search,
                    sort_by,
                    sort_desc
                }
            });
            
            const response = await fetch(
                `${config.API.BASE_URL}${config.API.ENDPOINTS.QR_LIST}?${params}`,
                createFetchOptions()
            );
            const data = await handleResponse(response);
            
            // Debug output
            console.log('API Response:', {
                total: data.total,
                items: data.items.length
            });
            
            // Ensure we always return an object with items array
            return {
                items: data.items || [],
                total: data.total || 0,
                page: data.page || 1,
                page_size: data.page_size || limit
            };
        } catch (error) {
            console.error(`Error fetching QR codes: ${error.message}`);
            // Return empty result set on error
            return {
                items: [],
                total: 0,
                page: 1,
                page_size: limit
            };
        }
    },

    /**
     * Get a specific QR code by ID
     * @param {string} id - QR code ID
     * @returns {Promise<QRCodeResponse>}
     */
    async getQR(id) {
        try {
            const response = await fetch(
                `${config.API.BASE_URL}/api/v1/qr/${id}`,
                createFetchOptions()
            );
            return handleResponse(response);
        } catch (error) {
            showError(`Error fetching QR code: ${error.message}`);
            throw error;
        }
    },

    /**
     * Creates a new static QR code
     * @param {QRCodeCreate} data - QR code data
     * @returns {Promise<QRCodeResponse>}
     */
    async createStaticQR(data) {
        try {
            const response = await fetch(
                `${config.API.BASE_URL}/api/v1/qr/static`,
                createFetchOptions({
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
            );
            return handleResponse(response);
        } catch (error) {
            showError(`Error creating static QR code: ${error.message}`);
            throw error;
        }
    },

    /**
     * Creates a new dynamic QR code
     * @param {QRCodeCreate} data - QR code data
     * @returns {Promise<QRCodeResponse>}
     */
    async createDynamicQR(data) {
        try {
            const response = await fetch(
                `${config.API.BASE_URL}${config.API.ENDPOINTS.QR_DYNAMIC}`,
                createFetchOptions({
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
            );
            return handleResponse(response);
        } catch (error) {
            showError(`Error creating dynamic QR code: ${error.message}`);
            throw error;
        }
    },

    /**
     * Updates any QR code by ID
     * @param {string} id - QR code ID
     * @param {QRCodeUpdate} data - Update data
     * @returns {Promise<QRCodeResponse>}
     */
    async updateQR(id, data) {
        try {
            const response = await fetch(
                `${config.API.BASE_URL}/api/v1/qr/${id}`,
                createFetchOptions({
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
            );
            return handleResponse(response);
        } catch (error) {
            showError(`Error updating QR code: ${error.message}`);
            throw error;
        }
    },

    /**
     * Updates a dynamic QR code's redirect URL
     * @param {string} id - QR code ID
     * @param {string} redirectUrl - New redirect URL
     * @returns {Promise<QRCodeResponse>}
     */
    async updateDynamicQR(id, redirectUrl) {
        try {
            const response = await fetch(
                `${config.API.BASE_URL}/api/v1/qr/dynamic/${id}`,
                createFetchOptions({
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ redirect_url: redirectUrl })
                })
            );
            return handleResponse(response);
        } catch (error) {
            showError(`Error updating dynamic QR code: ${error.message}`);
            throw error;
        }
    },

    /**
     * Gets the QR code image URL
     * @param {string} id - QR code ID
     * @param {Object} options - Image options
     * @param {string} [options.format='png'] - Image format (png/jpeg/jpg/svg/webp)
     * @param {number} [options.quality] - Image quality (1-100, for jpeg/webp)
     * @returns {string} - QR code image URL
     */
    getQRImageUrl(id, { format = 'png', quality = null } = {}) {
        const params = new URLSearchParams({ image_format: format });
        if (quality !== null) params.append('image_quality', quality.toString());
        return `${config.API.BASE_URL}/api/v1/qr/${id}/image?${params}`;
    },

    /**
     * Gets the redirect URL for a QR code
     * @param {string} shortId - Short ID for the QR code
     * @returns {string} - Redirect URL
     */
    getRedirectUrl(shortId) {
        return `${config.API.BASE_URL}/r/${shortId}`;
    },

    /**
     * Deletes a QR code by ID
     * @param {string} id - QR code ID
     * @returns {Promise<void>}
     */
    async deleteQR(id) {
        try {
            const response = await fetch(
                `${config.API.BASE_URL}/api/v1/qr/${id}`,
                createFetchOptions({
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
            );
            
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || `Failed to delete QR code: ${response.status}`);
            }
            
            return true;
        } catch (error) {
            showError(`Error deleting QR code: ${error.message}`);
            throw error;
        }
    }
};