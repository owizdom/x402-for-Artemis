# Artemis Analytics Integration Guide

This guide explains how to integrate the X402 Pipeline with Artemis Analytics Sheets and Terminal.

## Overview

The X402 Pipeline fetches data from Dune Analytics queries and exports it in a format ready for Artemis Analytics. The exported data includes:

- **Parquet files** - Optimized for Artemis Analytics ingestion
- **CSV files** - Human-readable format for quick inspection
- **Schema metadata** - JSON file with dataset structure and metadata

## Quick Start

### 1. Fetch Data from Dune

```bash
# Set your Dune API key
export DUNE_API_KEY="your_dune_api_key"

# Fetch all queries
python src/x402_pipeline.py fetch-all

# Or fetch individual queries
python src/x402_pipeline.py fetch "num transactions"
```

### 2. Export for Artemis

```bash
# Export all data in Artemis-ready format
python src/x402_pipeline.py export

# Export only Parquet (recommended for large datasets)
python src/x402_pipeline.py export --format parquet

# Export only CSV (for human inspection)
python src/x402_pipeline.py export --format csv

# Specify custom output directory
python src/x402_pipeline.py export --output-dir ./artemis_data
```

## Output Files

After running `export`, you'll find these files in the `data/exports/` directory (or your specified output directory):

### 1. Parquet File
- **Format**: `artemis_x402_dune_data_YYYYMMDD_HHMMSS.parquet`
- **Purpose**: Primary format for Artemis Analytics ingestion
- **Advantages**: 
  - Columnar storage (efficient for analytics)
  - Compressed (smaller file size)
  - Preserves data types
  - Fast query performance

### 2. CSV File
- **Format**: `artemis_x402_dune_data_YYYYMMDD_HHMMSS.csv`
- **Purpose**: Human-readable format for inspection and validation
- **Use Cases**:
  - Quick data validation
  - Manual inspection
  - Import into spreadsheet tools

### 3. Schema Metadata
- **Format**: `artemis_x402_dune_schema_YYYYMMDD_HHMMSS.json`
- **Purpose**: Dataset documentation and structure information
- **Contains**:
  - Column names and types
  - Query metadata
  - Export timestamp
  - Artemis integration notes

## Data Structure

Each exported row includes:

### Query Data Columns
- All columns from the original Dune query results
- Varies by query (e.g., `period`, `project`, `txs`, `volume`, `chain`, etc.)

### Metadata Columns (prefixed with `_`)
- `_query_name` - Logical name of the query (e.g., "num transactions")
- `_query_id` - Dune query ID
- `_fetched_at` - Timestamp when data was fetched from Dune
- `_exported_at` - Timestamp when data was exported

## Integration with Artemis Sheets

### Option 1: Direct File Upload

1. **Navigate to Artemis Sheets**
2. **Upload Parquet File**:
   - Click "Import Data" or "Upload Dataset"
   - Select the `.parquet` file from `data/exports/` directory
   - Artemis will automatically detect the schema

3. **Verify Data**:
   - Check that all columns are recognized
   - Review the schema metadata JSON file for reference
   - Validate row counts match expectations

### Option 2: Programmatic Integration

If you have Artemis API access:

```python
from artemis import ArtemisClient
import pandas as pd

# Initialize Artemis client
client = ArtemisClient(api_key="your_artemis_api_key")

# Load exported data
df = pd.read_parquet("data/exports/artemis_x402_dune_data_YYYYMMDD_HHMMSS.parquet")

# Upload to Artemis Sheets
client.sheets.upload_dataframe(
    sheet_name="x402_dune_analytics",
    dataframe=df,
    description="X402 Dune Analytics query results"
)
```

## Integration with Artemis Terminal

### Using the CLI

Artemis Terminal can directly read Parquet files:

```bash
# In Artemis Terminal
artemis load data/exports/artemis_x402_dune_data_YYYYMMDD_HHMMSS.parquet

# Query the data
artemis query "SELECT * FROM x402_dune_analytics WHERE _query_name = 'num transactions'"
```

### Programmatic Access

```python
from artemis import ArtemisClient

client = ArtemisClient(api_key="your_artemis_api_key")

# Load dataset into Terminal
result = client.terminal.execute(
    query="""
    SELECT 
        _query_name,
        COUNT(*) as row_count,
        MIN(_fetched_at) as first_fetch,
        MAX(_fetched_at) as last_fetch
    FROM x402_dune_analytics
    GROUP BY _query_name
    """
)
```

## Automated Pipeline

### Scheduled Exports (Recommended)

Use the built-in scheduler for automatic daily updates:

