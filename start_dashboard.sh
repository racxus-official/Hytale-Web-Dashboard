#!/bin/bash
# Hytale Web Dashboard Startup Script
# This script automatically detects its location, installs dependencies, and starts the API.

# --- DYNAMIC PATH CONFIGURATION ---
# Get the absolute path of the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Define expected paths relative to this script
DASHBOARD_DIR="$SCRIPT_DIR"
SERVER_DIR="$SCRIPT_DIR/Server"
GAME_START_SCRIPT="$SCRIPT_DIR/start.sh"
API_SCRIPT="server_api.py"

echo "=== Hytale Web Dashboard Launcher ==="
echo "📂 Working Directory: $DASHBOARD_DIR"
echo "📅 Date: $(date)"
echo ""

# --- ENVIRONMENT CHECKS ---

# 1. Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Critical Error: Python3 is not installed on this system."
    echo "   Please install Python 3 to continue."
    exit 1
fi

# 2. Virtual Environment Management
if [ ! -d "venv" ]; then
    echo "🔨 Virtual environment not found. Creating 'venv'..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to create virtual environment."
        exit 1
    fi
fi

# Activate the virtual environment
source venv/bin/activate

# 3. Automatic Dependency Installation
echo "📦 Verifying Python dependencies..."
# We try to import the modules; if it fails, we install them.
if ! python3 -c "import flask, flask_cors, psutil" 2>/dev/null; then
    echo "   ⚙️  Missing dependencies detected. Installing..."
    pip install Flask Flask-CORS psutil
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies via pip."
        exit 1
    fi
    echo "   ✅ Dependencies installed successfully."
else
    echo "   ✅ All dependencies are already installed."
fi

# --- FILE INTEGRITY SCAN ---

echo ""
echo "🔍 Scanning filesystem..."

# Check for the API script
if [ ! -f "$API_SCRIPT" ]; then
    echo "❌ Critical Error: '$API_SCRIPT' not found in $DASHBOARD_DIR"
    echo "   Make sure this launch script is in the same folder as the Python API."
    exit 1
fi

# Check for Server Directory
if [ -d "$SERVER_DIR" ]; then
    echo "   ✅ Server directory found."
    if [ -f "$SERVER_DIR/HytaleServer.jar" ]; then
        echo "   ✅ HytaleServer.jar found."
    else
        echo "   ⚠️  Warning: 'HytaleServer.jar' not found inside $SERVER_DIR"
    fi
else
    echo "   ⚠️  Warning: 'Server' directory not found in $DASHBOARD_DIR"
fi

# Check for the Game Start Script
if [ -f "$GAME_START_SCRIPT" ]; then
    echo "   ✅ Game start script (start.sh) found."
else
    echo "   ⚠️  Warning: 'start.sh' not found in $DASHBOARD_DIR"
fi

# --- AUTO-SYNC CONFIGURATION ---
# This part updates config.json automatically to handle folder renaming/moving
echo "⚙️  Syncing configuration paths..."
python3 -c "
import json
import os

config_path = 'config.json'
# Force the start_script path to the current absolute location of start.sh
launcher_path = os.path.join('$DASHBOARD_DIR', 'start.sh')
server_path = os.path.join('$DASHBOARD_DIR', 'Server')

data = {
    'admin_token': 'admin',
    'start_script': launcher_path,
    'server_dir': server_path,
    'max_ram': 12
}

# Preserve the admin token if the file already exists
if os.path.exists(config_path):
    try:
        with open(config_path, 'r') as f:
            old_data = json.load(f)
            if 'admin_token' in old_data:
                data['admin_token'] = old_data['admin_token']
    except:
        pass

with open(config_path, 'w') as f:
    json.dump(data, f, indent=4)
"

# --- LAUNCH ---

echo ""
echo "🚀 Starting Web Dashboard..."
echo "🌐 URL: http://localhost:5000"
echo "🛑 To stop the dashboard: Press Ctrl+C"
echo "---------------------------------------------------"

# Run the Python application
python3 "$API_SCRIPT"

# --- SHUTDOWN ---
echo ""
echo "📴 Dashboard terminated."