#!/bin/bash
# ATLAS v2.0 Startup Script with Logging

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/atlas_$(date +%Y%m%d_%H%M%S).log"

# Create logs directory
mkdir -p "$LOG_DIR"

# Change to project directory
cd "$SCRIPT_DIR"

# Log startup
echo "============================================================" | tee -a "$LOG_FILE"
echo "ATLAS v2.0 Starting at $(date)" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!" | tee -a "$LOG_FILE"
    echo "Please create .env with your API credentials" | tee -a "$LOG_FILE"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python Version: $PYTHON_VERSION" | tee -a "$LOG_FILE"

# Check if requirements are installed
if ! python3 -c "import telethon" 2>/dev/null; then
    echo "Installing requirements..." | tee -a "$LOG_FILE"
    pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE"
fi

# Run ATLAS
echo "Starting ATLAS..." | tee -a "$LOG_FILE"
python3 atlas_agent.py 2>&1 | tee -a "$LOG_FILE"
