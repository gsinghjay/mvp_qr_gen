#!/bin/bash

# Ensure the script fails if any command fails
set -e

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# PostgreSQL database connection variables
DB_CONTAINER="qr_generator_postgres"
DB_NAME=${DB_NAME:-"qrdb"}
DB_USER=${DB_USER:-"pguser"}
DB_PASSWORD=${DB_PASSWORD:-"pgpassword"}
DB_HOST="localhost"

# Create the output directory if it doesn't exist
REPORT_DIR="database_reports"
mkdir -p $REPORT_DIR

# Generate a timestamp for the report
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="${REPORT_DIR}/db_schema_report_${TIMESTAMP}.txt"

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}${BOLD}=== $1 ===${NC}" | tee -a $REPORT_FILE
}

# Function to run PostgreSQL command in docker container
run_psql_cmd() {
    local container=$1
    local command=$2
    docker exec $container psql -U $DB_USER -d $DB_NAME -c "$command" | tee -a $REPORT_FILE
}

# Function to run PostgreSQL query command in docker container and format as a table
run_psql_query() {
    local container=$1
    local query=$2
    docker exec $container psql -U $DB_USER -d $DB_NAME -c "\\pset format aligned" -c "$query" | tee -a $REPORT_FILE
}

# Start generating the report
echo "Generating PostgreSQL database schema report for QR Code Generator..." | tee $REPORT_FILE
echo "Date: $(date)" | tee -a $REPORT_FILE
echo "Database: $DB_NAME" | tee -a $REPORT_FILE
echo "=======================================================" | tee -a $REPORT_FILE

# Check if container is running
print_section "CHECKING CONTAINER STATUS"
if docker ps | grep -q $DB_CONTAINER; then
    echo -e "${GREEN}✓ Production database container ($DB_CONTAINER) is running${NC}" | tee -a $REPORT_FILE
else
    echo -e "${RED}✗ Production database container ($DB_CONTAINER) is not running${NC}" | tee -a $REPORT_FILE
    exit 1
fi

# Database version
print_section "DATABASE VERSION"
run_psql_cmd $DB_CONTAINER "SELECT version();"

# List all tables
print_section "TABLES"
run_psql_cmd $DB_CONTAINER "\\dt;"

# Get detailed information for each table
print_section "TABLE DETAILS"

# Get list of tables
TABLES=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")

# Loop through tables and get details
for TABLE in $TABLES; do
    # Remove spaces
    TABLE=$(echo $TABLE | tr -d ' ')
    print_section "TABLE: $TABLE"
    
    # Table structure
    echo -e "${YELLOW}Table Structure:${NC}" | tee -a $REPORT_FILE
    run_psql_cmd $DB_CONTAINER "\\d+ $TABLE;"
    
    # Count rows
    echo -e "${YELLOW}Row Count:${NC}" | tee -a $REPORT_FILE
    run_psql_cmd $DB_CONTAINER "SELECT COUNT(*) FROM $TABLE;"
    
    # Sample data (first 5 rows)
    echo -e "${YELLOW}Sample Data (first 5 rows):${NC}" | tee -a $REPORT_FILE
    run_psql_query $DB_CONTAINER "SELECT * FROM $TABLE LIMIT 5;"
done

# Get database indices
print_section "INDICES"
run_psql_cmd $DB_CONTAINER "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;"

# Get database size
print_section "DATABASE SIZE"
run_psql_cmd $DB_CONTAINER "SELECT pg_size_pretty(pg_database_size('$DB_NAME')) AS db_size;"

# Get table sizes
print_section "TABLE SIZES"
run_psql_cmd $DB_CONTAINER "SELECT table_name, pg_size_pretty(pg_total_relation_size(table_name::text)) AS total_size FROM information_schema.tables WHERE table_schema = 'public' ORDER BY pg_total_relation_size(table_name::text) DESC;"

# Get Alembic migration history
print_section "ALEMBIC MIGRATION HISTORY"
if docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "\\dt alembic_version" 2>/dev/null | grep -q "alembic_version"; then
    run_psql_cmd $DB_CONTAINER "SELECT * FROM alembic_version;"
else
    echo "No alembic_version table found." | tee -a $REPORT_FILE
fi

# Information specific to QR scan logs
print_section "QR SCAN STATISTICS"
run_psql_cmd $DB_CONTAINER "SELECT COUNT(*) AS total_scans FROM scan_logs;"
run_psql_cmd $DB_CONTAINER "SELECT COUNT(*) AS total_genuine_scans FROM scan_logs WHERE is_genuine_scan = true;"

# Device statistics
print_section "DEVICE STATISTICS"
run_psql_query $DB_CONTAINER "SELECT device_family, COUNT(*) as count FROM scan_logs GROUP BY device_family ORDER BY count DESC LIMIT 10;"

