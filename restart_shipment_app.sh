#!/bin/bash

# Script to restart the sgkexport launchd service and ensure PostgreSQL is running

# Get the directory where the script is located
SCRIPT_DIR=$(dirname "$0")
PLIST_PATH="$HOME/Library/LaunchAgents/com.stephanieaguh.sgkexport.plist"
LABEL="com.stephanieaguh.sgkexport"
PG_SERVICE="postgresql@14"

# --- PostgreSQL Check ---
echo "Checking status of PostgreSQL service ($PG_SERVICE)..."
if brew services list | grep "$PG_SERVICE" | grep -q started; then
    echo "PostgreSQL service is running."
else
    echo "PostgreSQL service is not running correctly. Attempting restart..."
    brew services restart "$PG_SERVICE"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to execute PostgreSQL restart command via Homebrew."
        # Optional: Add more specific troubleshooting hints here if needed
        echo "Please check PostgreSQL manually (e.g., brew services list, logs)."
        exit 1
    fi
    sleep 2 # Give the service a moment to stabilize after restart command
    echo "Re-checking status of PostgreSQL service ($PG_SERVICE)..."
    if brew services list | grep "$PG_SERVICE" | grep -q started; then
        echo "PostgreSQL service started successfully."
    else
        # If it still fails, something is wrong with PostgreSQL itself
        echo "Error: Failed to start PostgreSQL service after restart attempt."
        echo "Please check PostgreSQL logs and status manually."
        exit 1
    fi
fi
# --- End PostgreSQL Check ---


echo "Attempting to restart the $LABEL service..."

# Unload the service (stop if running)
echo "Unloading service: $LABEL"
launchctl unload "$PLIST_PATH"
if [ $? -ne 0 ]; then
    echo "Warning: Unload command may have failed (this is often okay if the service wasn't running)."
fi

# Add a small delay to ensure it fully unloads
sleep 1

# Load the service (start it)
echo "Loading service: $LABEL"
launchctl load "$PLIST_PATH"
if [ $? -ne 0 ]; then
    echo "Error: Failed to load the service. Check plist syntax and paths."
    exit 1
fi

echo "Service $LABEL restart initiated."
echo "You can check the status with 'ps aux | grep gunicorn' and logs at:"
echo "  Output: $HOME/sgkexport.out.log"
echo "  Error:  $HOME/sgkexport.err.log"

exit 0 