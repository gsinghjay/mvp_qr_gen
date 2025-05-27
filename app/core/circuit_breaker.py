"""
Circuit breaker implementation for service resilience.

This module provides circuit breaker functionality using the aiobreaker library
to protect against failures in new service implementations and ensure graceful
fallback to legacy implementations with proper asyncio support.
"""

import logging
from typing import Any
import datetime

import aiobreaker

from .config import settings
from .metrics_logger import MetricsLogger

logger = logging.getLogger(__name__)


class NewQRGenerationServiceListener(aiobreaker.CircuitBreakerListener):
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
    
    async def state_change(self, cb: aiobreaker.CircuitBreaker, old_state, new_state) -> None:
        """
        Handle circuit breaker state changes.
        
        Args:
            cb: The circuit breaker instance
            old_state: Previous state
            new_state: New state
        """
        # Debug what types are actually being passed
        logger.info(f"Circuit breaker {cb.name} state change - old_state type: {type(old_state)}, new_state type: {type(new_state)}")
        logger.info(f"Circuit breaker {cb.name} state change - old_state: {repr(old_state)}, new_state: {repr(new_state)}")
        
        # Handle different state object types
        if hasattr(old_state, 'name'):
            old_state_name = old_state.name
        elif isinstance(old_state, str):
            old_state_name = old_state.replace('-', '_')
        else:
            old_state_name = "unknown"
            
        if hasattr(new_state, 'name'):
            new_state_name = new_state.name
        elif isinstance(new_state, str):
            new_state_name = new_state.replace('-', '_')
        else:
            new_state_name = "unknown"
        
        logger.info(f"Circuit breaker {cb.name} state changed from {old_state_name} to {new_state_name}")
        
        # Update metrics with new state
        MetricsLogger.set_circuit_breaker_state(
            service=self.service_name,
            operation="qr_generation",
            state=new_state_name
        )
    
    async def failure(self, cb: aiobreaker.CircuitBreaker, exception: Exception) -> None:
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
    
    async def success(self, cb: aiobreaker.CircuitBreaker) -> None:
        """
        Handle circuit breaker successes.
        
        Args:
            cb: The circuit breaker instance
        """
        logger.debug(f"Circuit breaker {cb.name} recorded success")
        # Note: We don't need to log success metrics as they're implicit
        # in the absence of failures and the circuit being closed


def get_new_qr_generation_breaker() -> aiobreaker.CircuitBreaker:
    """
    Create and configure an async circuit breaker for NewQRGenerationService.
    
    This function creates a circuit breaker instance configured with values
    from application settings and attaches a listener for monitoring.
    
    Returns:
        Configured CircuitBreaker instance for NewQRGenerationService
    """
    # Create the circuit breaker with configuration from settings
    # Convert reset_timeout (seconds) to a timedelta for aiobreaker
    timeout_duration = datetime.timedelta(seconds=settings.QR_GENERATION_CB_RESET_TIMEOUT)
    
    breaker = aiobreaker.CircuitBreaker(
        fail_max=settings.QR_GENERATION_CB_FAIL_MAX,
        timeout_duration=timeout_duration,
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
    
    logger.info(f"Created async circuit breaker for NewQRGenerationService with fail_max={settings.QR_GENERATION_CB_FAIL_MAX}, timeout_duration={timeout_duration}")
    
    return breaker 