"""
Circuit breaker implementation for resilient service calls.

This module provides circuit breaker patterns for protecting against cascading failures
when calling new service implementations during the Observatory-First refactoring.
"""

import logging
from typing import Optional

import pybreaker

from .config import settings
from .metrics_logger import MetricsLogger

logger = logging.getLogger(__name__)


class NewQRGenerationServiceListener(pybreaker.CircuitBreakerListener):
    """
    Circuit breaker listener for the NewQRGenerationService.
    
    This listener logs state changes and failures, and reports metrics
    to Prometheus for monitoring circuit breaker behavior.
    """
    
    def state_change(self, cb: pybreaker.CircuitBreaker, old_state: pybreaker.CircuitBreakerState, new_state: pybreaker.CircuitBreakerState) -> None:
        """
        Called when the circuit breaker changes state.
        
        Args:
            cb: The circuit breaker instance
            old_state: Previous state
            new_state: New state
        """
        state_name = new_state.name.lower()
        logger.info(f"Circuit breaker for NewQRGenerationService changed state: {old_state.name} -> {new_state.name}")
        MetricsLogger.set_circuit_breaker_state("NewQRGenerationService", state_name)
    
    def failure(self, cb: pybreaker.CircuitBreaker, exc: Exception) -> None:
        """
        Called when a failure is recorded by the circuit breaker.
        
        Args:
            cb: The circuit breaker instance
            exc: The exception that caused the failure
        """
        logger.warning(f"Circuit breaker for NewQRGenerationService recorded failure: {exc}")
        MetricsLogger.log_circuit_breaker_failure("NewQRGenerationService")
    
    def success(self, cb: pybreaker.CircuitBreaker) -> None:
        """
        Called when a successful call is recorded by the circuit breaker.
        
        Args:
            cb: The circuit breaker instance
        """
        logger.debug("Circuit breaker for NewQRGenerationService recorded success")


# Module-level circuit breaker instance (singleton pattern)
_new_qr_generation_breaker: Optional[pybreaker.CircuitBreaker] = None


def get_new_qr_generation_breaker() -> pybreaker.CircuitBreaker:
    """
    Get or create the circuit breaker instance for NewQRGenerationService.
    
    This function implements a singleton pattern to ensure consistent
    circuit breaker state across the application.
    
    Returns:
        pybreaker.CircuitBreaker: Configured circuit breaker instance
    """
    global _new_qr_generation_breaker
    
    if _new_qr_generation_breaker is None:
        # Create the circuit breaker with configuration from settings
        _new_qr_generation_breaker = pybreaker.CircuitBreaker(
            fail_max=settings.QR_GENERATION_CB_FAIL_MAX,
            reset_timeout=settings.QR_GENERATION_CB_RESET_TIMEOUT,
            exclude=[KeyboardInterrupt, SystemExit],  # Never treat these as service failures
            name="NewQRGenerationService"
        )
        
        # Add the listener for logging and metrics
        listener = NewQRGenerationServiceListener()
        _new_qr_generation_breaker.add_listener(listener)
        
        # Initialize the circuit breaker state metric
        MetricsLogger.set_circuit_breaker_state("NewQRGenerationService", "closed")
        
        logger.info(f"Initialized circuit breaker for NewQRGenerationService with fail_max={settings.QR_GENERATION_CB_FAIL_MAX}, reset_timeout={settings.QR_GENERATION_CB_RESET_TIMEOUT}")
    
    return _new_qr_generation_breaker 