```bash
# Quick setup
bash scripts/setup_scheduler.sh

# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/x402scan-artemis-sync && \
  source venv/bin/activate && \
  export DUNE_API_KEY="your_key" && \
  python src/scheduler.py run-once >> pipeline/data/logs/cron.log 2>&1
```

Or run as a daemon (continuous mode):
```bash
export DUNE_API_KEY="your_key"
python src/scheduler.py daemon
```

**See [SCHEDULER_SETUP.md](./SCHEDULER_SETUP.md) for complete setup instructions.**

### Continuous Integration

For automated workflows:

```python
#!/usr/bin/env python3
"""Automated export script for CI/CD"""

from x402_pipeline import DuneDataPipeline
import os

def main():
    # Initialize pipeline
    pipeline = DuneDataPipeline(api_key=os.getenv("DUNE_API_KEY"))
    
    # Fetch all queries
    print("Fetching all queries...")
    pipeline.fetch_all()
    
    # Export for Artemis
    print("\nExporting for Artemis...")
    summary = pipeline.export_for_artemis(
        output_dir="extract",
        format="both"
    )
    
    print(f"\n[OK] Export complete: {summary['total_rows']} rows")
    return summary

if __name__ == "__main__":
    main()
```

## Data Refresh Strategy

### Recommended Approach

1. **Daily Refresh**: Fetch fresh data daily from Dune
2. **Incremental Updates**: Use `_fetched_at` timestamp to track updates
3. **Version Control**: Keep historical exports for trend analysis

### Example Refresh Workflow

```bash
#!/bin/bash
# refresh_artemis_data.sh

export DUNE_API_KEY="your_key"
cd /path/to/x402scan-artemis-sync
source venv/bin/activate

# Fetch latest data
python src/x402_pipeline.py fetch-all

# Export with timestamp
python src/x402_pipeline.py export --output-dir data/exports/$(date +%Y%m%d)

# Optional: Upload to Artemis via API
# python scripts/upload_to_artemis.py data/exports/$(date +%Y%m%d)
```

## Query-Specific Usage

### Filtering by Query

All exported data includes `_query_name` for easy filtering:

```python
import pandas as pd

df = pd.read_parquet("data/exports/artemis_x402_dune_data_*.parquet")

# Filter by query name
transactions = df[df["_query_name"] == "num transactions"]
volume_evm = df[df["_query_name"] == "x402 volume evm"]
facilitators = df[df["_query_name"] == "facilitators by chain"]
```

### Combining Multiple Queries

```python
# Group by query and analyze
summary = df.groupby("_query_name").agg({
    "row_count": "count",
    "_fetched_at": ["min", "max"]
})
```

## Troubleshooting

### Issue: Missing pandas/pyarrow

**Error**: `ImportError: pandas and pyarrow are required`

**Solution**:
```bash
pip install pandas pyarrow
```

### Issue: No data to export

**Error**: `No data to export. Run 'fetch-all' first`

**Solution**:
```bash
# Fetch data first
python src/x402_pipeline.py fetch-all

# Then export
python src/x402_pipeline.py export
```

### Issue: Parquet file too large

**Solution**: Use Parquet's built-in compression or split by query:

```python
# Export each query separately
for query_name in QUERY_IDS.keys():
    data = pipeline.get_query(query_name)
    if data:
        df = pd.DataFrame(data)
        df.to_parquet(f"data/exports/{query_name}.parquet")
```

## Best Practices

1. **Regular Exports**: Set up automated daily/weekly exports
2. **Version Control**: Keep historical exports with timestamps
3. **Validation**: Always check row counts and data quality
4. **Documentation**: Review schema JSON files for column meanings
5. **Monitoring**: Track export success/failure in your logging system

## Support

For issues with:
- **X402 Pipeline**: Check `src/x402_pipeline.py` documentation
- **Artemis Integration**: Refer to Artemis Analytics documentation
- **Dune Queries**: Check Dune Analytics query documentation

## Example Queries for Artemis

### Transaction Trends
```sql
SELECT 
    period,
    project,
    SUM(txs) as total_transactions
FROM x402_dune_analytics
WHERE _query_name = 'num transactions'
GROUP BY period, project
ORDER BY period DESC
```

### Volume Analysis
```sql
SELECT 
    _query_name,
    SUM(volume) as total_volume,
    COUNT(*) as data_points
FROM x402_dune_analytics
WHERE _query_name LIKE '%volume%'
GROUP BY _query_name
```

### Facilitator Distribution
```sql
SELECT 
    chain,
    COUNT(*) as facilitator_count
FROM x402_dune_analytics
WHERE _query_name = 'facilitators by chain'
GROUP BY chain
ORDER BY facilitator_count DESC
```

