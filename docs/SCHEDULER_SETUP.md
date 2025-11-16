# Automated Daily Updates - Scheduler Setup

The X402 Pipeline includes an automated scheduler that fetches fresh data from Dune Analytics and exports it for Artemis Analytics on a daily schedule.

## Quick Start

### Option 1: Cron Job (Recommended for Servers)

```bash
# 1. Set up the scheduler
cd /path/to/x402scan-artemis-sync
bash scripts/setup_scheduler.sh

# 2. Edit your crontab
crontab -e

# 3. Add this line (runs daily at 2 AM):
0 2 * * * cd /path/to/x402scan-artemis-sync && source venv/bin/activate && export DUNE_API_KEY='your_key' && python src/scheduler.py run-once >> pipeline/data/logs/cron.log 2>&1
```

### Option 2: Daemon Mode (Continuous)

```bash
# Run as a background daemon (updates every 24 hours)
export DUNE_API_KEY='your_key'
python src/scheduler.py daemon

# Or with custom interval (updates every 12 hours)
python src/scheduler.py daemon --interval 12
```

### Option 3: Systemd Service (Linux)

Create `/etc/systemd/system/x402-pipeline.service`:

```ini
[Unit]
Description=X402 Pipeline Daily Scheduler
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/x402scan-artemis-sync
Environment="DUNE_API_KEY=your_key"
ExecStart=/path/to/x402scan-artemis-sync/venv/bin/python src/scheduler.py daemon
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable x402-pipeline
sudo systemctl start x402-pipeline
sudo systemctl status x402-pipeline
```

## Scheduler Modes

### 1. Run Once (`run-once`)

Executes a single update cycle and exits. Perfect for cron jobs.

```bash
python src/scheduler.py run-once
```

**What it does:**
1. Fetches all queries from Dune Analytics
2. Exports data to Artemis-ready format
3. Logs results and exits

### 2. Daemon Mode (`daemon`)

Runs continuously, updating at regular intervals.

```bash
# Default: updates every 24 hours
python src/scheduler.py daemon

# Custom interval: updates every 12 hours
python src/scheduler.py daemon --interval 12

# Updates every 6 hours
python src/scheduler.py daemon --interval 6
```

**What it does:**
1. Runs continuously in the background
2. Automatically fetches and exports at specified intervals
3. Retries failed updates after 1 hour
4. Logs all activity

## Command Line Options

```bash
python src/scheduler.py [mode] [options]

Modes:
  run-once    - Run a single update cycle
  daemon      - Run continuously with scheduled updates

Options:
  --api-key KEY        Dune API key (overrides DUNE_API_KEY env var)
  --db PATH            Path to SQLite database (default: data/databases/x402_data.db)
  --output-dir DIR     Output directory for exports (default: extract)
  --format FORMAT      Export format: parquet, csv, or both (default: both)
  --interval HOURS     Update interval for daemon mode (default: 24)
  --log-dir DIR        Directory for log files (default: logs)
```

## Logging

All scheduler runs are logged to:
- **Console** - Real-time output
- **Log files** - `data/logs/scheduler_YYYYMMDD.log` (one file per day)

### Log File Structure

```
data/logs/
├── scheduler_20251116.log
├── scheduler_20251117.log
└── ...
```

### Example Log Output

```
2025-11-16 02:00:00 - INFO - ============================================================
2025-11-16 02:00:00 - INFO - Starting daily X402 Pipeline update
2025-11-16 02:00:00 - INFO - ============================================================
2025-11-16 02:00:01 - INFO - Initializing pipeline...
2025-11-16 02:00:01 - INFO - ✓ Pipeline initialized
2025-11-16 02:00:01 - INFO - 
2025-11-16 02:00:01 - INFO - Fetching all queries from Dune...
2025-11-16 02:05:30 - INFO - ✓ Fetch complete: 9/9 queries fetched successfully
2025-11-16 02:05:30 - INFO -   Duration: 329.45 seconds
2025-11-16 02:05:31 - INFO - ✓ Export complete: 5234 rows exported
2025-11-16 02:05:31 - INFO -   Duration: 1.23 seconds
2025-11-16 02:05:31 - INFO - ============================================================
2025-11-16 02:05:31 - INFO - DAILY UPDATE SUMMARY
2025-11-16 02:05:31 - INFO - ============================================================
2025-11-16 02:05:31 - INFO - Queries fetched: 9/9
2025-11-16 02:05:31 - INFO - Rows exported: 5234
2025-11-16 02:05:31 - INFO - Files created: 3
2025-11-16 02:05:31 - INFO - Total duration: 330.68 seconds
2025-11-16 02:05:31 - INFO - Status: ✓ SUCCESS
```

## Cron Job Examples

### Daily at 2 AM
```bash
0 2 * * * cd /path/to/x402scan-artemis-sync && source venv/bin/activate && export DUNE_API_KEY='your_key' && python src/scheduler.py run-once >> pipeline/data/logs/cron.log 2>&1
```

