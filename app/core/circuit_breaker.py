"""
Circuit breaker implementation for service resilience.

This module provides circuit breaker functionality using the pybreaker library
to protect against failures in new service implementations and ensure graceful
fallback to legacy implementations.
"""

import logging
from typing import Any

import pybreaker

from .config import settings
from .metrics_logger import MetricsLogger

logger = logging.getLogger(__name__)


class NewQRGenerationServiceListener(pybreaker.CircuitBreakerListener):
    """
    Circuit breaker listener for NewQRGenerationService.
    
    This listener handles state changes, failures, and successes for the
    NewQRGenerationService circuit breaker, logging events and updating metrics.
    """
    
    def __init__(self, service_name: str = "NewQRGenerationService"):
        """
        Initialize the circuit breaker listener.
        
        Args:
            service_name: Name of the service for logging and metrics
        """
        self.service_name = service_name
    
    def state_change(self, cb: pybreaker.CircuitBreaker, old_state: pybreaker.CircuitBreakerState, new_state: pybreaker.CircuitBreakerState) -> None:
        """
        Handle circuit breaker state changes.
        
        Args:
            cb: The circuit breaker instance
            old_state: Previous state
            new_state: New state
        """
        state_names = {
            pybreaker.STATE_CLOSED: "closed",
            pybreaker.STATE_OPEN: "open", 
            pybreaker.STATE_HALF_OPEN: "half_open"
        }
        
        old_state_name = state_names.get(old_state, "unknown")
        new_state_name = state_names.get(new_state, "unknown")
        
        logger.info(f"Circuit breaker {cb.name} state changed from {old_state_name} to {new_state_name}")
        
        # Update metrics with new state
        MetricsLogger.set_circuit_breaker_state(
            service=self.service_name,
            operation="qr_generation",
            state=new_state_name
        )
    
    def failure(self, cb: pybreaker.CircuitBreaker, exception: Exception) -> None:
        """
        Handle circuit breaker failures.
        
        Args:
            cb: The circuit breaker instance
            exception: The exception that caused the failure
        """
        error_type = type(exception).__name__
        logger.warning(f"Circuit breaker {cb.name} recorded failure: {error_type}: {str(exception)}")
        
        # Log failure metrics
        MetricsLogger.log_circuit_breaker_failure(
            service=self.service_name,
            operation="qr_generation", 
            error_type=error_type
        )
    
    def success(self, cb: pybreaker.CircuitBreaker) -> None:
        """
        Handle circuit breaker successes.
        
        Args:
            cb: The circuit breaker instance
        """
        logger.debug(f"Circuit breaker {cb.name} recorded success")
        # Note: We don't need to log success metrics as they're implicit
        # in the absence of failures and the circuit being closed


def get_new_qr_generation_breaker() -> pybreaker.CircuitBreaker:
    """
    Create and configure a circuit breaker for NewQRGenerationService.
    
    This function creates a circuit breaker instance configured with values
    from application settings and attaches a listener for monitoring.
    
    Returns:
        Configured CircuitBreaker instance for NewQRGenerationService
    """
    # Create the circuit breaker with configuration from settings
    breaker = pybreaker.CircuitBreaker(
        fail_max=settings.QR_GENERATION_CB_FAIL_MAX,
        reset_timeout=settings.QR_GENERATION_CB_RESET_TIMEOUT,
        name="NewQRGenerationService"
    )
    
    # Attach the listener for monitoring and metrics
    listener = NewQRGenerationServiceListener()
    breaker.add_listener(listener)
    
    # Initialize metrics with closed state
    MetricsLogger.set_circuit_breaker_state(
        service="NewQRGenerationService",
        operation="qr_generation",
        state="closed"
    )
    
    logger.info(f"Created circuit breaker for NewQRGenerationService with fail_max={settings.QR_GENERATION_CB_FAIL_MAX}, reset_timeout={settings.QR_GENERATION_CB_RESET_TIMEOUT}")
    
    return breaker 