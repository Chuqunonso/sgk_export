# Guide: Running a Flask/Gunicorn App on macOS Login using launchd

This guide explains how to configure a Python Flask application served by Gunicorn to start automatically when a user logs into macOS, using the `launchd` service manager.

## Prerequisites

*   A working Flask application.
*   A virtual environment (`venv`) for the project.
*   Gunicorn installed in the virtual environment (`pip install gunicorn`).
*   Your application should be runnable via a command like `gunicorn <options> wsgi:app`.

## Steps

### 1. Find the Gunicorn Executable Path

`launchd` needs the absolute path to the `gunicorn` executable *inside* your project's virtual environment.

```bash
# Navigate to your project directory
cd /path/to/your/project

# Activate the virtual environment
source venv/bin/activate

# Find the path
which gunicorn
# Example output: /Users/stephanieaguh/sgkExport/sgk_export/venv/bin/gunicorn

# Deactivate (optional for this step)
# deactivate
```
Note down this full path.

### 2. Create the `launchd` `.plist` File

`launchd` uses `.plist` (Property List) XML files for configuration. Create a file specifically for your application in the user's LaunchAgents directory.

**File Location:** `~/Library/LaunchAgents/`
**Recommended Naming:** `com.yourdomain.yourappname.plist` (Use reverse domain name notation).

**Example File:** `~/Library/LaunchAgents/com.stephanieaguh.sgkexport.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Label: A unique identifier for this service -->
    <key>Label</key>
    <string>com.stephanieaguh.sgkexport</string>

    <!-- ProgramArguments: The command and its arguments -->
    <key>ProgramArguments</key>
    <array>
        <!-- Path to gunicorn found in Step 1 -->
        <string>/Users/stephanieaguh/sgkExport/sgk_export/venv/bin/gunicorn</string>
        <!-- Gunicorn arguments (e.g., config file, WSGI app) -->
        <string>-c</string>
        <string>gunicorn.conf.py</string>
        <string>wsgi:app</string>
    </array>

    <!-- WorkingDirectory: The directory where the command should run -->
    <key>WorkingDirectory</key>
    <string>/Users/stephanieaguh/sgkExport/sgk_export</string>

    <!-- RunAtLoad: Start the service automatically when the user logs in -->
    <key>RunAtLoad</key>
    <true/>

    <!-- KeepAlive: Restart the service if it crashes or exits unexpectedly -->
    <key>KeepAlive</key>
    <true/>

    <!-- StandardOutPath: File to redirect standard output (stdout) -->
    <key>StandardOutPath</key>
    <string>/Users/stephanieaguh/sgkexport.out.log</string>

    <!-- StandardErrorPath: File to redirect standard error (stderr) -->
    <key>StandardErrorPath</key>
    <string>/Users/stephanieaguh/sgkexport.err.log</string>

    <!-- EnvironmentVariables: Set required environment variables -->
    <!-- launchd runs with a minimal environment, so explicitly define -->
    <!-- variables needed by your app (e.g., secrets, database URLs) -->
    <key>EnvironmentVariables</key>
    <dict>
        <!-- Essential for finding executables if not using absolute paths everywhere -->
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/stephanieaguh/sgkExport/sgk_export/venv/bin</string>
        <!-- Example: Database connection string -->
        <key>DATABASE_URL</key>
        <string>postgresql://stephanieaguh@localhost/sgk_export_db</string>
        <!-- Example: Flask environment mode -->
        <key>FLASK_ENV</key>
        <string>development</string> <!-- Or 'production' -->
        <!-- Example: Flask Secret Key -->
        <key>SECRET_KEY</key>
        <string>your-very-secure-secret-key-replace-me</string>
        <!-- Add any other environment variables your app needs -->
    </dict>
</dict>
</plist>
```

**Important:** Customize the paths, label, command arguments, and environment variables for your specific project.

### 3. Load and Start the Service

Use the `launchctl` command to tell `launchd` about your new service.

```bash
# Load the service definition (this also starts it if RunAtLoad is true)
launchctl load ~/Library/LaunchAgents/com.stephanieaguh.sgkexport.plist

# Optional: Explicitly start if needed (usually not necessary with RunAtLoad)
# launchctl start com.stephanieaguh.sgkexport
```

### 4. Verify the Service

Check if the service is running correctly:

*   **Check Processes:** Look for your Gunicorn master and worker processes.
    ```bash
    ps aux | grep gunicorn
    ```
*   **Check Logs:** Examine the output and error logs defined in the `.plist`.
    ```bash
    tail -f ~/sgkexport.out.log
    tail -f ~/sgkexport.err.log
    ```
*   **Check Application:** Access your application via a web browser.
*   **Reboot Test:** Restart your Mac, log in, and verify the service started automatically using the methods above.

## Managing the Service

*   **Stop the Service Temporarily:**
    ```bash
    launchctl stop com.stephanieaguh.sgkexport
    ```
*   **Unload the Service (Stop and prevent auto-start):**
    ```bash
    launchctl unload ~/Library/LaunchAgents/com.stephanieaguh.sgkexport.plist
    ```
*   **Reload/Restart (To apply code changes or `.plist` updates):**
    ```bash
    launchctl unload ~/Library/LaunchAgents/com.stephanieaguh.sgkexport.plist
    launchctl load ~/Library/LaunchAgents/com.stephanieaguh.sgkexport.plist
    ```

## Troubleshooting

*   **Load Errors (`launchctl load` fails):**
    *   Check `.plist` syntax: `plutil -lint ~/Library/LaunchAgents/com.your.label.plist`
    *   Verify all paths in the `.plist` are correct and accessible by your user.
    *   Ensure the `WorkingDirectory` exists.
    *   Ensure log file directories are writable (e.g., your home directory `~` is fine, `/tmp` usually is).
    *   Check permissions on the `.plist` file itself (`chmod 644 ...`).
*   **Service Starts but App Doesn't Work (Check Logs):**
    *   **Missing Environment Variables:** This is common. Ensure *all* required variables (`SECRET_KEY`, `DATABASE_URL`, etc.) are in the `EnvironmentVariables` dict in the `.plist`.
    *   **Path Issues:** Ensure the `PATH` includes the `venv/bin`.
    *   **Permissions:** Make sure the user running the service can access project files and the database.
    *   **Application Errors:** Debug errors shown in the log files just like normal application errors. 