### Twice Daily (2 AM and 2 PM)
```bash
0 2,14 * * * cd /path/to/x402scan-artemis-sync && source venv/bin/activate && export DUNE_API_KEY='your_key' && python src/scheduler.py run-once >> pipeline/data/logs/cron.log 2>&1
```

### Every 12 Hours
```bash
0 */12 * * * cd /path/to/x402scan-artemis-sync && source venv/bin/activate && export DUNE_API_KEY='your_key' && python src/scheduler.py run-once >> pipeline/data/logs/cron.log 2>&1
```

### Weekdays Only (Monday-Friday at 3 AM)
```bash
0 3 * * 1-5 cd /path/to/x402scan-artemis-sync && source venv/bin/activate && export DUNE_API_KEY='your_key' && python src/scheduler.py run-once >> pipeline/data/logs/cron.log 2>&1
```

## Testing the Scheduler

### Test Run Once
```bash
export DUNE_API_KEY='your_key'
python src/scheduler.py run-once
```

### Test Daemon Mode (Short Interval)
```bash
export DUNE_API_KEY='your_key'
# Run for 5 minutes with 1-minute intervals (for testing)
python src/scheduler.py daemon --interval 0.0167  # 1 minute
# Press Ctrl+C to stop
```

## Monitoring

### Check Logs
```bash
# View today's log
tail -f pipeline/data/logs/scheduler_$(date +%Y%m%d).log

# View all logs
ls -lh pipeline/data/logs/

# Search for errors
grep -i error pipeline/data/logs/*.log
```

### Check Last Update
```bash
# Check database for last fetch times
python src/x402_pipeline.py list

# Check export files
ls -lth data/exports/artemis_x402_dune_data_*.parquet | head -1
```

### Verify Cron Job
```bash
# Check if cron job is running
crontab -l

# Check cron logs (system-dependent)
# Linux: grep CRON /var/log/syslog
# macOS: grep cron /var/log/system.log
```

## Troubleshooting

### Issue: Scheduler Not Running

**Check:**
1. Is cron service running? (`systemctl status cron` or `service cron status`)
2. Are there errors in cron logs?
3. Is the path correct in the cron job?
4. Is the virtual environment activated?

**Solution:**
```bash
# Test manually first
export DUNE_API_KEY='your_key'
python src/scheduler.py run-once

# If that works, check cron syntax
crontab -l
```

### Issue: Permission Denied

**Solution:**
```bash
# Make scripts executable
chmod +x src/scheduler.py
chmod +x pipeline/setup_scheduler.sh

# Check file permissions
ls -l src/scheduler.py
```

### Issue: API Key Not Found

**Solution:**
```bash
# Set in environment
export DUNE_API_KEY='your_key'

# Or use command line option
python src/scheduler.py run-once --api-key 'your_key'

# Or add to crontab
0 2 * * * export DUNE_API_KEY='your_key' && ...
```

### Issue: Virtual Environment Not Found

**Solution:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install dune-client pandas pyarrow
```

### Issue: Scheduler Runs But No Data

**Check:**
1. Are queries being fetched? Check logs for fetch status
2. Is export working? Check for export errors
3. Are files being created? Check `data/exports/` directory

**Solution:**
```bash
# Run with verbose output
python src/scheduler.py run-once

# Check database
python src/x402_pipeline.py list

# Check exports
ls -lh data/exports/
```

## Best Practices

1. **Use Cron for Production**: More reliable than daemon mode for long-running systems
2. **Monitor Logs**: Set up log rotation and monitoring
3. **Test First**: Always test manually before setting up automation
4. **Backup Database**: Consider backing up `data/databases/x402_data.db` regularly
5. **Error Alerts**: Set up email/Slack notifications for failures
6. **Resource Limits**: Be aware of API rate limits and adjust intervals accordingly

## Advanced: Email Notifications

Add email notifications on failure:

```bash
# In crontab, add MAILTO
MAILTO=your-email@example.com
0 2 * * * cd /path/to/x402scan-artemis-sync && source venv/bin/activate && export DUNE_API_KEY='your_key' && python src/scheduler.py run-once >> pipeline/data/logs/cron.log 2>&1
```

Or modify the scheduler to send custom notifications (requires additional setup).

## Security Notes

1. **API Key Storage**: Consider using a secrets manager instead of hardcoding
2. **File Permissions**: Ensure log files and database have appropriate permissions
3. **Network Security**: If running on a server, ensure proper firewall rules
4. **Access Control**: Limit who can modify the scheduler configuration

## Support

For issues:
1. Check the logs: `pipeline/data/logs/scheduler_*.log`
2. Test manually: `python src/scheduler.py run-once`
3. Verify API key and network connectivity
4. Check the main pipeline: `python src/x402_pipeline.py list`

