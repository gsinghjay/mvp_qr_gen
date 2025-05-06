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
    // First check if the response is ok (status in the range 200-299)
    if (!response.ok) {
        // Try to get error details from the response body
        let errorMessage = `API request failed with status ${response.status}`;
        try {
            const errorData = await response.json();
            if (errorData.detail) {
                errorMessage = errorData.detail;
            }
        } catch (e) {
            // If parsing JSON fails, try to get the text
            try {
                const errorText = await response.text();
                if (errorText) {
                    errorMessage += `: ${errorText}`;
                }
            } catch (textError) {
                // If even getting text fails, just use the status
                console.error('Could not parse error response', textError);
            }
        }
        
        console.error('API Error:', errorMessage);
        throw new Error(errorMessage);
    }
    
    // For successful responses, parse the JSON
    try {
        return await response.json();
    } catch (jsonError) {
        console.error('Error parsing JSON response', jsonError);
        throw new Error('Invalid JSON response from API');
    }
}

/**
 * Creates fetch options with proper configuration for development/production
 * @param {Object} options - Fetch options to extend
 * @returns {Object} - Extended fetch options
 */
function createFetchOptions(options = {}) {
    // Clone the options to avoid modifying the original
    const fetchOptions = { ...options };
    
    // Always include credentials for same-origin requests
    fetchOptions.credentials = 'same-origin';
    
    // Add CORS mode for cross-origin requests
    if (window.location.hostname !== new URL(config.API.BASE_URL).hostname) {
        fetchOptions.mode = 'cors';
    }
    
    console.log('Fetch options:', fetchOptions);
    
    return fetchOptions;
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
            const apiUrl = `${config.API.BASE_URL}${config.API.ENDPOINTS.QR_DETAIL(id)}`;
            
            console.log('Fetching QR code:', apiUrl);
            
            const response = await fetch(
                apiUrl,
                createFetchOptions()
            );
            
            // Log response status
            console.log('API Response status:', response.status);
            
            return handleResponse(response);
        } catch (error) {
            console.error('Error fetching QR code:', error);
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
            // Ensure URL has https:// for production environments
            const apiUrl = `${config.API.BASE_URL}${config.API.ENDPOINTS.QR_STATIC}`;
            
            // Debug output
            console.log('Creating static QR code with:', {
                url: apiUrl,
                data: data
            });
            
            const response = await fetch(
                apiUrl,
                createFetchOptions({
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
            );
            
            // Log response status
            console.log('API Response status:', response.status);
            
            // If not OK, try to log response body
            if (!response.ok) {
                const errorBody = await response.text();
                console.error('API Error response:', errorBody);
                throw new Error(`API request failed with status ${response.status}: ${errorBody}`);
            }
            
            const responseData = await response.json();
            console.log('API Success response:', responseData);
            return responseData;
        } catch (error) {
            console.error('Error creating static QR code:', error);
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
            // Ensure URL has https:// for production environments
            const apiUrl = `${config.API.BASE_URL}${config.API.ENDPOINTS.QR_DYNAMIC}`;
            
            // Debug output
            console.log('Creating dynamic QR code with:', {
                url: apiUrl,
                data: data
            });
            
            const response = await fetch(
                apiUrl,
                createFetchOptions({
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
            );
            
            // Log response status
            console.log('API Response status:', response.status);
            
            // If not OK, try to log response body
            if (!response.ok) {
                const errorBody = await response.text();
                console.error('API Error response:', errorBody);
                throw new Error(`API request failed with status ${response.status}: ${errorBody}`);
            }
            
            const responseData = await response.json();
            console.log('API Success response:', responseData);
            return responseData;
        } catch (error) {
            console.error('Error creating dynamic QR code:', error);
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
     * Gets the URL for a QR code image
     * @param {string} id - QR code ID
     * @param {Object} options - Image options
     * @param {string} [options.format='png'] - Image format (png, svg, jpeg, webp)
     * @param {number} [options.quality=null] - Image quality (1-100, for lossy formats)
     * @param {boolean} [options.include_logo=false] - Whether to include the logo
     * @returns {string} - QR image URL
     */
    getQRImageUrl(id, { format = 'png', quality = null, include_logo = false } = {}) {
        if (!id) {
            console.warn('Missing QR ID for getQRImageUrl');
            return '';
        }
        
        const params = new URLSearchParams({ image_format: format });
        if (quality !== null) params.append('image_quality', quality.toString());
        if (include_logo) params.append('include_logo', 'true');
        
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
     * Deletes a QR code
     * @param {string} id - QR code ID
     * @returns {Promise<void>}
     */
    async deleteQR(id) {
        try {
            const response = await fetch(
                `${config.API.BASE_URL}/api/v1/qr/${id}`,
                createFetchOptions({ method: 'DELETE' })
            );
            return handleResponse(response);
        } catch (error) {
            console.error(`Error deleting QR code: ${error.message}`);
            throw error;
        }
    },

    // Analytics functions removed - not supported by backend
};