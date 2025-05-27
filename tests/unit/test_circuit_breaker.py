"""
Diagnostic script to test the aiobreaker circuit breaker directly.
This script was updated as part of Task 1.4.x to work with aiobreaker instead of pybreaker.
"""
import logging
import time
import asyncio

import aiobreaker
from app.core.circuit_breaker import get_new_qr_generation_breaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the state name from the state object/string
def get_state_name(state):
    """Get a readable state name from the state object or string."""
    if hasattr(state, 'name'):
        return state.name.upper()
    elif isinstance(state, str):
        return state.replace('-', '_').upper()
    else:
        return f"UNKNOWN ({repr(state)})"

async def test_circuit_breaker():
    """Test the circuit breaker functionality directly using aiobreaker."""
    print("Testing aiobreaker circuit breaker functionality")
    
    # Get the circuit breaker instance
    breaker = get_new_qr_generation_breaker()
    print(f"Circuit breaker created with fail_max={breaker.fail_max}, timeout_duration={breaker.timeout_duration}")
    print(f"Initial state: {get_state_name(breaker.current_state)}")
    
    # Try operations that will fail until the circuit opens
    for i in range(breaker.fail_max + 2):  # +2 to ensure we see the open state
        try:
            print(f"\nAttempt {i+1}: Executing operation that will fail")
            
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
        print(f"  Current state: {get_state_name(breaker.current_state)}")
        
        # Short delay
        await asyncio.sleep(0.5)
    
    # If the circuit is open (check by state name)
    current_state = get_state_name(breaker.current_state)
    if "OPEN" in current_state:
        print(f"\nCircuit is {current_state}. Waiting {breaker.timeout_duration.total_seconds()} seconds for it to transition to HALF-OPEN...")
        await asyncio.sleep(breaker.timeout_duration.total_seconds() + 0.5)
        print(f"After timeout, current state: {get_state_name(breaker.current_state)}")
        
        # Now in half-open state, try a successful operation to close the circuit
        try:
            print("\nAttempting successful operation in HALF-OPEN state...")
            
            @breaker
            async def successful_operation():
                return "Success!"
            
            result = await successful_operation()
            print(f"  Operation succeeded with result: {result}")
            print(f"  Current state: {get_state_name(breaker.current_state)}")
            
        except Exception as e:
            print(f"  Unexpected error: {e}")
    
    print("\nTest completed. Key observations:")
    print(f"- Circuit breaker transitions: CLOSED -> OPEN after {breaker.fail_max} failures")
    print(f"- In OPEN state, calls fail fast with CircuitBreakerError (no actual call)")
    print(f"- After {breaker.timeout_duration.total_seconds()}s, transitions to HALF-OPEN for trial")
    print(f"- In HALF_OPEN, first success transitions to CLOSED")
    print("\nCheck metrics to verify state changes were recorded.")

if __name__ == "__main__":
    print("Running aiobreaker circuit breaker test...")
    asyncio.run(test_circuit_breaker()) 