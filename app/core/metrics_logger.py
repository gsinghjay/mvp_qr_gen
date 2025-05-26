"""
Application-level metrics logger for custom Prometheus metrics.

This module provides custom business metrics complementing the existing HTTP metrics
from MetricsMiddleware. These metrics track QR code operations, service performance,
and feature flag status.
"""

import time
from functools import wraps
from typing import Callable, Optional

from prometheus_client import Counter, Gauge, Histogram

# ============================================================================
# Custom Prometheus Metrics for QR Application
# ============================================================================

# QR Code Creation Metrics
qr_creations_total = Counter(
    'qr_creations_total', 
    'Total QR codes created',
    ['qr_type', 'status']
)

# QR Redirect Processing Metrics  
qr_redirects_processed_total = Counter(
    'qr_redirects_processed_total',
    'Total QR redirects processed', 
    ['status']
)

# QR Image Generation Metrics
qr_image_generations_total = Counter(
    'qr_image_generations_total',
    'Total QR images generated',
    ['format', 'status']  
)

# QR Generation Path Comparison Metrics (Task 1.3)
qr_generation_path_total = Counter(
    'qr_generation_path_total',
    'Total QR generation operations by path',
    ['path', 'operation', 'status']
)

qr_generation_path_duration_seconds = Histogram(
    'qr_generation_path_duration_seconds',
    'Duration of QR generation operations by path',
    ['path', 'operation'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
)

# Service Call Duration Metrics
service_call_duration_seconds = Histogram(
    'service_call_duration_seconds',
    'Duration of internal service calls',
    ['service_name', 'operation_name'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# Feature Flag Status Metrics
feature_flag_active = Gauge(
    'feature_flag_active', 
    'Feature flag status (1=active, 0=inactive)',
    ['flag_name']
)

# Circuit Breaker Metrics
app_circuit_breaker_state_enum = Gauge(
    'app_circuit_breaker_state_enum',
    'Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)',
    ['service_name']
)

app_circuit_breaker_fallbacks_total = Counter(
    'app_circuit_breaker_fallbacks_total',
    'Total number of times the circuit breaker caused a fallback',
    ['service_name', 'operation_name']
)

app_circuit_breaker_failures_recorded_total = Counter(
    'app_circuit_breaker_failures_recorded_total',
    'Total number of failures recorded by the circuit breaker before opening or during half-open state',
    ['service_name']
)


class MetricsLogger:
    """
    Static utility class for logging application-level metrics.
    
    This class provides a clean interface for recording custom business metrics
    that complement the HTTP-level metrics from MetricsMiddleware.
    """
    
    @staticmethod
    def log_qr_created(qr_type: str, success: bool) -> None:
        """
        Log QR code creation event.
        
        Args:
            qr_type: Type of QR code ('static' or 'dynamic')
            success: Whether creation was successful
        """
        status = 'success' if success else 'failure'
        qr_creations_total.labels(qr_type=qr_type, status=status).inc()
    
    @staticmethod
    def log_redirect_processed(status: str) -> None:
        """
        Log QR redirect processing event.
        
        Args:
            status: Status of redirect ('success', 'not_found', 'invalid', 'error')
        """
        qr_redirects_processed_total.labels(status=status).inc()
    
    @staticmethod
    def log_image_generated(format: str, success: bool) -> None:
        """
        Log QR image generation event.
        
        Args:
            format: Image format ('png', 'svg', 'jpeg', 'webp')
            success: Whether generation was successful
        """
        status = 'success' if success else 'failure'
        qr_image_generations_total.labels(format=format, status=status).inc()
    
    @staticmethod
    def log_service_call(service_name: str, operation: str, duration: float) -> None:
        """
        Log internal service call performance.
        
        Args:
            service_name: Name of the service ('QRCodeService', 'QRCodeRepository', etc.)
            operation: Operation name ('create_static_qr', 'get_by_id', etc.)
            duration: Duration in seconds
        """
        service_call_duration_seconds.labels(
            service_name=service_name, 
            operation_name=operation
        ).observe(duration)
    
    @staticmethod
    def set_feature_flag(flag_name: str, active: bool) -> None:
        """
        Set feature flag status.
        
        Args:
            flag_name: Name of the feature flag
            active: Whether the flag is active
        """
        value = 1.0 if active else 0.0
        feature_flag_active.labels(flag_name=flag_name).set(value)
    
    @staticmethod
    def set_circuit_breaker_state(service_name: str, state_name: str) -> None:
        """
        Set circuit breaker state.
        
        Args:
            service_name: Name of the service
            state_name: State name ("closed", "open", "half_open")
        """
        # Map state names to enum values
        state_mapping = {
            "closed": 0,
            "open": 1,
            "half_open": 2
        }
        
        state_value = state_mapping.get(state_name.lower(), 0)
        app_circuit_breaker_state_enum.labels(service_name=service_name).set(state_value)
    
    @staticmethod
    def log_circuit_breaker_fallback(service_name: str, operation_name: str) -> None:
        """
        Log circuit breaker fallback event.
        
        Args:
            service_name: Name of the service
            operation_name: Name of the operation that triggered fallback
        """
        app_circuit_breaker_fallbacks_total.labels(
            service_name=service_name,
            operation_name=operation_name
        ).inc()
    
    @staticmethod
    def log_circuit_breaker_failure(service_name: str) -> None:
        """
        Log circuit breaker failure event.
        
        Args:
            service_name: Name of the service that failed
        """
        app_circuit_breaker_failures_recorded_total.labels(service_name=service_name).inc()
    
    @staticmethod
    def log_qr_generation_path(path: str, operation: str, duration: float, success: bool) -> None:
        """
        Log QR generation path metrics for comparing old vs new implementations.
        
        Args:
            path: Path taken ("old" or "new")
            operation: Operation performed ("create_static", "create_dynamic", "generate_image")
            duration: Duration in seconds
            success: Whether the operation was successful
        """
        status = 'success' if success else 'failure'
        qr_generation_path_total.labels(path=path, operation=operation, status=status).inc()
        qr_generation_path_duration_seconds.labels(path=path, operation=operation).observe(duration)
    
    @staticmethod
    def time_service_call(service_name: str, operation: str) -> Callable:
        """
        Decorator to automatically time and log service calls.
        
        Args:
            service_name: Name of the service
            operation: Operation name
            
        Returns:
            Decorator function
            
        Example:
            @MetricsLogger.time_service_call("QRCodeService", "create_static_qr")
            def create_static_qr(self, data):
                # Implementation here
                pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    duration = time.perf_counter() - start_time
                    MetricsLogger.log_service_call(service_name, operation, duration)
                    return result
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    MetricsLogger.log_service_call(service_name, operation, duration)
                    raise
            return wrapper
        return decorator


# ============================================================================
# Utility Functions
# ============================================================================

def initialize_feature_flags() -> None:
    """
    Initialize feature flags based on current settings.
    
    This function reads from app.core.config.settings and reports
    the actual status to Prometheus. Should be called during application startup.
    """
    from .config import settings as app_settings
    
    # Observatory-First feature flags (Phase 0)
    MetricsLogger.set_feature_flag(
        'new_qr_service_enabled', 
        app_settings.USE_NEW_QR_GENERATION_SERVICE
    )
    MetricsLogger.set_feature_flag(
        'new_analytics_service_enabled',
        app_settings.USE_NEW_ANALYTICS_SERVICE
    )
    MetricsLogger.set_feature_flag(
        'new_validation_service_enabled',
        app_settings.USE_NEW_VALIDATION_SERVICE
    )
    
    # Legacy feature flags (for backward compatibility)
    MetricsLogger.set_feature_flag(
        'enhanced_validation_enabled',
        app_settings.FEATURE_ENHANCED_VALIDATION_ENABLED
    )
    MetricsLogger.set_feature_flag(
        'performance_optimization_enabled',
        app_settings.FEATURE_PERFORMANCE_OPTIMIZATION_ENABLED
    )
    MetricsLogger.set_feature_flag(
        'debug_mode_enabled',
        app_settings.FEATURE_DEBUG_MODE_ENABLED or app_settings.DEBUG
    ) 