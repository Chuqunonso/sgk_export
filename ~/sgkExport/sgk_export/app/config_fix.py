"""Configuration fixes for memory and logging issues"""

def apply_fixes(app):
    """Apply performance and stability fixes to the Flask app"""
    import logging
    from logging.handlers import RotatingFileHandler
    import os
    
    # 1. Fix database connection pool settings
    if 'SQLALCHEMY_ENGINE_OPTIONS' in app.config:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'].update({
            'pool_size': 5,        # Reduced from 10
            'max_overflow': 2,     # Reduced from 5
            'pool_timeout': 20,    # Slightly reduced
            'pool_pre_ping': True  # Keep this setting
        })
    
    # 2. Set up proper rotating log handlers
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    
    # Application log handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'application.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplication
    app.logger.handlers = []
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # 3. Add memory monitoring middleware
    @app.before_request
    def check_resources():
        """Monitor memory usage and log if it exceeds threshold"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_use = process.memory_info().rss / 1024 / 1024  # MB
            if memory_use > 500:  # 500MB threshold
                app.logger.warning(f"High memory usage: {memory_use:.2f}MB")
        except:
            # Don't crash if psutil isn't available
            pass
    
    return app 