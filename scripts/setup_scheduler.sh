#!/bin/bash
# Setup script for X402 Pipeline daily scheduler
# This script helps set up automatic daily updates via cron

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_DIR/venv"
SCHEDULER_SCRIPT="$PROJECT_DIR/src/scheduler.py"

echo "X402 Pipeline Scheduler Setup"
echo "=============================="
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -q dune-client pandas pyarrow

# Check for API key
if [ -z "$DUNE_API_KEY" ]; then
    echo ""
    echo "[WARN] Warning: DUNE_API_KEY not set"
    echo "Please set it before running the scheduler:"
    echo "  export DUNE_API_KEY='your_api_key_here'"
    echo ""
    read -p "Enter your Dune API key now (or press Enter to skip): " api_key
    if [ -n "$api_key" ]; then
        export DUNE_API_KEY="$api_key"
        echo "[OK] API key set for this session"
    fi
fi

# Make scheduler executable
chmod +x "$SCHEDULER_SCRIPT"

echo ""
echo "Setup complete!"
echo ""
echo "To test the scheduler, run:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  export DUNE_API_KEY='your_key'"
echo "  python src/scheduler.py run-once"
echo ""
echo "To set up daily cron job, run:"
echo "  crontab -e"
echo ""
echo "And add this line (runs daily at 2 AM):"
echo "  0 2 * * * cd $PROJECT_DIR && source venv/bin/activate && export DUNE_API_KEY='your_key' && python src/scheduler.py run-once >> data/logs/cron.log 2>&1"
echo ""
echo "Or use the daemon mode (runs continuously):"
echo "  python src/scheduler.py daemon"
echo ""

