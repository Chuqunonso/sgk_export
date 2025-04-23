#!/bin/bash

# Script to restart the sgkexport launchd service

# Get the directory where the script is located
SCRIPT_DIR=$(dirname "$0")
PLIST_PATH="$HOME/Library/LaunchAgents/com.stephanieaguh.sgkexport.plist"
LABEL="com.stephanieaguh.sgkexport"

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