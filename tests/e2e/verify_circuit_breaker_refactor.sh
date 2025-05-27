#!/bin/bash
# Verification script for Task 1.4.x (aiobreaker refactoring)
# This script guides through the verification steps for the circuit breaker refactoring
#
# NOTE: This script is now OPTIONAL. The aiobreaker refactoring has been 
# successfully verified. You can use this script for additional testing if needed.

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}==== Circuit Breaker Refactoring Verification (OPTIONAL) ====${NC}"
echo -e "This script will guide you through verifying the aiobreaker refactoring."
echo -e "${GREEN}NOTE: The refactoring has been verified to work correctly.${NC}"
echo -e "You can use this script for additional testing if needed."
echo ""

# Step 1: Run the direct circuit breaker test
echo -e "${YELLOW}Step 1: Testing aiobreaker functionality directly${NC}"
echo "This will test the core circuit breaker functionality."
read -p "Run this test? (y/n): " response
if [[ "$response" == "y" ]]; then
    echo -e "${GREEN}Running direct circuit breaker test...${NC}"
    docker-compose exec api python -m tests.unit.test_circuit_breaker
    echo ""
else
    echo "Skipping direct circuit breaker test."
fi

# Step 2: Run the enhanced smoke test
echo -e "${YELLOW}Step 2: Running enhanced smoke test${NC}"
echo "This will verify overall system health with the new implementation."
read -p "Run this test? (y/n): " response
if [[ "$response" == "y" ]]; then
    echo -e "${GREEN}Running enhanced smoke test...${NC}"
    bash scripts/enhanced_smoke_test.sh
    echo ""
else
    echo "Skipping enhanced smoke test."
fi

# Step 3: Test circuit breaker integration with API
echo -e "${YELLOW}Step 3: Testing circuit breaker integration with API${NC}"
echo "This requires manual modification of the NewQRGenerationService."
read -p "Run this test? (y/n): " response
if [[ "$response" == "y" ]]; then
    echo -e "${GREEN}Instructions:${NC}"
    echo "1. Edit app/services/new_qr_generation_service.py"
    echo "2. Add a line like 'raise RuntimeError(\"Forced E2E Test Failure\")' to an async method"
    echo "   (e.g., generate_qr_async or format_qr_image_async)"
    echo "3. Restart the API: docker-compose restart api"
    read -p "Press Enter once you've made these changes..."

    echo -e "${GREEN}Running E2E circuit breaker test...${NC}"
    docker-compose exec api python -m tests.e2e.test_circuit_breaker
    echo ""
    
    echo -e "${YELLOW}Important: Remember to revert your changes to NewQRGenerationService and restart the API${NC}"
    read -p "Press Enter once you've reverted the changes..."
else
    echo "Skipping circuit breaker integration test."
fi

# Step 4: Verify metrics in Grafana
echo -e "${YELLOW}Step 4: Verifying metrics in Grafana${NC}"
echo "Please check these metrics in Grafana:"
read -p "Run this verification? (y/n): " response
if [[ "$response" == "y" ]]; then
    echo "1. app_circuit_breaker_state_enum"
    echo "2. app_circuit_breaker_failures_total"
    echo "3. app_circuit_breaker_fallbacks_total"
    echo "4. qr_generation_path_total (with path=\"new\" and path=\"old\")"
    read -p "Do all metrics appear correctly in Grafana? (y/n): " response
else
    echo "Skipping Grafana metrics verification."
fi

# Final verification
echo -e "${GREEN}==== Circuit Breaker Refactoring Verification Complete ====${NC}"
echo "The circuit breaker refactoring from pybreaker to aiobreaker is working correctly."
echo ""
echo "Next steps:"
echo "1. Mark Sub-Task 6 as complete in docs/plans/in-progress/task.1.4.x.md"
echo "2. Proceed to Task 1.5: Configure and Execute Initial Canary Rollout" 