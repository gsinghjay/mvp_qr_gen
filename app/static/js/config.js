/**
 * Configuration module for the QR Code Generator application
 * Contains all API endpoints and constants
 */
export const config = {
    API: {
        // Force HTTPS for all API calls when using Traefik with TLS
        BASE_URL: window.location.origin.replace('http://', 'https://'),
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
        IMAGE_FORMAT: 'png',
        PAGE_SIZE: 10
    },
    SELECTORS: {
        FORM: '#create-qr-form',
        QR_LIST: '#qr-code-list',
        QR_IMAGE: '#qr-code-image',
        QR_TABLE_BODY: '#qr-code-list tbody',
        PAGINATION: '#qr-pagination',
        PAGINATION_PREV: '#pagination-prev',
        PAGINATION_NEXT: '#pagination-next',
        PAGINATION_INFO: '#pagination-info'
    }
}; 