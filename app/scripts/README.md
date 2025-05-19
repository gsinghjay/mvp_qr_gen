# Database Scripts

This directory contains utility scripts for database management and reporting.

## db_schema_report.sh

A comprehensive PostgreSQL database reporting tool that generates detailed information about the database schema, statistics, and scan data for the QR Code Generator application.

### Features

- Detailed table structure information
- Row counts and sample data
- Database size and table sizes
- Index information
- QR code statistics (counts by type, scan averages)
- Device, browser, and OS statistics
- Time series data for scans (hourly, weekly, monthly)
- Top QR codes by scan count
- Analytics-ready data queries for dashboard development

### Usage

```bash
# Run with default settings
./app/scripts/db_schema_report.sh

# Run with custom database settings
DB_NAME=custom_db DB_USER=custom_user ./app/scripts/db_schema_report.sh
```

### Environment Variables

The script supports the following environment variables:

- `DB_CONTAINER`: Name of the PostgreSQL Docker container (default: "qr_generator_postgres")
- `DB_NAME`: Name of the database (default: "qrdb")
- `DB_USER`: Database user (default: "pguser")
- `DB_PASSWORD`: Database password (default: "pgpassword")
- `DB_HOST`: Database host (default: "localhost")

### Output

The script generates a detailed report file in the `database_reports` directory with a timestamp in the filename:

```
database_reports/db_schema_report_YYYYMMDD_HHMMSS.txt
```

### Example Reports

The report includes the following sections:

1. **Database Version**: PostgreSQL version information
2. **Tables**: List of all tables in the database
3. **Table Details**: For each table:
   - Table structure with columns, types, and constraints
   - Row count
   - Sample data (first 5 rows)
4. **Indices**: All database indices with definitions
5. **Database Size**: Total database size
6. **Table Sizes**: Size of each table
7. **Alembic Migration History**: Current migration version if available
8. **QR Scan Statistics**: Total scans and genuine scans
9. **Device/Browser/OS Statistics**: Breakdown of scan sources
10. **QR Code Statistics**: Counts by type, average scans
11. **Time Series Data**: Scan patterns by hour/week/month for analytics dashboard
12. **Top QR Codes**: Most scanned QR codes with details

### Requirements

- Docker with the PostgreSQL container running
- Access to the PostgreSQL database container
- Bash shell environment

### Analytics Dashboard Support

This script is particularly useful for planning the analytics dashboard implementation as it includes queries that provide:

- Time series data in multiple granularities (hourly, weekly, monthly)
- Device and browser statistics
- Genuine vs. total scan breakdowns
- Top performing QR codes

These queries can be directly adapted for use in the analytics dashboard API endpoints. 