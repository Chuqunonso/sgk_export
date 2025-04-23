print("Starting package load: app/__init__.py")
import os
import sys
import logging
from flask import Flask, render_template, flash, session, redirect, url_for, request
from .extensions import db, login_manager, migrate, csrf
from .models.user import User
from .utils.logging_config import setup_logging
from .config import config
from uuid import UUID
from datetime import datetime, timedelta
from flask_login import current_user, logout_user

logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Application factory function"""
    logger.debug("Starting application initialization")
    logger.debug(f"Python path during create_app: {sys.path}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')
    logger.debug(f"Using configuration: {config_name}")
    
    # Initialize Flask app with explicit template folder
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    logger.debug(f"Template directory set to: {template_dir}")
    logger.debug("Flask app instance created")
    
    # Load configuration
    try:
        app.config.from_object(config[config_name])
        logger.debug("Configuration loaded successfully")
        logger.debug(f"Loaded config values: {dict(app.config)}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}", exc_info=True)
        raise
    
    # Set up logging
    try:
        setup_logging()
        logger.debug("Logging configured")
    except Exception as e:
        logger.error(f"Failed to setup logging: {str(e)}", exc_info=True)
        raise
    
    # Initialize extensions
    try:
        logger.debug("Initializing extensions")
        db.init_app(app)
        migrate.init_app(app, db)
        login_manager.init_app(app)
        csrf.init_app(app)
        logger.debug("Extensions initialized")
    except Exception as e:
        logger.error(f"Failed to initialize extensions: {str(e)}", exc_info=True)
        raise
    
    # CSRF and HTTP 400 Error Handler
    @app.errorhandler(400)
    def handle_csrf_error(e):
        # Check if this is a CSRF error
        if 'CSRF' in str(e) or hasattr(e, 'description') and 'CSRF' in str(e.description):
            logger.error(f"CSRF Error: {str(e)}")
            flash("CSRF validation failed. Please try again.", "error")
            return render_template('error.html', error="Security validation failed. Please try again."), 400
        
        # Handle other 400 errors
        logger.error(f"400 Error: {str(e)}")
        return render_template('error.html', error=f"Bad request: {str(e)}"), 400
    
    # Register blueprints
    try:
        logger.debug("Registering blueprints")
        from .routes import main, auth, shipments, tracking, contacts, admin, api, profile
        app.register_blueprint(main.bp)
        app.register_blueprint(auth.bp)
        app.register_blueprint(shipments.bp)
        app.register_blueprint(tracking.bp)
        app.register_blueprint(contacts.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(api.bp)
        app.register_blueprint(profile.bp)
        logger.debug("Blueprints registered")
    except Exception as e:
        logger.error(f"Failed to register blueprints: {str(e)}", exc_info=True)
        raise
    
    # Configure CSRF to accept tokens from headers (after blueprints are registered)
    from .extensions import configure_csrf
    configure_csrf(app)
    
    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        try:
            # Attempt to convert the user_id to UUID
            uuid_id = UUID(user_id)
            return db.session.get(User, uuid_id)
        except (ValueError, TypeError):
            # If the user_id is not a valid UUID, return None
            # This will cause Flask-Login to treat the user as not authenticated
            return None
    
    # --- Inactivity Check ---    
    @app.before_request
    def before_request_handler():
        # Make session permanent so it uses PERMANENT_SESSION_LIFETIME
        session.permanent = True 
        
        # Check only if user is authenticated and last_activity is set
        if current_user.is_authenticated and 'last_activity' in session:
            now_utc = datetime.utcnow() # Use naive UTC time
            last_active_time = session['last_activity']
            
            # Ensure last_active_time is a datetime object 
            if not isinstance(last_active_time, datetime):
                 # If it's somehow not a datetime, log out the user for safety
                logger.warning(f"Session 'last_activity' was not a datetime object for user {current_user.id}. Logging out.")
                logout_user()
                flash('Session error. Please log in again.', 'warning')
                # Redirect to login immediately if session data is corrupted
                # Check if the current request endpoint is already the login page to avoid redirect loop
                if request.endpoint and request.endpoint != 'auth.login':
                     return redirect(url_for('auth.login'))
                return # Prevent further processing or redirect loop
            
            # Convert last_active_time to naive UTC if it's offset-aware
            if last_active_time.tzinfo is not None:
                logger.debug(f"Converting offset-aware last_activity ({last_active_time}) to naive UTC.")
                last_active_time = last_active_time.replace(tzinfo=None)
            
            # Now both should be naive UTC datetimes
            delta = now_utc - last_active_time
            inactive_duration = timedelta(minutes=2) # Define the 2-minute inactivity limit
            
            # Check if inactive duration is exceeded
            if delta > inactive_duration:
                logger.info(f"User {current_user.id} timed out due to inactivity.")
                logout_user() # Log the user out
                flash('You have been logged out due to inactivity.', 'info')
                # Redirect to login page after logging out due to inactivity
                # Check endpoint to avoid redirect loop if already on login page implicitly
                if request.endpoint and request.endpoint != 'auth.login':
                    return redirect(url_for('auth.login'))
                return # Stop processing the request if redirected
            else:
                # If user is active, update the last_activity time with naive UTC
                session['last_activity'] = now_utc 
        # If user is not authenticated or it's their first request in the session,
        # 'last_activity' might not be set yet, which is fine.
        elif current_user.is_authenticated and 'last_activity' not in session:
            # If authenticated but no timestamp (e.g., session migrated?), set it now.
             session['last_activity'] = datetime.utcnow() # Store naive UTC

    logger.debug("Application initialization completed")
    logger.debug(f"Final app object type: {type(app)}")
    logger.debug(f"Final app object attributes: {dir(app)}")
    return app 