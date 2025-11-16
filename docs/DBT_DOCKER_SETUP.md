# dbt & Docker Setup Guide

This guide explains how to use the X402 Pipeline with dbt transformations and Docker containerization.

## Overview

The pipeline now includes:
- **dbt** - SQL-based data transformations and modeling
- **Docker** - Containerized deployment for easy setup and scaling

## Architecture

```
┌─────────────────┐
│  Dune Analytics │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  X402 Pipeline  │ (Python)
│  - Fetch data   │
│  - Store SQLite │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  dbt Models     │ (SQL)
│  - Transform    │
│  - Model data   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Artemis Export │
│  - Parquet       │
│  - CSV           │
└─────────────────┘
```

## Quick Start with Docker

### 1. Set Up Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Dune API key
nano .env
```

### 2. Build and Start

```bash
# Build Docker images
make build

# Start services
make up

# View logs
make logs
```

### 3. Verify It's Working

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs x402-pipeline

# Check exports
ls -lh data/exports/
```

## dbt Project Structure

```
dbt/
├── models/
│   ├── staging/          # Staging models (views)
│   │   ├── stg_dune_queries.sql
│   │   ├── stg_transactions.sql
│   │   ├── stg_volume.sql
│   │   └── stg_facilitators.sql
│   └── marts/           # Mart models (tables)
│       ├── fct_transactions.sql
│       ├── fct_volume.sql
│       ├── dim_facilitators.sql
│       └── mart_artemis_export.sql
├── analyses/            # Ad-hoc analyses
├── tests/               # Data tests
├── seeds/               # Seed data
├── macros/              # dbt macros
├── snapshots/           # Snapshots
└── profiles.yml         # Database connection config
```

## dbt Models

### Staging Models

**`stg_dune_queries`** - Base staging model reading from SQLite
- Reads raw query results from `query_results` table
- Prepares data for transformation

**`stg_transactions`** - Transaction data
- Parses JSON from transaction queries
- Extracts: period, project, transaction_count, transaction_percent

**`stg_volume`** - Volume data
- Handles both EVM and Solana volume
- Extracts: period, chain, token, volume_amount

**`stg_facilitators`** - Facilitator data
- Chain-based and Solana facilitators
- Extracts: chain, facilitator, count, percent

### Mart Models

**`fct_transactions`** - Transaction fact table
- Aggregated by period and project
- Total transactions, averages, last updated

**`fct_volume`** - Volume fact table
- Aggregated by period, chain, token
- Total volume, averages, last updated

**`dim_facilitators`** - Facilitator dimension table
- Clean facilitator listing by chain
- Total counts and percentages

**`mart_artemis_export`** - Unified export model
- Combines all metrics into single table
- Optimized for Artemis Analytics
- Denormalized structure for easy querying

## Running dbt

### With Docker

```bash
# Run all models
make dbt-run

# Run specific model
docker-compose run --rm dbt dbt run --select staging --profiles-dir dbt

# Run tests
make dbt-test

# Generate documentation
make dbt-docs

# Compile models (check syntax)
make dbt-compile
```

### Locally

```bash
# Install dbt
pip install dbt-core dbt-sqlite

# Run models
cd /path/to/x402scan-artemis-sync
dbt run --profiles-dir dbt

# Run specific model
dbt run --select mart_artemis_export --profiles-dir dbt

# Test models
dbt test --profiles-dir dbt
```

## Docker Commands

### Basic Operations

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f x402-pipeline

# Restart service
docker-compose restart x402-pipeline
```

### Interactive Commands

```bash
# Open shell in container
make shell
# or
docker-compose exec x402-pipeline /bin/bash

# Run pipeline command
docker-compose exec x402-pipeline python src/x402_pipeline.py list

# Run scheduler once
docker-compose exec x402-pipeline python src/scheduler.py run-once
```

### Data Management

```bash
# View database (from host)
sqlite3 data/databases/x402_data.db "SELECT * FROM query_results LIMIT 5;"

