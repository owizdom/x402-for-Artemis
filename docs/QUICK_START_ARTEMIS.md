# Quick Start: X402 Pipeline → Artemis Analytics

## 3-Step Integration

### Step 1: Fetch Data from Dune
```bash
export DUNE_API_KEY="your_dune_api_key"
python src/x402_pipeline.py fetch-all
```

### Step 2: Export for Artemis
```bash
python src/x402_pipeline.py export
```

### Step 3: Upload to Artemis

**For Artemis Sheets:**
- Upload the `.parquet` file from `data/exports/` directory
- Or use the CSV file for quick inspection

**For Artemis Terminal:**
```bash
artemis load data/exports/artemis_x402_dune_data_*.parquet
```

## What You Get

After running `export`, you'll have:

1. **`artemis_x402_dune_data_*.parquet`** - Main dataset (Parquet format)
2. **`artemis_x402_dune_data_*.csv`** - Human-readable version
3. **`artemis_x402_dune_schema_*.json`** - Schema and metadata

## Data Structure

Each row includes:
- **Query data** - All columns from the Dune query
- **Metadata** (prefixed with `_`):
  - `_query_name` - Query logical name
  - `_query_id` - Dune query ID
  - `_fetched_at` - When data was fetched
  - `_exported_at` - When data was exported

## 🔄 Automated Refresh

Add to crontab for daily updates:
```bash
0 2 * * * cd /path/to/x402scan-artemis-sync && \
  export DUNE_API_KEY="your_key" && \
  python src/x402_pipeline.py fetch-all && \
  python src/x402_pipeline.py export
```

## Full Documentation

See [ARTEMIS_INTEGRATION.md](./ARTEMIS_INTEGRATION.md) for complete integration guide.

