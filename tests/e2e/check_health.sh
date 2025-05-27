#!/bin/bash
# Simple health check script for E2E tests

API_URL="${E2E_API_BASE_URL:-http://localhost:80}/health"
echo "Checking health at: $API_URL"

# Get auth credentials from environment variables
AUTH_USER="${AUTH_USER}"
AUTH_PASS="${AUTH_PASS}"

# Check if credentials are set
if [[ -z "$AUTH_USER" || -z "$AUTH_PASS" ]]; then
  echo "ERROR: Authentication credentials not found in environment variables."
  echo "Please ensure AUTH_USER and AUTH_PASS are set in .env file."
  exit 1
fi

# Use curl to check the status code
# Added -k for self-signed certificates and -u for basic auth
STATUS_CODE=$(curl -k -s -u "${AUTH_USER}:${AUTH_PASS}" -o /dev/null -w "%{http_code}" "$API_URL")

if [ "$STATUS_CODE" -eq 200 ]; then
  echo "Health check PASSED (Status: $STATUS_CODE)"
  exit 0
else
  echo "Health check FAILED (Status: $STATUS_CODE)"
  exit 1
fi 