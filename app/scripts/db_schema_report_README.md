# Database Schema Report Script

## Overview

This script (`db_schema_report.sh`) generates a comprehensive report of the PostgreSQL database schema and scan data for the QR Code Generator application. It is particularly useful for understanding the database structure before implementing new features, such as the analytics dashboard.

## Analytics Dashboard Support

The script includes several queries that directly support the planned analytics dashboard implementation:

### Time Series Data
```sql
-- Hourly scan patterns
SELECT 
  EXTRACT(HOUR FROM scanned_at) as hour, 
  COUNT(*) as total_scans, 
  SUM(CASE WHEN is_genuine_scan THEN 1 ELSE 0 END) as genuine_scans 
FROM scan_logs 
WHERE scanned_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' 
GROUP BY hour 
ORDER BY hour;

-- Weekly scan patterns
SELECT 
  TO_CHAR(DATE_TRUNC('week', scanned_at), 'YYYY-MM-DD') as week_start,
  COUNT(*) as total_scans, 
  SUM(CASE WHEN is_genuine_scan THEN 1 ELSE 0 END) as genuine_scans 
FROM scan_logs 
WHERE scanned_at >= CURRENT_DATE - INTERVAL '1 month' 
GROUP BY DATE_TRUNC('week', scanned_at) 
ORDER BY week_start DESC;

-- Monthly scan patterns
SELECT 
  TO_CHAR(DATE_TRUNC('month', scanned_at), 'YYYY-MM') as month,
  COUNT(*) as total_scans, 
  SUM(CASE WHEN is_genuine_scan THEN 1 ELSE 0 END) as genuine_scans 
FROM scan_logs 
WHERE scanned_at >= CURRENT_DATE - INTERVAL '1 year' 
GROUP BY DATE_TRUNC('month', scanned_at) 
ORDER BY month DESC;
```

### Device Statistics
```sql
-- Device breakdown
SELECT device_family, COUNT(*) as count 
FROM scan_logs 
GROUP BY device_family 
ORDER BY count DESC 
LIMIT 10;

-- Browser breakdown
SELECT browser_family, COUNT(*) as count 
FROM scan_logs 
GROUP BY browser_family 
ORDER BY count DESC 
LIMIT 10;

-- OS breakdown
SELECT os_family, COUNT(*) as count 
FROM scan_logs 
GROUP BY os_family 
ORDER BY count DESC 
LIMIT 10;
```

### Top Performing QR Codes
```sql
-- By total scans
SELECT 
  qr.title, 
  qr.id, 
  qr.qr_type, 
  qr.scan_count, 
  qr.genuine_scan_count,
  qr.created_at
FROM qr_codes qr 
ORDER BY qr.scan_count DESC 
LIMIT 10;

-- By genuine scans
SELECT 
  qr.title, 
  qr.id, 
  qr.qr_type, 
  qr.scan_count, 
  qr.genuine_scan_count,
  qr.created_at
FROM qr_codes qr 
ORDER BY qr.genuine_scan_count DESC 
LIMIT 10;
```

## Adapting Queries for the Analytics Dashboard

When implementing the analytics dashboard endpoints, you can adapt these queries by:

1. **Adding Date Range Filters**:
   ```sql
   WHERE scanned_at BETWEEN :start_date AND :end_date
   ```

2. **Filtering by QR Code ID**:
   ```sql
   WHERE qr_code_id = :qr_id
   ```

3. **Genuine Scan Filtering**:
   ```sql
   WHERE is_genuine_scan = TRUE
   ```

4. **Custom Grouping**:
   ```sql
   -- For daily data points
   GROUP BY DATE(scanned_at)
   
   -- For hourly data points
   GROUP BY DATE(scanned_at), EXTRACT(HOUR FROM scanned_at)
   ```

## Database Schema Notes

Key tables and fields for the analytics dashboard implementation:

### QR Codes Table (`qr_codes`)
- `id`: Primary key (UUID)
- `title`: User-friendly title
- `qr_type`: Type of QR code (static/dynamic)
- `scan_count`: Total number of scans
- `genuine_scan_count`: Number of genuine scans
- `last_scan_at`: Timestamp of last scan
- `first_genuine_scan_at`: Timestamp of first genuine scan
- `last_genuine_scan_at`: Timestamp of last genuine scan

### Scan Logs Table (`scan_logs`)
- `id`: Primary key (UUID)
- `qr_code_id`: Foreign key to QR code
- `scanned_at`: Timestamp of scan
- `is_genuine_scan`: Whether scan came from QR code (vs direct URL)
- `device_family`: Device type
- `os_family`: Operating system
- `browser_family`: Browser type
- `is_mobile`, `is_tablet`, `is_pc`, `is_bot`: Device type flags

## Usage with the Analytics Dashboard Plan

The analytics dashboard plan in `docs/plans/analytics-dashboard.md` describes multiple endpoints that need to be implemented. The queries in this script can be directly used for:

1. **Task 1.2** - Creating the scan log fragment
2. **Task 1.3** - Creating device/browser/OS stats
3. **Task 1.4** - Creating chart data for time series

## Running the Script

```bash
# Run the script
./app/scripts/db_schema_report.sh

# Check the generated report
less database_reports/db_schema_report_*.txt
```

Reports are automatically saved to the `database_reports` directory with a timestamp in the filename. 