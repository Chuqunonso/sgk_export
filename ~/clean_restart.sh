#!/bin/bash

echo "Stopping services..."
launchctl unload ~/Library/LaunchAgents/com.stephanieaguh.sgkexport.plist

echo "Cleaning up log files..."
> ~/sgkexport.out.log
> ~/sgkexport.err.log

echo "Creating log directories..."
mkdir -p ~/sgkExport/sgk_export/logs

echo "Checking PostgreSQL..."
brew services list | grep postgresql@14 > /dev/null
if [ $? -ne 0 ]; then
    echo "Starting PostgreSQL..."
    brew services start postgresql@14
fi

echo "Installing psutil for memory monitoring..."
cd ~/sgkExport/sgk_export
source venv/bin/activate
pip install psutil

echo "Starting application..."
launchctl load ~/Library/LaunchAgents/com.stephanieaguh.sgkexport.plist

echo "Done! Services restarted with optimized settings."
echo "Watch logs with: tail -f ~/sgkexport.out.log ~/sgkexport.err.log" 