"""
Diagnostic script to test the circuit breaker directly.
"""
import logging
import time
import asyncio

import aiobreaker
from app.core.circuit_breaker import get_new_qr_generation_breaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_circuit_breaker():
    """Test the circuit breaker functionality directly."""
    print("Testing circuit breaker functionality")
    
    # Get the circuit breaker instance
    breaker = get_new_qr_generation_breaker()
    print(f"Circuit breaker created with fail_max={breaker.fail_max}, timeout_duration={breaker.timeout_duration}")
    print(f"Initial state: {breaker.current_state}")
    
    # Try a few operations that will fail
    for i in range(5):
        try:
            print(f"Attempt {i+1}: Executing operation that will fail")
            
            # Use the circuit breaker to execute a function that will fail
            @breaker
            async def failing_operation():
                raise RuntimeError(f"Simulated failure {i+1}")
            
            await failing_operation()
            
        except RuntimeError as e:
            print(f"  Expected failure: {e}")
        except aiobreaker.CircuitBreakerError as e:
            print(f"  Circuit breaker error: {e}")
        
        # Check and print the current state
        print(f"  Current state: {breaker.current_state}")
        
        # Short delay
        await asyncio.sleep(0.5)
    
    print("\nTest completed. Check metrics to verify state changes were recorded.")

if __name__ == "__main__":
    asyncio.run(test_circuit_breaker()) 