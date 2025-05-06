/**
 * DEPRECATED: This file is being phased out in favor of a modular architecture.
 * Please use the new modules instead:
 * - modal-handler.js: Modal dialog operations
 * - form-handler.js: Form submissions and validation
 * - qr-operations.js: QR code operations (create, update, delete)
 * - list-manager.js: List pagination, sorting, filtering
 * - event-initializer.js: Initialization and event binding
 * - main.js: Entry point that imports and initializes all modules
 * 
 * This file is kept for backward compatibility and will be removed in a future update.
 */

// Show deprecation warning in console
console.warn('DEPRECATED: script.js is deprecated and will be removed in a future update. Please use the new modular architecture.');

// Re-export the init function from event-initializer.js for backward compatibility
import { init as appInit } from './event-initializer.js';

// Export init function
export function init() {
    console.warn('DEPRECATED: Using script.js init() is deprecated. Please update imports to use event-initializer.js directly.');
    return appInit();
} 