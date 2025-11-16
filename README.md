# X402 Pipeline for Artemis

Complete x402 ETL pipeline for fetching query results from Dune Analytics, transforming them with dbt, and exporting them into Artemis Analytics-ready formats.

## Overview

This pipeline:
- Fetches data from 9 Dune Analytics queries
- Stores data in a local SQLite database
- Transforms data using dbt (data build tool)
- Exports data in Parquet and CSV formats for Artemis Analytics

## Prerequisites

Before you begin, ensure you have:
- **Python 3.8+** installed
- **Dune Analytics API Key** (get it from [Dune Analytics](https://dune.com))
- **Git** (for cloning the repository)

## Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/owizdom/x402-for-Artemis.git
cd x402-for-Artemis
```

### Step 2: Create Virtual Environment

Create an isolated Python environment:

```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

### Step 4: Install Dependencies

Install all required Python packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- `dune-client` - Dune Analytics API client
- `pandas` - Data manipulation
- `pyarrow` - Parquet file support
- `dbt-core` - Data transformation tool
- `dbt-sqlite` - SQLite adapter for dbt

### Step 5: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
```

Add your Dune API key to the `.env` file:

```bash
echo "DUNE_API_KEY=your_dune_api_key_here" > .env
```

**Or manually edit the `.env` file:**
```
DUNE_API_KEY=your_dune_api_key_here
```

**Note:** The `.env` file is already in `.gitignore` and won't be committed to the repository.

### Step 6: Verify Installation

Test that everything is set up correctly:

```bash
# Make sure venv is activated
source venv/bin/activate

# Load environment variables
export $(cat .env | xargs)

# Test the pipeline
python src/x402_pipeline.py list
```

You should see a list of available queries. If you see an error about the API key, double-check your `.env` file.

## Usage

### Basic Commands

**Always activate the virtual environment first:**
```bash
source venv/bin/activate
export $(cat .env | xargs)
```

#### List Available Queries

```bash
python src/x402_pipeline.py list
```

This shows all 9 available queries with their IDs and last fetch status.

#### Fetch a Single Query

```bash
python src/x402_pipeline.py fetch "num transactions"
```

Replace `"num transactions"` with any query name from the list.

#### Fetch All Queries

```bash
python src/x402_pipeline.py fetch-all
```

This fetches all 9 queries sequentially. It may take a few minutes.

#### View Query Results

Get the first 10 results from a query:
```bash
python src/x402_pipeline.py get "num transactions" --limit 10
```

Get the last 5 results:
```bash
python src/x402_pipeline.py tail "num transactions" -n 5
```

#### Export Data for Artemis

Export all fetched data in Parquet and CSV formats:
```bash
python src/x402_pipeline.py export
```

Files will be saved to `data/exports/` with timestamps.

### Running dbt Transformations

After fetching data, you can run dbt transformations:

```bash
# Activate venv and load env vars
source venv/bin/activate
export $(cat .env | xargs)

# Run dbt models
dbt run --profiles-dir dbt --project-dir .
```

This will execute all SQL models in `dbt/models/` to transform your data.

### Running Tests

Test your dbt models:
```bash
dbt test --profiles-dir dbt --project-dir .
```

## Project Structure

```
.
├── src/                   # Source code
│   ├── x402_pipeline.py   # Core pipeline (fetch, export, dbt)
│   └── scheduler.py       # Automated scheduler
├── scripts/               # Setup and utility scripts
│   ├── setup.sh          # Main setup script
│   └── setup_scheduler.sh # Scheduler setup
├── config/                # Configuration files
│   ├── dbt_project.yml    # dbt project configuration
│   └── docker-compose.yml # Docker orchestration
├── docker/                # Docker files
│   ├── Dockerfile        # Docker image definition
│   └── .dockerignore     # Docker ignore patterns
├── dbt/                   # dbt project
│   ├── models/            # SQL models
│   │   ├── staging/      # Staging models
│   │   └── marts/        # Mart models
│   └── profiles.yml       # Database connection config
├── data/                  # Data storage
│   ├── databases/        # SQLite databases
│   ├── exports/          # Exported data (Parquet/CSV)
│   └── logs/             # Log files
├── docs/                  # Documentation
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not in git)
└── README.md             # This file
```

## Available Queries

The pipeline fetches data from these 9 Dune Analytics queries:

1. **num transactions** (Query ID: 6084845)
2. **num transactions percent** (Query ID: 6084845)
3. **x402 volume evm** (Query ID: 6094619)
4. **volume by token evm** (Query ID: 6094619)
5. **facilitators by chain** (Query ID: 6084891)
6. **facilitators by chain percent** (Query ID: 6084891)
7. **facilitators solana** (Query ID: 6084802)
8. **x402 volume solana** (Query ID: 6094785)
9. **volume by token solana** (Query ID: 6094785)

## Data Flow

```
Dune Analytics API
    ↓
X402 Pipeline (Python)
    ↓
SQLite Database (data/databases/x402_data.db)
    ↓
dbt Transformations (SQL)
    ↓
Artemis Export (Parquet/CSV in data/exports/)
```

## Automated Scheduling

### Using the Scheduler Script

Run the pipeline once:
```bash
source venv/bin/activate
export $(cat .env | xargs)
python src/scheduler.py run-once
```

Run as a background daemon:
```bash
source venv/bin/activate
export $(cat .env | xargs)
python src/scheduler.py daemon
```

### Using Cron (Linux/macOS)

Add to your crontab to run daily at 2 AM:
```bash
crontab -e
```

Add this line (adjust the path):
```bash
0 2 * * * cd /path/to/x402-for-Artemis && source venv/bin/activate && export $(cat .env | xargs) && python src/scheduler.py run-once >> data/logs/cron.log 2>&1
```


### Database Issues

Clear the database if needed:
```bash
sqlite3 data/databases/x402_data.db "DELETE FROM query_results;"
```

### dbt Issues

Check dbt installation:
```bash
dbt --version
```

Test database connection:
```bash
dbt debug --profiles-dir dbt --project-dir .
```

Run with verbose output:
```bash
dbt run --profiles-dir dbt --project-dir . --debug
```

### Import Errors

If you see "dune-client library not installed":
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Monitoring

### Check Database

View how many records are stored:
```bash
sqlite3 data/databases/x402_data.db "SELECT COUNT(*) FROM query_results;"
```

### View Logs

Check scheduler logs:
```bash
tail -f data/logs/scheduler_*.log
```

### Check Exports

List exported files:
```bash
ls -lh data/exports/
```

## Documentation

Additional documentation is available in the `docs/` directory:

- **[Artemis Integration Guide](docs/ARTEMIS_INTEGRATION.md)** - Complete integration guide
- **[dbt & Docker Setup](docs/DBT_DOCKER_SETUP.md)** - dbt and Docker configuration
- **[Scheduler Setup](docs/SCHEDULER_SETUP.md)** - Automated scheduling guide
- **[Quick Start](docs/QUICK_START_ARTEMIS.md)** - Quick reference

## Environment Variables

The following environment variables can be set (in `.env` file or exported):

- `DUNE_API_KEY` - **Required** - Your Dune Analytics API key
- `DB_PATH` - Optional - Path to SQLite database (default: `data/databases/x402_data.db`)
- `OUTPUT_DIR` - Optional - Export directory (default: `data/exports`)