# Browser statistics
print_section "BROWSER STATISTICS"
run_psql_query $DB_CONTAINER "SELECT browser_family, COUNT(*) as count FROM scan_logs GROUP BY browser_family ORDER BY count DESC LIMIT 10;"

# OS statistics
print_section "OS STATISTICS"
run_psql_query $DB_CONTAINER "SELECT os_family, COUNT(*) as count FROM scan_logs GROUP BY os_family ORDER BY count DESC LIMIT 10;"

# QR code statistics
print_section "QR CODE STATISTICS"
run_psql_cmd $DB_CONTAINER "SELECT qr_type, COUNT(*) FROM qr_codes GROUP BY qr_type;"
run_psql_cmd $DB_CONTAINER "SELECT AVG(scan_count) as avg_scans, MAX(scan_count) as max_scans FROM qr_codes;"
run_psql_cmd $DB_CONTAINER "SELECT AVG(genuine_scan_count) as avg_genuine_scans, MAX(genuine_scan_count) as max_genuine_scans FROM qr_codes;"

# Scans by day for last 7 days
print_section "SCANS BY DAY (LAST 7 DAYS)"
run_psql_query $DB_CONTAINER "SELECT DATE(scanned_at) as day, COUNT(*) as total_scans, SUM(CASE WHEN is_genuine_scan THEN 1 ELSE 0 END) as genuine_scans FROM scan_logs WHERE scanned_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY day ORDER BY day DESC;"

# Time series analysis for analytics dashboard
print_section "TIME SERIES DATA FOR ANALYTICS DASHBOARD"
# Hourly scan patterns (for last 24 hours)
echo -e "${YELLOW}Hourly Scan Patterns (Last 24 Hours):${NC}" | tee -a $REPORT_FILE
run_psql_query $DB_CONTAINER "SELECT 
  EXTRACT(HOUR FROM scanned_at) as hour, 
  COUNT(*) as total_scans, 
  SUM(CASE WHEN is_genuine_scan THEN 1 ELSE 0 END) as genuine_scans 
FROM scan_logs 
WHERE scanned_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' 
GROUP BY hour 
ORDER BY hour;"

# Weekly scan patterns (for last month)
echo -e "${YELLOW}Weekly Scan Patterns (Last Month):${NC}" | tee -a $REPORT_FILE
run_psql_query $DB_CONTAINER "SELECT 
  TO_CHAR(DATE_TRUNC('week', scanned_at), 'YYYY-MM-DD') as week_start,
  COUNT(*) as total_scans, 
  SUM(CASE WHEN is_genuine_scan THEN 1 ELSE 0 END) as genuine_scans 
FROM scan_logs 
WHERE scanned_at >= CURRENT_DATE - INTERVAL '1 month' 
GROUP BY DATE_TRUNC('week', scanned_at) 
ORDER BY week_start DESC;"

# Monthly scan patterns (for last year)
echo -e "${YELLOW}Monthly Scan Patterns (Last Year):${NC}" | tee -a $REPORT_FILE
run_psql_query $DB_CONTAINER "SELECT 
  TO_CHAR(DATE_TRUNC('month', scanned_at), 'YYYY-MM') as month,
  COUNT(*) as total_scans, 
  SUM(CASE WHEN is_genuine_scan THEN 1 ELSE 0 END) as genuine_scans 
FROM scan_logs 
WHERE scanned_at >= CURRENT_DATE - INTERVAL '1 year' 
GROUP BY DATE_TRUNC('month', scanned_at) 
ORDER BY month DESC;"

# Top QR codes by scans
echo -e "${YELLOW}Top 10 QR Codes by Scan Count:${NC}" | tee -a $REPORT_FILE
run_psql_query $DB_CONTAINER "SELECT 
  qr.title, 
  qr.id, 
  qr.qr_type, 
  qr.scan_count, 
  qr.genuine_scan_count,
  qr.created_at
FROM qr_codes qr 
ORDER BY qr.scan_count DESC 
LIMIT 10;"

# Top QR codes by genuine scans (most accurate measure)
echo -e "${YELLOW}Top 10 QR Codes by Genuine Scan Count:${NC}" | tee -a $REPORT_FILE
run_psql_query $DB_CONTAINER "SELECT 
  qr.title, 
  qr.id, 
  qr.qr_type, 
  qr.scan_count, 
  qr.genuine_scan_count,
  qr.created_at
FROM qr_codes qr 
ORDER BY qr.genuine_scan_count DESC 
LIMIT 10;"

# Finalize report
echo -e "\n${GREEN}Database schema report completed successfully!${NC}" | tee -a $REPORT_FILE
echo -e "Report saved to: ${YELLOW}$REPORT_FILE${NC}"

# Make the script executable
chmod +x "$0" 