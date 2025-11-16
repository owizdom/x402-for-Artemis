#!/bin/bash
# Complete setup script for X402 Pipeline with dbt and Docker support

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_PATH="$PROJECT_DIR/venv"

echo "=========================================="
echo "X402 Pipeline Setup"
echo "=========================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "[OK] Python version: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing dependencies..."
echo "  - dune-client"
echo "  - pandas"
echo "  - pyarrow"
echo "  - dbt-core"
echo "  - dbt-sqlite"
pip install -q -r requirements.txt

echo ""
echo "[OK] All dependencies installed"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data/databases data/exports data/logs dbt/target dbt/dbt_packages
echo "[OK] Directories created"

# Check for API key
if [ -z "$DUNE_API_KEY" ]; then
    echo ""
    echo "[WARN] Warning: DUNE_API_KEY not set"
    echo ""
    read -p "Enter your Dune API key now (or press Enter to skip): " api_key
    if [ -n "$api_key" ]; then
        export DUNE_API_KEY="$api_key"
        echo "[OK] API key set for this session"
        echo ""
        echo "To make it permanent, add to your ~/.bashrc or ~/.zshrc:"
        echo "  export DUNE_API_KEY='$api_key'"
    fi
else
    echo "[OK] DUNE_API_KEY is set"
fi

# Make scripts executable
echo ""
echo "Setting up scripts..."
chmod +x src/*.py scripts/*.sh 2>/dev/null || true
echo "[OK] Scripts are executable"

# Test installation
echo ""
echo "Testing installation..."
python3 -c "import dune_client; import pandas; import pyarrow; import dbt" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[OK] All packages imported successfully"
else
    echo "[WARN] Some packages may not be installed correctly"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Set your Dune API key:"
echo "   export DUNE_API_KEY='your_key_here'"
echo ""
echo "3. Test the pipeline:"
echo "   python src/x402_pipeline.py list"
echo ""
echo "4. Fetch data:"
echo "   python src/x402_pipeline.py fetch-all"
echo ""
echo "5. Export for Artemis:"
echo "   python src/x402_pipeline.py export"
echo ""
echo "6. Run dbt transformations:"
echo "   dbt run --profiles-dir dbt"
echo ""
echo "7. Or use Docker:"
echo "   make build"
echo "   make up"
echo ""
echo "For more information, see:"
echo "  - docs/ARTEMIS_INTEGRATION.md"
echo "  - docs/DBT_DOCKER_SETUP.md"
echo "  - docs/SCHEDULER_SETUP.md"
echo ""

