"""
Diagnostic script to test the circuit breaker directly.
"""
import logging
import time

import pybreaker
from app.core.circuit_breaker import get_new_qr_generation_breaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_circuit_breaker():
    """Test the circuit breaker functionality directly."""
    print("Testing circuit breaker functionality")
    
    # Get the circuit breaker instance
    breaker = get_new_qr_generation_breaker()
    print(f"Circuit breaker created with fail_max={breaker.fail_max}, reset_timeout={breaker.reset_timeout}")
    print(f"Initial state: {breaker.current_state}")
    
    # Try a few operations that will fail
    for i in range(5):
        try:
            print(f"Attempt {i+1}: Executing operation that will fail")
            
            # Use the circuit breaker to execute a function that will fail
            @breaker
            def failing_operation():
                raise RuntimeError(f"Simulated failure {i+1}")
            
            failing_operation()
            
        except RuntimeError as e:
            print(f"  Expected failure: {e}")
        except pybreaker.CircuitBreakerError as e:
            print(f"  Circuit breaker error: {e}")
        
        # Check and print the current state
        print(f"  Current state: {breaker.current_state}")
        
        # Short delay
        time.sleep(0.5)
    
    print("\nTest completed. Check metrics to verify state changes were recorded.")

if __name__ == "__main__":
    test_circuit_breaker() 