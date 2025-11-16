# X402 Pipeline - Artemis Analytics Integration Package

## Overview

The **X402 Pipeline** is a production-ready data pipeline that fetches query results from Dune Analytics and exports them in a format optimized for Artemis Analytics Sheets and Terminal.

## What We're Delivering

### 1. **Automated Data Pipeline** (`src/x402_pipeline.py`)
- Single-file, self-contained Python script
- Fetches data from 9 Dune Analytics queries
- Stores data locally in SQLite with timestamps
- Exports to Artemis-ready formats (Parquet + CSV)
- Includes retry logic and error handling
- Full CLI interface for easy operation

### 2. **Artemis-Ready Data Exports**
- **Parquet files** - Optimized columnar format for analytics
- **CSV files** - Human-readable format for validation
- **Schema metadata** - Complete dataset documentation in JSON

### 3. **Complete Documentation**
- Integration guide with step-by-step instructions
- Quick start guide for immediate use
- Example queries and use cases

## Key Features

**Production Ready**
- Clean, well-commented code
- Error handling and retry logic
- Comprehensive logging
- Type hints and documentation

**Artemis Optimized**
- Parquet format for efficient analytics
- Metadata columns for tracking
- Schema documentation included
- Compatible with both Sheets and Terminal

**Easy Integration**
- Simple CLI commands
- Programmatic API available
- Automated export functionality
- Ready for scheduled updates

## Data Sources

The pipeline fetches data from 9 Dune Analytics queries:

1. **num transactions** (Query ID: 6084845)
2. **num transactions percent** (Query ID: 6084845)
3. **x402 volume evm** (Query ID: 6094619)
4. **volume by token evm** (Query ID: 6094619)
5. **facilitators by chain** (Query ID: 6084891)
6. **facilitators by chain percent** (Query ID: 6084891)
7. **facilitators solana** (Query ID: 6084802)
8. **x402 volume solana** (Query ID: 6094785)
9. **volume by token solana** (Query ID: 6094785)

## Quick Integration Steps

### For Artemis Team

1. **Review the Pipeline**
   ```bash
   # View the main pipeline file
   cat src/x402_pipeline.py
   ```

2. **Test the Export**
   ```bash
   # Set Dune API key
   export DUNE_API_KEY="your_key"
   
   # Fetch and export data
   python src/x402_pipeline.py fetch-all
   python src/x402_pipeline.py export
   ```

3. **Import to Artemis**
   - Upload the `.parquet` file from `data/exports/` directory
   - Or use the CSV for quick validation
   - Review the schema JSON for column documentation

### For End Users

1. **Install Dependencies**
   ```bash
   pip install dune-client pandas pyarrow
   ```

2. **Run Pipeline**
   ```bash
   export DUNE_API_KEY="your_key"
   python src/x402_pipeline.py fetch-all
   python src/x402_pipeline.py export
   ```

3. **Use in Artemis**
   - Import Parquet file to Artemis Sheets
   - Or load into Artemis Terminal for querying

## File Structure

```
x402scan-artemis-sync/
├── pipeline/
│   └── x402_pipeline.py          # Main pipeline (single file, ready to use)
├── docs/
│   ├── ARTEMIS_INTEGRATION.md     # Complete integration guide
│   ├── QUICK_START_ARTEMIS.md     # Quick start guide
│   └── ARTEMIS_PRESENTATION.md    # This file
├── data/exports/                        # Export output directory
│   ├── artemis_x402_dune_data_*.parquet
│   ├── artemis_x402_dune_data_*.csv
│   └── artemis_x402_dune_schema_*.json
└── README.md                       # Project overview
```

## Data Format

### Exported Files

**Parquet File** (`artemis_x402_dune_data_*.parquet`)
- Columnar storage format
- Optimized for analytics queries
- Compressed for efficient storage
- Preserves data types

**CSV File** (`artemis_x402_dune_data_*.csv`)
- Human-readable format
- Easy validation and inspection
- Compatible with spreadsheet tools

**Schema File** (`artemis_x402_dune_schema_*.json`)
- Complete column documentation
- Data types and nullability
- Query metadata
- Artemis integration notes

### Data Structure

Each exported row includes:

**Query Data Columns** (varies by query):
- Example: `period`, `project`, `txs`, `volume`, `chain`, `token`, etc.

**Metadata Columns** (prefixed with `_`):
- `_query_name` - Logical query name
- `_query_id` - Dune query ID
- `_fetched_at` - Fetch timestamp
- `_exported_at` - Export timestamp

## Integration Options

### Option 1: Direct File Upload
- Upload Parquet files directly to Artemis Sheets
- Simple drag-and-drop interface
- Automatic schema detection

### Option 2: Programmatic API
- Use Artemis Python SDK
- Automated uploads
- Integration with CI/CD pipelines

### Option 3: Scheduled Exports
- Set up cron jobs for regular updates
- Automated data refresh
- Version control with timestamps

## Example Use Cases

### 1. Transaction Analysis
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

### 2. Volume Trends
```sql
SELECT 
    _query_name,
    SUM(volume) as total_volume,
    COUNT(*) as data_points
FROM x402_dune_analytics
WHERE _query_name LIKE '%volume%'
GROUP BY _query_name
```

### 3. Facilitator Distribution
```sql
SELECT 
    chain,
    COUNT(*) as facilitator_count
FROM x402_dune_analytics
WHERE _query_name = 'facilitators by chain'
GROUP BY chain
ORDER BY facilitator_count DESC
```

## Technical Specifications

### Requirements
- Python 3.8+
- Dune API key
- Dependencies: `dune-client`, `pandas`, `pyarrow`

### Performance
- Handles large datasets efficiently
- Retry logic for API failures
- Rate limiting to respect API limits
- Optimized Parquet exports

### Reliability
- Automatic retries with exponential backoff
- Error handling and logging
- Data validation before export
- Timestamp tracking for audit trails

## Support & Documentation

### Documentation Files
- **ARTEMIS_INTEGRATION.md** - Complete integration guide
- **QUICK_START_ARTEMIS.md** - Quick start instructions
- **ARTEMIS_PRESENTATION.md** - This presentation document

### Code Documentation
- Inline comments throughout the pipeline
- Docstrings for all functions
- Type hints for better IDE support
- CLI help text for all commands

## Next Steps

1. **Review the Pipeline Code**
   - Single file: `src/x402_pipeline.py`
   - Clean, production-ready code
   - Easy to understand and modify

2. **Test the Export**
   - Run `fetch-all` to get sample data
   - Run `export` to generate Artemis files
   - Verify output files in `data/exports/` directory

3. **Integrate with Artemis**
   - Upload Parquet files to Artemis Sheets
   - Or load into Artemis Terminal
   - Start querying and analyzing!

## Questions?

- Check `docs/ARTEMIS_INTEGRATION.md` for detailed instructions
- Review `src/x402_pipeline.py` for code details
- All files are ready to use immediately

---

**Ready for Integration**

The pipeline is complete, tested, and ready for immediate use with Artemis Analytics.

