"""
Avatar Data Generator - Flask Application
Main application file with authentication and routing.
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import get_config
from models import db, User, Settings
import os


def create_app():
    """
    Application factory pattern for creating Flask app.

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    csrf = CSRFProtect(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        return User.query.get(int(user_id))

    # Add security headers to all responses
    @app.after_request
    def set_security_headers(response):
        """Add security headers to all HTTP responses."""
        for header, value in app.config['SECURITY_HEADERS'].items():
            response.headers[header] = value

        # Disable caching in development mode
        if app.config.get('DEBUG'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        return response

    # Routes
    @app.route('/')
    def index():
        """Home page - redirect to dashboard if logged in, else login."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        Login page and authentication handler.

        GET: Display login form
        POST: Process login credentials
        """
        # Redirect if already logged in
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember = request.form.get('remember') == 'on'

            # Validate input
            if not email or not password:
                flash('Please provide both email and password.', 'error')
                return render_template('login.html', error='Please provide both email and password.')

            # Find user by email
            user = User.query.filter_by(email=email).first()

            # Verify credentials
            if user and user.is_active and user.check_password(password):
                # Update last login timestamp
                user.update_last_login()
                db.session.commit()

                # Log user in
                login_user(user, remember=remember)

                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                # Invalid credentials
                flash('Invalid email or password.', 'error')
                return render_template('login.html', error='Invalid email or password.')

        # GET request - show login form
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        """Log out the current user and redirect to login page."""
        logout_user()
        flash('You have been logged out successfully.', 'success')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """
        Protected dashboard page - requires authentication.

        Displays user dashboard.
        """
        # Extract user name from email (part before @)
        user_name = current_user.email.split('@')[0]

        return render_template('dashboard.html', user_name=user_name)

    # Avatar generation route
    @app.route('/generate', methods=['GET', 'POST'])
    @login_required
    def generate():
        """
        Avatar generation page.

        GET: Display generation form
        POST: Process avatar generation request (to be implemented)
        """
        # Extract user name from email (part before @)
        user_name = current_user.email.split('@')[0]

        if request.method == 'POST':
            # POST handling to be implemented
            flash('Avatar generation processing will be implemented soon!', 'info')
            return render_template('generate.html', user_name=user_name)

        # GET request - show generation form
        return render_template('generate.html', user_name=user_name)

    @app.route('/datasets')
    @login_required
    def datasets():
        """Datasets management page (placeholder)."""
        flash('Datasets feature coming soon!', 'info')
        return redirect(url_for('dashboard'))

    @app.route('/history')
    @login_required
    def history():
        """Generation history page (placeholder)."""
        flash('History feature coming soon!', 'info')
        return redirect(url_for('dashboard'))

    @app.route('/settings', methods=['GET'])
    @login_required
    def settings():
        """
        Settings page - display current bio prompt settings.

        GET: Display settings form with current values
        """
        # Extract user name from email (part before @)
        user_name = current_user.email.split('@')[0]

        # Load current settings from database
        bio_prompts = {
            'bio_prompt_facebook': Settings.get_value('bio_prompt_facebook', ''),
            'bio_prompt_instagram': Settings.get_value('bio_prompt_instagram', ''),
            'bio_prompt_x': Settings.get_value('bio_prompt_x', ''),
            'bio_prompt_tiktok': Settings.get_value('bio_prompt_tiktok', '')
        }

        return render_template('settings.html', user_name=user_name, bio_prompts=bio_prompts)

    @app.route('/settings/save', methods=['POST'])
    @login_required
    def save_settings():
        """
        Save settings endpoint (AJAX).

        POST: Save updated bio prompts to database
        Returns: JSON response with success/error status
        """
        try:
            # Get JSON data from request
            data = request.get_json()

            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400

            # Define expected settings keys
            expected_keys = [
                'bio_prompt_facebook',
                'bio_prompt_instagram',
                'bio_prompt_x',
                'bio_prompt_tiktok'
            ]

            # Validate that at least one expected key is present
            has_valid_key = any(key in data for key in expected_keys)
            if not has_valid_key:
                return jsonify({
                    'success': False,
                    'error': 'No valid settings provided'
                }), 400

            # Save each setting
            saved_settings = []
            for key in expected_keys:
                if key in data:
                    value = data[key]

                    # Validate value type (should be string)
                    if not isinstance(value, str):
                        return jsonify({
                            'success': False,
                            'error': f'Invalid value type for {key}'
                        }), 400

                    # Save or update setting
                    Settings.set_value(key, value)
                    saved_settings.append(key)

            # Commit all changes to database
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Settings saved successfully',
                'saved_settings': saved_settings
            }), 200

        except Exception as e:
            # Rollback on error
            db.session.rollback()

            # Log error (in production, use proper logging)
            print(f"Error saving settings: {str(e)}")

            return jsonify({
                'success': False,
                'error': 'An error occurred while saving settings'
            }), 500

    @app.route('/forgot-password')
    def forgot_password():
        """Password reset page (placeholder)."""
        flash('Password reset feature coming soon! Please contact your administrator.', 'info')
        return redirect(url_for('login'))

    @app.route('/signup')
    def signup():
        """User registration page (placeholder)."""
        flash('Registration is currently disabled. Please contact your administrator.', 'info')
        return redirect(url_for('login'))

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        flash('Page not found.', 'error')
        return redirect(url_for('dashboard' if current_user.is_authenticated else 'login'))

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        flash('An internal error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard' if current_user.is_authenticated else 'login'))

    return app


if __name__ == '__main__':
    app = create_app()

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    # Run the application
    port = app.config.get('APP_PORT', 7001)
    debug = app.config.get('DEBUG', False)

    print(f"Starting Avatar Data Generator on port {port}...")
    print(f"Debug mode: {debug}")

    app.run(host='0.0.0.0', port=port, debug=debug)
