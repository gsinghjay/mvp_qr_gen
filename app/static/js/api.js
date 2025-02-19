/**
 * API service module for the QR Code Generator application
 */
import { config } from './config.js';
import { showError } from './utils.js';

/**
 * Handles API errors and returns JSON response
 * @param {Response} response - The fetch response object
 * @returns {Promise} - JSON response or throws error
 */
async function handleResponse(response) {
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'API request failed');
    }
    return response.json();
}

export const api = {
    /**
     * Fetches all QR codes
     * @returns {Promise<Array>} - Array of QR codes
     */
    async fetchQRCodes() {
        try {
            const response = await fetch(`${config.API.BASE_URL}${config.API.ENDPOINTS.QR_LIST}`);
            return handleResponse(response);
        } catch (error) {
            showError(`Error fetching QR codes: ${error.message}`);
            throw error;
        }
    },

    /**
     * Creates a new dynamic QR code
     * @param {Object} data - QR code data
     * @returns {Promise<Object>} - Created QR code
     */
    async createDynamicQR(data) {
        try {
            const response = await fetch(`${config.API.BASE_URL}${config.API.ENDPOINTS.QR_DYNAMIC}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            return handleResponse(response);
        } catch (error) {
            showError(`Error creating QR code: ${error.message}`);
            throw error;
        }
    },

    /**
     * Updates an existing QR code
     * @param {string} id - QR code ID
     * @param {string} redirectUrl - New redirect URL
     * @returns {Promise<Object>} - Updated QR code
     */
    async updateQR(id, redirectUrl) {
        try {
            const response = await fetch(`${config.API.BASE_URL}${config.API.ENDPOINTS.QR_UPDATE(id)}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ redirect_url: redirectUrl })
            });
            return handleResponse(response);
        } catch (error) {
            showError(`Error updating QR code: ${error.message}`);
            throw error;
        }
    },

    /**
     * Deletes a QR code
     * @param {string} id - QR code ID
     * @returns {Promise<void>}
     */
    async deleteQR(id) {
        try {
            const response = await fetch(`${config.API.BASE_URL}${config.API.ENDPOINTS.QR_DELETE(id)}`, {
                method: 'DELETE'
            });
            if (!response.ok) {
                throw new Error('Failed to delete QR code');
            }
        } catch (error) {
            showError(`Error deleting QR code: ${error.message}`);
            throw error;
        }
    },

    /**
     * Gets the image URL for a QR code
     * @param {string} id - QR code ID
     * @returns {string} - QR code image URL
     */
    getQRImageUrl(id) {
        return `${config.API.BASE_URL}${config.API.ENDPOINTS.QR_IMAGE(id)}`;
    }
}; 