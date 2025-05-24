#!/bin/bash

# Test script for Observatory-First Refactoring Alerts
# This script helps verify that alerts are properly configured and can fire

set -e

echo "🔬 Observatory-First Refactoring Alert Testing Script"
echo "=================================================="

# Configuration
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"
API_URL="https://localhost"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if service is running
check_service() {
    local service_name=$1
    local url=$2
    
    echo -n "Checking ${service_name}... "
    if curl -s -f -k "${url}" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not accessible${NC}"
        return 1
    fi
}

# Function to check Prometheus rules
check_prometheus_rules() {
    echo -e "\n${BLUE}📊 Checking Prometheus Alert Rules${NC}"
    echo "=================================="
    
    # Check if Prometheus is loading rules
    local rules_response=$(curl -s "${PROMETHEUS_URL}/api/v1/rules" 2>/dev/null || echo "")
    
    if [[ -n "$rules_response" ]]; then
        echo -e "${GREEN}✓ Prometheus rules API accessible${NC}"
        
        # Check for our specific rule groups
        if echo "$rules_response" | grep -q "qr_system_critical_alerts"; then
            echo -e "${GREEN}✓ Critical alerts rule group loaded${NC}"
        else
            echo -e "${YELLOW}⚠ Critical alerts rule group not found${NC}"
        fi
        
        if echo "$rules_response" | grep -q "qr_system_refactoring_alerts"; then
            echo -e "${GREEN}✓ Refactoring alerts rule group loaded${NC}"
        else
            echo -e "${YELLOW}⚠ Refactoring alerts rule group not found${NC}"
        fi
    else
        echo -e "${RED}✗ Cannot access Prometheus rules API${NC}"
    fi
}

# Function to check current alerts
check_current_alerts() {
    echo -e "\n${BLUE}🚨 Checking Current Alert Status${NC}"
    echo "================================"
    
    local alerts_response=$(curl -s "${PROMETHEUS_URL}/api/v1/alerts" 2>/dev/null || echo "")
    
    if [[ -n "$alerts_response" ]]; then
        echo -e "${GREEN}✓ Prometheus alerts API accessible${NC}"
        
        # Count active alerts
        local active_alerts=$(echo "$alerts_response" | grep -o '"state":"firing"' | wc -l)
        local pending_alerts=$(echo "$alerts_response" | grep -o '"state":"pending"' | wc -l)
        
        echo "Active alerts: ${active_alerts}"
        echo "Pending alerts: ${pending_alerts}"
        
        if [[ $active_alerts -gt 0 ]]; then
            echo -e "${RED}⚠ There are currently firing alerts!${NC}"
        else
            echo -e "${GREEN}✓ No alerts currently firing${NC}"
        fi
    else
        echo -e "${RED}✗ Cannot access Prometheus alerts API${NC}"
    fi
}

# Function to test alert by creating temporary load
test_alert_with_load() {
    echo -e "\n${BLUE}🔄 Testing Alert Response (Optional Load Test)${NC}"
    echo "=============================================="
    
    read -p "Do you want to run a brief load test to potentially trigger performance alerts? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Running brief load test..."
        
        # Simple load test - make multiple concurrent requests
        for i in {1..10}; do
            curl -s -k "${API_URL}/health" > /dev/null &
            curl -s -k "${API_URL}/api/v1/qr" > /dev/null &
        done
        
        wait
        echo -e "${GREEN}✓ Load test completed${NC}"
        echo "Check Prometheus/Grafana in a few minutes to see if any performance alerts triggered."
    else
        echo "Skipping load test."
    fi
}

# Function to check Grafana alerting
check_grafana_alerting() {
    echo -e "\n${BLUE}📈 Checking Grafana Alert Configuration${NC}"
    echo "======================================"
    
    # Check if Grafana is accessible
    if curl -s -f "${GRAFANA_URL}/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Grafana is accessible${NC}"
        
        # Note: Grafana API calls would require authentication
        echo "To check Grafana alerts manually:"
        echo "1. Open ${GRAFANA_URL}"
        echo "2. Go to Alerting > Alert Rules"
        echo "3. Verify that QR System alert rules are loaded"
        echo "4. Check Notification Channels in Alerting > Notification Channels"
    else
        echo -e "${RED}✗ Grafana not accessible${NC}"
    fi
}

# Function to show next steps
show_next_steps() {
    echo -e "\n${BLUE}📋 Next Steps for Observatory-First Monitoring${NC}"
    echo "=============================================="
    echo "1. Monitor baseline metrics for 1 week before refactoring"
    echo "2. Adjust alert thresholds based on observed normal patterns"
    echo "3. Set up actual notification channels (email, Slack, etc.)"
    echo "4. Test alert firing by temporarily adjusting thresholds"
    echo "5. Document baseline performance metrics for comparison"
    echo ""
    echo "Key URLs:"
    echo "- Prometheus: ${PROMETHEUS_URL}"
    echo "- Grafana: ${GRAFANA_URL}"
    echo "- API Health: ${API_URL}/health"
}

# Main execution
main() {
    echo -e "${YELLOW}Starting Observatory-First Alert System Verification...${NC}"
    echo ""
    
    # Check all services
    echo -e "${BLUE}🔍 Service Health Check${NC}"
    echo "====================="
    check_service "Prometheus" "${PROMETHEUS_URL}/-/healthy"
    check_service "Grafana" "${GRAFANA_URL}/api/health"
    check_service "QR API" "${API_URL}/health"
    
    # Check Prometheus configuration
    check_prometheus_rules
    check_current_alerts
    
    # Check Grafana
    check_grafana_alerting
    
    # Optional load test
    test_alert_with_load
    
    # Show next steps
    show_next_steps
    
    echo -e "\n${GREEN}🎯 Observatory-First Alert Testing Complete!${NC}"
    echo "The monitoring infrastructure is ready for the refactoring process."
}

# Run main function
main "$@" 