/**
 * Configuration module for the QR Code Generator application
 * Contains all API endpoints and constants
 */
export const config = {
    API: {
        BASE_URL: window.location.origin,  // Use the current origin (protocol + host)
        ENDPOINTS: {
            QR_LIST: '/api/v1/qr',
            QR_DYNAMIC: '/api/v1/qr/dynamic',
            QR_IMAGE: (id) => `/api/v1/qr/${id}/image`,
            QR_UPDATE: (id) => `/api/v1/qr/${id}`,
            QR_DELETE: (id) => `/api/v1/qr/${id}`
        }
    },
    DEFAULT_VALUES: {
        FILL_COLOR: '#000000',
        BACK_COLOR: '#FFFFFF',
        SIZE: 10,
        BORDER: 4,
        IMAGE_FORMAT: 'png'
    },
    SELECTORS: {
        FORM: '#create-qr-form',
        QR_LIST: '#qr-code-list',
        QR_IMAGE: '#qr-code-image',
        QR_TABLE_BODY: '#qr-code-list tbody'
    }
}; 