# Copy files from container
docker-compose cp x402-pipeline:/app/data/exports/. ./data/exports/

# Backup database
docker-compose exec x402-pipeline cp data/databases/x402_data.db data/databases/x402_data.db.backup
```

## Development Workflow

### 1. Local Development

```bash
# Set up local environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test pipeline
python src/x402_pipeline.py fetch-all
python src/x402_pipeline.py export

# Test dbt
dbt run --profiles-dir dbt
```

### 2. Test in Docker

```bash
# Build
make build

# Test
docker-compose run --rm x402-pipeline python src/x402_pipeline.py list
```

### 3. Deploy

```bash
# Build production image
docker-compose build

# Start services
docker-compose up -d

# Monitor
make logs
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
DUNE_API_KEY=your_key_here
DB_PATH=data/databases/x402_data.db
OUTPUT_DIR=extract
EXPORT_FORMAT=both
UPDATE_INTERVAL=24
```

### dbt Configuration

Edit `dbt/profiles.yml`:

```yaml
x402_pipeline:
  target: dev
  outputs:
    dev:
      type: sqlite
      database: data/databases/x402_data.db
      schema: main
```

### Docker Compose

Edit `config/docker-compose.yml` to customize:
- Update interval
- Resource limits
- Volume mounts
- Environment variables

## Monitoring

### Check Container Health

```bash
docker-compose ps
```

### View Logs

```bash
# All logs
docker-compose logs

# Recent logs
docker-compose logs --tail=100 x402-pipeline

# Follow logs
docker-compose logs -f x402-pipeline
```

### Check Data

```bash
# List queries
docker-compose exec x402-pipeline python src/x402_pipeline.py list

# Check exports
ls -lh data/exports/

# Check dbt models
docker-compose exec x402-pipeline sqlite3 data/databases/x402_data.db "SELECT name FROM sqlite_master WHERE type='table';"
```

## Troubleshooting

### Issue: dbt Models Not Running

**Check:**
1. Is dbt installed? `docker-compose exec x402-pipeline dbt --version`
2. Are profiles configured? Check `dbt/profiles.yml`
3. Does database exist? `docker-compose exec x402-pipeline ls -la data/databases/x402_data.db`

**Solution:**
```bash
# Run dbt manually to see errors
docker-compose run --rm dbt dbt run --profiles-dir dbt --debug
```

### Issue: Container Won't Start

**Check:**
1. Are ports available?
2. Are volumes writable?
3. Check logs: `docker-compose logs x402-pipeline`

**Solution:**
```bash
# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Data Not Persisting

**Check:**
1. Are volumes mounted? `docker-compose config`
2. Are files in correct location?

**Solution:**
```bash
# Verify volume mounts
docker-compose exec x402-pipeline ls -la /app/

# Check host files
ls -la data/databases/x402_data.db data/exports/ data/logs/
```

## Production Deployment

### Recommended Setup

1. **Use Docker Compose** for orchestration
2. **Set up monitoring** (Prometheus, Grafana)
3. **Configure backups** for database
4. **Set up log rotation**
5. **Use secrets management** for API keys

### Example Production config/docker-compose.yml

```yaml
version: '3.8'

services:
  x402-pipeline:
    build: .
    restart: always
    environment:
      - DUNE_API_KEY=${DUNE_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Best Practices

1. **Version Control**: Commit dbt models and Docker configs
2. **Testing**: Run dbt tests before deploying
3. **Documentation**: Keep dbt docs up to date
4. **Monitoring**: Set up alerts for failures
5. **Backups**: Regular database backups
6. **Security**: Use secrets management, not hardcoded keys

## Next Steps

- Review dbt models in `dbt/models/`
- Customize transformations for your needs
- Set up monitoring and alerts
- Configure production deployment
- Set up CI/CD pipeline

