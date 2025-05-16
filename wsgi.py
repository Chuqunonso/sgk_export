#!/usr/bin/env python3
import os
import sys
import logging

# Configure logging - reduce verbosity to prevent log file issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wsgi')
logger.setLevel(logging.WARNING)

# Minimal debug output
logger.debug(f"Python path in wsgi.py: {sys.path}")

try:
    # Import and create the Flask app
    from app import create_app
    app = create_app()
    
    # Apply performance and stability fixes
    try:
        from app.config_fix import apply_fixes
        app = apply_fixes(app)
        logger.warning("Applied performance and stability fixes")
    except Exception as e:
        logger.error(f"Failed to apply fixes: {str(e)}")
except Exception as e:
    logger.error("Failed to initialize Flask application in WSGI: %s", str(e), exc_info=True)
    raise

# This is used by Gunicorn
if __name__ == '__main__':
    app.run() 