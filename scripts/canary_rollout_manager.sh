#!/bin/bash
# Canary Rollout Manager for NewQRGenerationService
# This script helps manage the incremental rollout of the new QR generation service
# by gradually increasing the canary percentage and monitoring system health.

set -e

# Configuration
ENV_FILE=".env"
LOG_FILE="canary_rollout.log"
STEP_DURATION_HOURS=24
CHECK_INTERVAL_MINUTES=60
MAX_ERROR_THRESHOLD=2
ROLLOUT_STEPS=(5 20 50 100)
CURRENT_STEP=0
MAX_RETRY_COUNT=3

# Helper functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

update_env_var() {
    local var_name="$1"
    local var_value="$2"
    log "Setting $var_name=$var_value in $ENV_FILE"
    
    # Check if variable exists in file
    if grep -q "^$var_name=" "$ENV_FILE"; then
        # Update existing variable
        sed -i "s/^$var_name=.*/$var_name=$var_value/" "$ENV_FILE"
    else
        # Add new variable
        echo "$var_name=$var_value" >> "$ENV_FILE"
    fi
}

restart_service() {
    log "Restarting API service to apply changes"
    docker-compose restart api
    sleep 10  # Wait for service to restart
}

check_health() {
    log "Checking system health"
    local health_status=$(curl -k -s -u admin_user:strongpassword https://10.1.6.12/health | jq -r '.status')
    local qr_service_status=$(curl -k -s -u admin_user:strongpassword https://10.1.6.12/health | jq -r '.checks.new_qr_generation.status')
    
    if [[ "$health_status" == "healthy" && "$qr_service_status" == "pass" ]]; then
        log "System health check: PASS"
        return 0
    else
        log "System health check: FAIL - Health: $health_status, QR Service: $qr_service_status"
        return 1
    fi
}

check_circuit_breaker() {
    log "Checking circuit breaker state"
    local cb_state=$(curl -k -s -u admin_user:strongpassword https://10.1.6.12/metrics | grep app_circuit_breaker_state_enum | grep NewQRGenerationService | awk '{print $2}')
    
    if [[ "$cb_state" == "0.0" ]]; then
        log "Circuit breaker check: PASS (CLOSED)"
        return 0
    else
        log "Circuit breaker check: FAIL - State: $cb_state (OPEN or HALF_OPEN)"
        return 1
    fi
}

count_recent_errors() {
    log "Checking for recent errors"
    local error_count=$(docker-compose logs --tail=100 api | grep -i error | grep -i "NewQRGenerationService" | wc -l)
    log "Found $error_count recent errors"
    return "$error_count"
}

run_smoke_test() {
    log "Running smoke test"
    local result=$(cd /home/webhost/qr-app && scripts/enhanced_smoke_test.sh | grep -i fail | wc -l)
    
    if [[ "$result" -eq 0 ]]; then
        log "Smoke test: PASS"
        return 0
    else
        log "Smoke test: FAIL - $result failures detected"
        return 1
    fi
}

get_current_percentage() {
    local current_percentage=$(grep "^CANARY_PERCENTAGE=" "$ENV_FILE" | cut -d= -f2)
    echo "$current_percentage"
}

main() {
    log "Starting canary rollout manager"
    log "Rollout steps: ${ROLLOUT_STEPS[*]}"
    
    # Find current step
    local current_percentage=$(get_current_percentage)
    for i in "${!ROLLOUT_STEPS[@]}"; do
        if [[ "${ROLLOUT_STEPS[$i]}" -eq "$current_percentage" ]]; then
            CURRENT_STEP=$i
            break
        fi
    done
    
    log "Current canary percentage: $current_percentage% (step $CURRENT_STEP of ${#ROLLOUT_STEPS[@]})"
    
    # Start monitoring and rollout process
    while [[ $CURRENT_STEP -lt ${#ROLLOUT_STEPS[@]} ]]; do
        local target_percentage=${ROLLOUT_STEPS[$CURRENT_STEP]}
        local current_percentage=$(get_current_percentage)
        
        # If we need to change the percentage
        if [[ "$current_percentage" -ne "$target_percentage" ]]; then
            log "Updating canary percentage to $target_percentage%"
            update_env_var "CANARY_PERCENTAGE" "$target_percentage"
            restart_service
        fi
        
        # Monitor for the specified duration
        local checks_count=$(( STEP_DURATION_HOURS * 60 / CHECK_INTERVAL_MINUTES ))
        local retry_count=0
        local failed_checks=0
        
        log "Monitoring step $CURRENT_STEP ($target_percentage%) for $STEP_DURATION_HOURS hours ($checks_count checks)"
        
        for (( i=1; i<=checks_count; i++ )); do
            log "Running check $i of $checks_count"
            
            if ! check_health; then
                failed_checks=$((failed_checks + 1))
            fi
            
            if ! check_circuit_breaker; then
                failed_checks=$((failed_checks + 1))
            fi
            
            count_recent_errors
            local error_count=$?
            if [[ $error_count -gt $MAX_ERROR_THRESHOLD ]]; then
                failed_checks=$((failed_checks + 1))
                log "Too many errors detected: $error_count (threshold: $MAX_ERROR_THRESHOLD)"
            fi
            
            if ! run_smoke_test; then
                failed_checks=$((failed_checks + 1))
            fi
            
            # If too many failures, roll back
            if [[ $failed_checks -ge 3 ]]; then
                log "ALERT: Too many failures detected ($failed_checks). Rolling back."
                
                if [[ $CURRENT_STEP -gt 0 ]]; then
                    # Roll back to previous step
                    CURRENT_STEP=$((CURRENT_STEP - 1))
                    local rollback_percentage=${ROLLOUT_STEPS[$CURRENT_STEP]}
                    log "Rolling back to $rollback_percentage%"
                    update_env_var "CANARY_PERCENTAGE" "$rollback_percentage"
                    restart_service
                    
                    # Increase retry count
                    retry_count=$((retry_count + 1))
                    if [[ $retry_count -ge $MAX_RETRY_COUNT ]]; then
                        log "ERROR: Maximum retry count reached. Stopping rollout process."
                        exit 1
                    fi
                    
                    # Reset for next monitoring cycle
                    failed_checks=0
                    i=0
                    log "Retrying step $CURRENT_STEP ($rollback_percentage%) - Attempt $retry_count of $MAX_RETRY_COUNT"
                else
                    # Already at first step, disable canary
                    log "ERROR: Failures at minimum canary percentage. Disabling canary testing."
                    update_env_var "CANARY_TESTING_ENABLED" "false"
                    restart_service
                    exit 1
                fi
            fi
            
            # Wait for next check interval
            if [[ $i -lt $checks_count ]]; then
                log "Waiting $CHECK_INTERVAL_MINUTES minutes until next check..."
                sleep $(( CHECK_INTERVAL_MINUTES * 60 ))
            fi
        done
        
        log "Successfully completed monitoring period for step $CURRENT_STEP ($target_percentage%)"
        
        # Move to next step
        CURRENT_STEP=$((CURRENT_STEP + 1))
        if [[ $CURRENT_STEP -lt ${#ROLLOUT_STEPS[@]} ]]; then
            log "Moving to next step: $CURRENT_STEP (${ROLLOUT_STEPS[$CURRENT_STEP]}%)"
        else
            log "Canary rollout complete! Service is now at 100%"
        fi
    done
    
    log "Canary rollout process completed successfully"
}

# Run the main function
main "$@" 