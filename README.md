# X402 Pipeline for Artemis

Complete x402 ETL pipeline for fetching query results, transforming them with dbt, and exporting them into Artemis Analytics-ready formats.

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run setup script
bash scripts/setup.sh

# Activate virtual environment
source venv/bin/activate

# Set API key
export DUNE_API_KEY="your_dune_api_key"

# Test
python pipeline/x402_pipeline.py list
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export DUNE_API_KEY="your_dune_api_key"
```

### Option 3: Docker

```bash
# Copy environment file
cp .env.example .env
# Edit .env and add your DUNE_API_KEY

# Build and start
make build
make up

# View logs
make logs
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
├── Makefile              # Convenience commands
└── README.md             # This file
```

## Features

- **Dune Analytics Integration** - Fetch data from 9 Dune queries
- **SQLite Storage** - Local database with timestamps
- **dbt Transformations** - SQL-based data modeling
- **Artemis Export** - Parquet and CSV formats
- **Docker Support** - Containerized deployment
- **Automated Scheduler** - Daily updates
- **Virtual Environment** - Isolated dependencies

## Usage

### Basic Commands

```bash
# Activate virtual environment first
source venv/bin/activate

# List available queries
python src/x402_pipeline.py list

# Fetch all queries
python src/x402_pipeline.py fetch-all

# Export for Artemis
python src/x402_pipeline.py export

# Run dbt transformations
dbt run --profiles-dir dbt
```

### Using Makefile

```bash
# Setup (creates venv and installs deps)
make setup

# Install dependencies
make install

# Test locally
make test-local

# Fetch data
make fetch-all

# Export data
make export

# Run dbt
make dbt-local

# Docker commands
make build
make up
make logs
```

### Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Run dbt
make dbt-run

# Stop services
docker-compose down
```

## 🔄 Automated Updates

### Using Scheduler

```bash
# Run once
python src/scheduler.py run-once

# Run as daemon (continuous)
python src/scheduler.py daemon

# With Docker
docker-compose up -d
```

### Using Cron

```bash
# Add to crontab
0 2 * * * cd /path/to/x402scan-artemis-sync && \
  source venv/bin/activate && \
  export DUNE_API_KEY='your_key' && \
  python src/scheduler.py run-once >> data/logs/cron.log 2>&1
```

## Documentation

- **[Artemis Integration Guide](docs/ARTEMIS_INTEGRATION.md)** - Complete integration guide
- **[dbt & Docker Setup](docs/DBT_DOCKER_SETUP.md)** - dbt and Docker configuration
- **[Scheduler Setup](docs/SCHEDULER_SETUP.md)** - Automated scheduling guide
- **[Quick Start](docs/QUICK_START_ARTEMIS.md)** - Quick reference

## Data Flow

```
Dune Analytics
    ↓
X402 Pipeline (Python)
    ↓
SQLite Database
    ↓
dbt Transformations (SQL)
    ↓
Artemis Export (Parquet/CSV)
```

## Dependencies

- **dune-client** - Dune Analytics API client
- **pandas** - Data manipulation
- **pyarrow** - Parquet file support
- **dbt-core** - Data transformation
- **dbt-sqlite** - SQLite adapter for dbt

## Environment Variables

Create `.env` file or export:

```bash
export DUNE_API_KEY="your_dune_api_key"
export DB_PATH="x402_data.db"
export OUTPUT_DIR="extract"
```

## Docker

The project includes full Docker support:

- **Dockerfile** - Containerizes the pipeline
- **docker-compose.yml** - Orchestrates services
- **Health checks** - Monitors container health
- **Volume mounts** - Persists data and logs

## Testing

```bash
# Test pipeline
source venv/bin/activate
python src/x402_pipeline.py list

# Test dbt
dbt run --profiles-dir dbt
dbt test --profiles-dir dbt

# Test Docker
docker-compose up --build
```

## Monitoring

```bash
# View logs
tail -f logs/scheduler_*.log

# Check database
sqlite3 x402_data.db "SELECT COUNT(*) FROM query_results;"

# Check exports
ls -lh extract/
```

## Development

```bash
# Activate venv
source venv/bin/activate

# Install dev dependencies (if any)
pip install -r requirements.txt

# Run tests
python src/x402_pipeline.py list

# Run dbt
dbt run --profiles-dir dbt
```

## Notes

- Virtual environment is required for local development
- Docker includes all dependencies
- dbt models are in `dbt/models/`
- Exports go to `data/exports/` directory
- Logs are in `data/logs/` directory

## Troubleshooting

### Virtual Environment Issues

```bash
# Recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### dbt Issues

```bash
# Check dbt installation
dbt --version

# Test connection
dbt debug --profiles-dir dbt

# Run with debug
dbt run --profiles-dir dbt --debug
```

### Docker Issues

```bash
# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## License

See LICENSE file for details.

## Contributing

1. Activate virtual environment
2. Install dependencies
3. Make changes
4. Test locally
5. Submit PR

## Support

For issues or questions:
1. Check documentation in `docs/`
2. Review logs in `logs/`
3. Test with `python src/x402_pipeline.py list`

---

**Ready to use!**

Start with `bash scripts/setup.sh` or `make setup` to get started.
