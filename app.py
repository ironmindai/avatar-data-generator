"""
Avatar Data Generator - Flask Application
Main application file with authentication and routing.
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import get_config
from models import db, User, Settings, Config, GenerationTask, GenerationResult
import os
import atexit
import logging
import io
import csv
import zipfile
import requests
import tempfile
import shutil
from datetime import datetime


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

    # Test log to verify journald is capturing app output
    print("[STARTUP] Avatar Data Generator application initialized successfully", flush=True)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'

    # Initialize APScheduler for background task processing
    # Only start scheduler if we're not in a reloader process and not running Flask CLI
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler = BackgroundScheduler()
        scheduler.start()

        # Suppress APScheduler's INFO and WARNING logs to keep logs clean when idle
        # Only show ERROR and above (critical errors will still be visible)
        logging.getLogger('apscheduler').setLevel(logging.ERROR)

        print(f"[SCHEDULER] Background scheduler started - checking for tasks every {app.config['WORKER_INTERVAL']} seconds", flush=True)

        # Add data generation task processor job (supports up to 3 parallel tasks)
        def scheduled_task_processor():
            """Wrapper function to run data generation task processor with Flask app context."""
            from concurrent.futures import ThreadPoolExecutor, as_completed
            from workers.task_processor import process_single_task

            def worker_with_context():
                """Worker function that establishes its own Flask app context."""
                with app.app_context():
                    try:
                        return process_single_task()
                    except Exception as e:
                        logging.error(f"[SCHEDULER] Error in worker thread: {e}", exc_info=True)
                        return False

            try:
                # Process up to 3 tasks in parallel
                max_parallel_tasks = 3
                futures = []

                with ThreadPoolExecutor(max_workers=max_parallel_tasks) as executor:
                    # Submit up to 3 tasks
                    for _ in range(max_parallel_tasks):
                        future = executor.submit(worker_with_context)
                        futures.append(future)

                    # Wait for all to complete (they'll return False if no tasks available)
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logging.error(f"[SCHEDULER] Error in parallel data generation task: {e}", exc_info=True)

            except Exception as e:
                logging.error(f"[SCHEDULER] Error processing data generation tasks: {e}", exc_info=True)

        # Schedule the data generation task processor to run every WORKER_INTERVAL seconds
        scheduler.add_job(
            func=scheduled_task_processor,
            trigger=IntervalTrigger(seconds=app.config['WORKER_INTERVAL']),
            id='task_processor_job',
            name='Process pending avatar data generation tasks',
            replace_existing=True
        )

        # Add image generation task processor job (supports up to 3 parallel tasks)
        def scheduled_image_processor():
            """Wrapper function to run image generation task processor with Flask app context."""
            from concurrent.futures import ThreadPoolExecutor, as_completed
            from workers.task_processor import process_image_generation

            def worker_with_context():
                """Worker function that establishes its own Flask app context."""
                with app.app_context():
                    try:
                        return process_image_generation()
                    except Exception as e:
                        logging.error(f"[SCHEDULER] Error in worker thread: {e}", exc_info=True)
                        return False

            try:
                # Process up to 3 tasks in parallel
                max_parallel_tasks = 3
                futures = []

                with ThreadPoolExecutor(max_workers=max_parallel_tasks) as executor:
                    # Submit up to 3 tasks
                    for _ in range(max_parallel_tasks):
                        future = executor.submit(worker_with_context)
                        futures.append(future)

                    # Wait for all to complete (they'll return False if no tasks available)
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logging.error(f"[SCHEDULER] Error in parallel image generation task: {e}", exc_info=True)

            except Exception as e:
                logging.error(f"[SCHEDULER] Error processing image generation tasks: {e}", exc_info=True)

        # Schedule the image generation task processor to run every WORKER_INTERVAL seconds
        scheduler.add_job(
            func=scheduled_image_processor,
            trigger=IntervalTrigger(seconds=app.config['WORKER_INTERVAL']),
            id='image_processor_job',
            name='Process image generation for completed data tasks',
            replace_existing=True
        )

        # Add stuck task recovery job (runs every 5 minutes)
        def scheduled_stuck_task_recovery():
            """Check for and recover stuck tasks."""
            with app.app_context():
                try:
                    from workers.task_processor import recover_stuck_tasks
                    recovered = recover_stuck_tasks(stuck_threshold_minutes=15)
                    if recovered > 0:
                        logging.info(f"[SCHEDULER] Recovered {recovered} stuck task(s)")
                except Exception as e:
                    logging.error(f"[SCHEDULER] Error recovering stuck tasks: {e}", exc_info=True)

        scheduler.add_job(
            func=scheduled_stuck_task_recovery,
            trigger=IntervalTrigger(minutes=5),
            id='stuck_task_recovery_job',
            name='Recover stuck tasks that have not progressed in 15+ minutes',
            replace_existing=True
        )

        # Run stuck task recovery immediately on startup (with stricter checks)
        print("[SCHEDULER] Running initial stuck task recovery check...", flush=True)
        with app.app_context():
            try:
                from workers.task_processor import recover_stuck_tasks
                # Startup recovery: check incomplete "completed" tasks AND use 0-min threshold
                recovered = recover_stuck_tasks(stuck_threshold_minutes=0, check_incomplete_completed=True)
                if recovered > 0:
                    print(f"[SCHEDULER] Startup recovery: Recovered {recovered} task(s)", flush=True)
                else:
                    print("[SCHEDULER] Startup recovery: No tasks need recovery", flush=True)
            except Exception as e:
                logging.error(f"[SCHEDULER] Error in startup recovery: {e}", exc_info=True)

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())

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
        # Language code to name mapping
        LANGUAGE_MAP = {
            # Most Common
            'en': 'English',
            'zh': 'Chinese (Mandarin)',
            'es': 'Spanish',
            'hi': 'Hindi',
            'ar': 'Arabic',
            'pt': 'Portuguese',
            'bn': 'Bengali',
            'ru': 'Russian',
            'ja': 'Japanese',
            'fr': 'French',
            'de': 'German',
            # European Languages
            'it': 'Italian',
            'pl': 'Polish',
            'uk': 'Ukrainian',
            'ro': 'Romanian',
            'nl': 'Dutch',
            'el': 'Greek',
            'cs': 'Czech',
            'sv': 'Swedish',
            'hu': 'Hungarian',
            'be': 'Belarusian',
            'bg': 'Bulgarian',
            'da': 'Danish',
            'fi': 'Finnish',
            'sk': 'Slovak',
            'no': 'Norwegian',
            'hr': 'Croatian',
            'lt': 'Lithuanian',
            'sl': 'Slovenian',
            'et': 'Estonian',
            'lv': 'Latvian',
            'is': 'Icelandic',
            'ga': 'Irish',
            'mt': 'Maltese',
            'cy': 'Welsh',
            # Asian Languages
            'ko': 'Korean',
            'vi': 'Vietnamese',
            'th': 'Thai',
            'id': 'Indonesian',
            'ms': 'Malay',
            'tl': 'Tagalog (Filipino)',
            'ur': 'Urdu',
            'pa': 'Punjabi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'mr': 'Marathi',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'si': 'Sinhala',
            'my': 'Burmese',
            'km': 'Khmer',
            'lo': 'Lao',
            'ne': 'Nepali',
            'dz': 'Dzongkha',
            'mn': 'Mongolian',
            'ug': 'Uyghur',
            'bo': 'Tibetan',
            'ka': 'Georgian',
            'hy': 'Armenian',
            'az': 'Azerbaijani',
            'kk': 'Kazakh',
            'uz': 'Uzbek',
            'tk': 'Turkmen',
            'ky': 'Kyrgyz',
            # Middle Eastern & African Languages
            'he': 'Hebrew',
            'fa': 'Persian (Farsi)',
            'tr': 'Turkish',
            'sw': 'Swahili',
            'am': 'Amharic',
            'ha': 'Hausa',
            'yo': 'Yoruba',
            'ig': 'Igbo',
            'zu': 'Zulu',
            'xh': 'Xhosa',
            'af': 'Afrikaans',
            'so': 'Somali',
            'ti': 'Tigrinya',
            'om': 'Oromo',
            'rw': 'Kinyarwanda',
            # Americas Languages
            'qu': 'Quechua',
            'gn': 'Guarani',
            'ay': 'Aymara',
            'ht': 'Haitian Creole',
            # Other Languages
            'sq': 'Albanian',
            'mk': 'Macedonian',
            'sr': 'Serbian',
            'bs': 'Bosnian',
            'eu': 'Basque',
            'ca': 'Catalan',
            'gl': 'Galician',
            'la': 'Latin',
            'eo': 'Esperanto',
            'yi': 'Yiddish',
            'lb': 'Luxembourgish',
            'fo': 'Faroese',
            'se': 'Northern Sami',
            'mi': 'Maori',
            'sm': 'Samoan',
            'to': 'Tongan'
        }

        # Extract user name from email (part before @)
        user_name = current_user.email.split('@')[0]

        if request.method == 'POST':
            # Extract form data
            persona_description = request.form.get('persona_description', '').strip()
            bio_language_code = request.form.get('bio_language', '').strip()
            number_to_generate = request.form.get('number_to_generate', '').strip()
            images_per_persona = request.form.get('images_per_persona', '').strip()

            # Convert language code to full language name
            bio_language = LANGUAGE_MAP.get(bio_language_code, bio_language_code)  # Fallback to code if not found

            # Validate required fields
            validation_errors = []

            if not persona_description:
                validation_errors.append('Persona description is required.')

            if not bio_language:
                validation_errors.append('Bio language is required.')

            if not number_to_generate:
                validation_errors.append('Number to generate is required.')
            else:
                try:
                    number_to_generate = int(number_to_generate)
                    if number_to_generate < 10 or number_to_generate > 300:
                        validation_errors.append('Number to generate must be between 10 and 300.')
                except ValueError:
                    validation_errors.append('Number to generate must be a valid number.')

            if not images_per_persona:
                validation_errors.append('Images per persona is required.')
            else:
                try:
                    images_per_persona = int(images_per_persona)
                    if images_per_persona not in [4, 8]:
                        validation_errors.append('Images per persona must be either 4 or 8.')
                except ValueError:
                    validation_errors.append('Images per persona must be a valid number.')

            # If validation errors exist, flash error and re-render form
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'error')
                return render_template('generate.html', user_name=user_name)

            # Create new generation task
            try:
                new_task = GenerationTask(
                    user_id=current_user.id,
                    persona_description=persona_description,
                    bio_language=bio_language,
                    number_to_generate=number_to_generate,
                    images_per_persona=images_per_persona
                )

                db.session.add(new_task)
                db.session.commit()

                # Flash success message with task ID
                flash(f'Avatar generation task created successfully! Task ID: {new_task.task_id}', 'success')

                # Redirect to history page to view the task
                return redirect(url_for('history'))

            except Exception as e:
                # Rollback on database error
                db.session.rollback()

                # Log error (in production, use proper logging)
                print(f"Error creating generation task: {str(e)}")

                flash('An error occurred while creating the generation task. Please try again.', 'error')
                return render_template('generate.html', user_name=user_name)

        # GET request - show generation form
        return render_template('generate.html', user_name=user_name)

    @app.route('/datasets')
    @login_required
    def datasets():
        """
        Datasets management page - lists all tasks for current user.

        Similar to /history but renders different template for dataset viewing.
        """
        user_name = current_user.email.split('@')[0]

        # Get all tasks for current user, newest first
        tasks = GenerationTask.query.filter_by(user_id=current_user.id)\
            .order_by(GenerationTask.created_at.desc())\
            .all()

        return render_template('datasets.html', user_name=user_name, tasks=tasks)

    @app.route('/datasets/<task_id>')
    @login_required
    def dataset_detail(task_id):
        """
        Dataset detail page - shows detailed view of a specific task.

        The actual data is loaded via JavaScript from /datasets/<task_id>/data API endpoint.
        This route just renders the template with the task_id.
        """
        user_name = current_user.email.split('@')[0]

        # Verify task exists and belongs to current user
        task = GenerationTask.query.filter_by(task_id=task_id, user_id=current_user.id).first()

        if not task:
            flash('Dataset not found.', 'error')
            return redirect(url_for('datasets'))

        return render_template('dataset_detail.html', user_name=user_name, task_id=task_id)

    @app.route('/history')
    @login_required
    def history():
        """Generation history page."""
        user_name = current_user.email.split('@')[0]

        # Get all tasks for current user, newest first
        tasks = GenerationTask.query.filter_by(user_id=current_user.id)\
            .order_by(GenerationTask.created_at.desc())\
            .all()

        return render_template('history.html', user_name=user_name, tasks=tasks)

    @app.route('/settings', methods=['GET'])
    @login_required
    def settings():
        """
        Settings page - display current bio prompt settings and face randomization settings.

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

        # Load face randomization settings from Config table (stored as boolean values)
        randomize_face_base = Config.get_value('randomize_face_base', False)
        randomize_face_gender_lock = Config.get_value('randomize_face_gender_lock', False)

        return render_template(
            'settings.html',
            user_name=user_name,
            bio_prompts=bio_prompts,
            randomize_face_base=randomize_face_base,
            randomize_face_gender_lock=randomize_face_gender_lock
        )

    @app.route('/settings/save', methods=['POST'])
    @login_required
    def save_settings():
        """
        Save settings endpoint (AJAX).

        POST: Save updated bio prompts and face randomization settings to database
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

            # Define expected settings keys with their types
            expected_string_keys = [
                'bio_prompt_facebook',
                'bio_prompt_instagram',
                'bio_prompt_x',
                'bio_prompt_tiktok'
            ]

            expected_boolean_keys = [
                'randomize_face_base',
                'randomize_face_gender_lock'
            ]

            # Validate that at least one expected key is present
            all_expected_keys = expected_string_keys + expected_boolean_keys
            has_valid_key = any(key in data for key in all_expected_keys)
            if not has_valid_key:
                return jsonify({
                    'success': False,
                    'error': 'No valid settings provided'
                }), 400

            # Save each setting
            saved_settings = []

            # Save string settings (bio prompts)
            for key in expected_string_keys:
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

            # Save boolean settings (face randomization) to Config table
            for key in expected_boolean_keys:
                if key in data:
                    value = data[key]

                    # Validate value type (should be boolean)
                    if not isinstance(value, bool):
                        return jsonify({
                            'success': False,
                            'error': f'Invalid value type for {key} - expected boolean'
                        }), 400

                    # Save or update config setting (value is already boolean)
                    Config.set_value(key, value)
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

    @app.route('/datasets/<task_id>/data')
    @login_required
    def dataset_detail_api(task_id):
        """
        Dataset detail API endpoint - returns JSON with task details, progress stats, and results.

        Args:
            task_id: Task ID (short UUID string)

        Query params:
            page: Page number (default: 1)
            per_page: Results per page (default: 20)

        Returns:
            JSON response with task data, progress statistics, and paginated results
        """
        # Find task by task_id string
        task = GenerationTask.query.filter_by(task_id=task_id).first()

        # Return 404 if task not found
        if not task:
            return jsonify({
                'success': False,
                'error': 'Task not found'
            }), 404

        # Verify task belongs to current user (security check)
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20

        # Get paginated results for this task
        results_query = GenerationResult.query.filter_by(task_id=task.id)\
            .order_by(GenerationResult.created_at.asc())

        pagination = results_query.paginate(page=page, per_page=per_page, error_out=False)

        # Calculate progress statistics
        total_personas = task.number_to_generate
        completed_personas = GenerationResult.query.filter_by(task_id=task.id).count()

        # Count actual images (only split images, NOT base_image)
        completed_images = 0
        results_with_images = GenerationResult.query.filter_by(task_id=task.id)\
            .filter(GenerationResult.images.isnot(None)).all()
        for result in results_with_images:
            # Count images in JSON array (base_image is for generation only, not part of dataset)
            if result.images:
                completed_images += len(result.images)

        # Calculate progress based on total work (personas + images)
        total_work_items = total_personas + (total_personas * task.images_per_persona)
        completed_work_items = completed_personas + completed_images
        progress_percentage = (completed_work_items / total_work_items * 100) if total_work_items > 0 else 0

        # Calculate time elapsed
        if task.completed_at:
            time_elapsed = (task.completed_at - task.created_at).total_seconds()
        else:
            time_elapsed = (datetime.utcnow() - task.created_at).total_seconds()

        # Format time elapsed as human-readable string
        hours, remainder = divmod(int(time_elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            time_elapsed_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            time_elapsed_str = f"{minutes}m {seconds}s"
        else:
            time_elapsed_str = f"{seconds}s"

        # Generate human-readable status message
        status_messages = {
            'pending': 'Waiting to start...',
            'generating-data': f'Generating personas... ({completed_personas}/{total_personas})',
            'generating-images': f'Generating images... ({completed_images}/{completed_personas})',
            'completed': f'Completed! Generated {completed_personas} personas with images.',
            'failed': 'Task failed. Check error log for details.'
        }
        status_message = status_messages.get(task.status, task.status)

        # Build results array (exclude base_image_url - it's for generation only)
        results_data = []
        for result in pagination.items:
            results_data.append({
                'id': result.id,
                'firstname': result.firstname,
                'lastname': result.lastname,
                'gender': result.gender,
                'bios': {
                    'facebook': result.bio_facebook,
                    'instagram': result.bio_instagram,
                    'x': result.bio_x,
                    'tiktok': result.bio_tiktok
                },
                'images': result.images or []
            })

        # Return JSON response
        return jsonify({
            'success': True,
            'task': {
                'task_id': task.task_id,
                'status': task.status,
                'persona_description': task.persona_description,
                'bio_language': task.bio_language,
                'number_to_generate': task.number_to_generate,
                'images_per_persona': task.images_per_persona,
                'created_at': task.created_at.isoformat(),
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'error_log': task.error_log
            },
            'progress': {
                'total_personas': total_personas,
                'completed_personas': completed_personas,
                'completed_images': completed_images,
                'progress_percentage': round(progress_percentage, 2),
                'time_elapsed': time_elapsed_str,
                'status_message': status_message
            },
            'results': results_data,
            'pagination': {
                'current_page': pagination.page,
                'total_pages': pagination.pages,
                'total_results': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'per_page': per_page
            }
        }), 200

    @app.route('/datasets/<task_id>/export/json')
    @login_required
    def export_json(task_id):
        """
        Export complete task data and results as JSON file.

        Args:
            task_id: Task ID (short UUID string)

        Returns:
            JSON file download
        """
        # Find task by task_id string
        task = GenerationTask.query.filter_by(task_id=task_id).first()

        # Return 404 if task not found
        if not task:
            flash('Task not found.', 'error')
            return redirect(url_for('datasets'))

        # Verify task belongs to current user
        if task.user_id != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('datasets'))

        # Get all results for this task
        results = GenerationResult.query.filter_by(task_id=task.id)\
            .order_by(GenerationResult.created_at.asc())\
            .all()

        # Build export data structure
        export_data = {
            'task': {
                'task_id': task.task_id,
                'status': task.status,
                'persona_description': task.persona_description,
                'bio_language': task.bio_language,
                'number_to_generate': task.number_to_generate,
                'images_per_persona': task.images_per_persona,
                'created_at': task.created_at.isoformat(),
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'error_log': task.error_log
            },
            'results': []
        }

        for result in results:
            export_data['results'].append({
                'id': result.id,
                'firstname': result.firstname,
                'lastname': result.lastname,
                'gender': result.gender,
                'bios': {
                    'facebook': result.bio_facebook,
                    'instagram': result.bio_instagram,
                    'x': result.bio_x,
                    'tiktok': result.bio_tiktok
                },
                'images': result.images or []
            })

        # Create JSON file in memory
        json_output = io.BytesIO()
        json_output.write(jsonify(export_data).get_data())
        json_output.seek(0)

        # Return JSON file as download
        return send_file(
            json_output,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'dataset_{task_id}.json'
        )

    @app.route('/datasets/<task_id>/export/csv')
    @login_required
    def export_csv(task_id):
        """
        Export task results as flattened CSV file.

        Args:
            task_id: Task ID (short UUID string)

        Returns:
            CSV file download
        """
        # Find task by task_id string
        task = GenerationTask.query.filter_by(task_id=task_id).first()

        # Return 404 if task not found
        if not task:
            flash('Task not found.', 'error')
            return redirect(url_for('datasets'))

        # Verify task belongs to current user
        if task.user_id != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('datasets'))

        # Get all results for this task
        results = GenerationResult.query.filter_by(task_id=task.id)\
            .order_by(GenerationResult.created_at.asc())\
            .all()

        # Create CSV in memory
        csv_output = io.StringIO()

        # Determine max number of images (up to 8)
        max_images = task.images_per_persona

        # Build CSV headers (exclude base_image_url - it's for generation only)
        headers = [
            'firstname', 'lastname', 'gender',
            'bio_facebook', 'bio_instagram', 'bio_x', 'bio_tiktok'
        ]
        # Add image columns based on images_per_persona
        for i in range(1, max_images + 1):
            headers.append(f'image_{i}')

        writer = csv.DictWriter(csv_output, fieldnames=headers)
        writer.writeheader()

        # Write each result as a row
        for result in results:
            row = {
                'firstname': result.firstname,
                'lastname': result.lastname,
                'gender': result.gender,
                'bio_facebook': result.bio_facebook or '',
                'bio_instagram': result.bio_instagram or '',
                'bio_x': result.bio_x or '',
                'bio_tiktok': result.bio_tiktok or ''
            }

            # Add image URLs
            images = result.images or []
            for i in range(1, max_images + 1):
                image_key = f'image_{i}'
                row[image_key] = images[i-1] if i <= len(images) else ''

            writer.writerow(row)

        # Prepare CSV for download
        csv_output.seek(0)
        csv_bytes = io.BytesIO()
        csv_bytes.write(csv_output.getvalue().encode('utf-8'))
        csv_bytes.seek(0)

        # Return CSV file as download
        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'dataset_{task_id}.csv'
        )

    @app.route('/datasets/<task_id>/export/zip')
    @login_required
    def export_zip(task_id):
        """
        Export complete dataset as ZIP file with images and data.json.

        Args:
            task_id: Task ID (short UUID string)

        Returns:
            ZIP file download with images folder and data.json
        """
        # Find task by task_id string
        task = GenerationTask.query.filter_by(task_id=task_id).first()

        # Return 404 if task not found
        if not task:
            flash('Task not found.', 'error')
            return redirect(url_for('datasets'))

        # Verify task belongs to current user
        if task.user_id != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('datasets'))

        # Get all results for this task
        results = GenerationResult.query.filter_by(task_id=task.id)\
            .order_by(GenerationResult.created_at.asc())\
            .all()

        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()

        try:
            import json

            # Create profiles directory
            profiles_dir = os.path.join(temp_dir, 'profiles')
            os.makedirs(profiles_dir, exist_ok=True)

            # Process each result and create individual profile folders
            for result in results:
                # Create folder name from person's name (sanitize for filesystem)
                folder_name = f"{result.firstname}_{result.lastname}".replace(' ', '_').replace('/', '_').replace('\\', '_')
                person_dir = os.path.join(profiles_dir, folder_name)
                os.makedirs(person_dir, exist_ok=True)

                # Create images subdirectory for this person
                person_images_dir = os.path.join(person_dir, 'images')
                os.makedirs(person_images_dir, exist_ok=True)

                # Build person's data
                person_data = {
                    'firstname': result.firstname,
                    'lastname': result.lastname,
                    'gender': result.gender,
                    'bios': {
                        'facebook': result.bio_facebook,
                        'instagram': result.bio_instagram,
                        'x': result.bio_x,
                        'tiktok': result.bio_tiktok
                    }
                }

                # Write details.json
                details_json_path = os.path.join(person_dir, 'details.json')
                with open(details_json_path, 'w', encoding='utf-8') as f:
                    json.dump(person_data, f, indent=2, ensure_ascii=False)

                # Write details.csv
                details_csv_path = os.path.join(person_dir, 'details.csv')
                with open(details_csv_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['field', 'value'])
                    writer.writeheader()
                    writer.writerow({'field': 'firstname', 'value': result.firstname})
                    writer.writerow({'field': 'lastname', 'value': result.lastname})
                    writer.writerow({'field': 'gender', 'value': result.gender})
                    writer.writerow({'field': 'bio_facebook', 'value': result.bio_facebook or ''})
                    writer.writerow({'field': 'bio_instagram', 'value': result.bio_instagram or ''})
                    writer.writerow({'field': 'bio_x', 'value': result.bio_x or ''})
                    writer.writerow({'field': 'bio_tiktok', 'value': result.bio_tiktok or ''})

                # Download split images for this person
                if result.images:
                    for idx, image_url in enumerate(result.images, start=1):
                        try:
                            response = requests.get(image_url, timeout=30)
                            if response.status_code == 200:
                                # Determine file extension
                                extension = '.jpg'
                                if '.' in image_url:
                                    url_ext = image_url.split('.')[-1].split('?')[0]
                                    if url_ext.lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                                        extension = f'.{url_ext.lower()}'

                                image_path = os.path.join(person_images_dir, f'{idx}{extension}')
                                with open(image_path, 'wb') as f:
                                    f.write(response.content)
                            else:
                                logging.warning(f"Failed to download image {idx} for {folder_name}: HTTP {response.status_code}")
                        except Exception as e:
                            logging.error(f"Error downloading image {idx} for {folder_name}: {e}")

            # Create ZIP file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add all profile folders with their contents
                for root, dirs, files in os.walk(profiles_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate relative path from temp_dir to maintain folder structure
                        arcname = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, arcname)

            zip_buffer.seek(0)

            # Clean up temp directory
            shutil.rmtree(temp_dir)

            # Return ZIP file as download
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'dataset_{task_id}.zip'
            )

        except Exception as e:
            # Clean up temp directory on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

            logging.error(f"Error creating ZIP export: {e}")
            flash('An error occurred while creating the ZIP export. Please try again.', 'error')
            return redirect(url_for('datasets'))

    @app.route('/api/dashboard/stats')
    @login_required
    def dashboard_stats():
        """
        Dashboard statistics API endpoint.

        Returns overview statistics and last 7 days data for current user:
        - Total tasks, personas, images
        - Completed/failed/in-progress task counts
        - Average personas per task and images per persona
        - Daily task, persona, and image counts for last 7 days

        Returns:
            JSON response with overview and last_7_days data
        """
        from sqlalchemy import func
        from datetime import timedelta

        try:
            # Calculate date range for last 7 days
            today = datetime.utcnow().date()
            seven_days_ago = today - timedelta(days=6)  # Include today = 7 days total

            # === OVERVIEW STATISTICS ===

            # Count all tasks for current user
            total_tasks = GenerationTask.query.filter_by(user_id=current_user.id).count()

            # Count tasks by status
            completed_tasks = GenerationTask.query.filter_by(
                user_id=current_user.id,
                status='completed'
            ).count()

            failed_tasks = GenerationTask.query.filter_by(
                user_id=current_user.id,
                status='failed'
            ).count()

            # Tasks in progress (any status except completed or failed)
            tasks_in_progress = GenerationTask.query.filter(
                GenerationTask.user_id == current_user.id,
                GenerationTask.status.notin_(['completed', 'failed'])
            ).count()

            # Count total personas (GenerationResult entries for user's tasks)
            total_personas = db.session.query(func.count(GenerationResult.id))\
                .join(GenerationTask, GenerationResult.task_id == GenerationTask.id)\
                .filter(GenerationTask.user_id == current_user.id)\
                .scalar() or 0

            # Count total images (sum of image array lengths)
            total_images = 0
            results_with_images = db.session.query(GenerationResult.images)\
                .join(GenerationTask, GenerationResult.task_id == GenerationTask.id)\
                .filter(
                    GenerationTask.user_id == current_user.id,
                    GenerationResult.images.isnot(None)
                ).all()

            for result in results_with_images:
                if result.images:
                    total_images += len(result.images)

            # Calculate averages
            average_personas_per_task = round(total_personas / total_tasks, 1) if total_tasks > 0 else 0.0
            average_images_per_persona = round(total_images / total_personas, 1) if total_personas > 0 else 0.0

            # === LAST 7 DAYS DATA ===

            # Generate list of all dates in range
            date_range = []
            for i in range(7):
                date = seven_days_ago + timedelta(days=i)
                date_range.append(date)

            # Query tasks by date (group by date of created_at)
            tasks_by_date_query = db.session.query(
                func.date(GenerationTask.created_at).label('date'),
                func.count(GenerationTask.id).label('count')
            ).filter(
                GenerationTask.user_id == current_user.id,
                func.date(GenerationTask.created_at) >= seven_days_ago,
                func.date(GenerationTask.created_at) <= today
            ).group_by(func.date(GenerationTask.created_at)).all()

            # Convert to dict for easy lookup
            tasks_by_date_dict = {str(row.date): row.count for row in tasks_by_date_query}

            # Query personas by date (based on task creation date)
            personas_by_date_query = db.session.query(
                func.date(GenerationTask.created_at).label('date'),
                func.count(GenerationResult.id).label('count')
            ).join(GenerationTask, GenerationResult.task_id == GenerationTask.id)\
            .filter(
                GenerationTask.user_id == current_user.id,
                func.date(GenerationTask.created_at) >= seven_days_ago,
                func.date(GenerationTask.created_at) <= today
            ).group_by(func.date(GenerationTask.created_at)).all()

            personas_by_date_dict = {str(row.date): row.count for row in personas_by_date_query}

            # For images, we need to manually count since they're in JSON arrays
            # Get all results grouped by task creation date
            results_by_date = db.session.query(
                func.date(GenerationTask.created_at).label('date'),
                GenerationResult.images
            ).join(GenerationTask, GenerationResult.task_id == GenerationTask.id)\
            .filter(
                GenerationTask.user_id == current_user.id,
                func.date(GenerationTask.created_at) >= seven_days_ago,
                func.date(GenerationTask.created_at) <= today,
                GenerationResult.images.isnot(None)
            ).all()

            # Count images by date
            images_by_date_dict = {}
            for row in results_by_date:
                date_str = str(row.date)
                image_count = len(row.images) if row.images else 0
                images_by_date_dict[date_str] = images_by_date_dict.get(date_str, 0) + image_count

            # Build response arrays with all dates filled (0 for missing dates)
            tasks_by_date = []
            personas_by_date = []
            images_by_date = []

            for date in date_range:
                date_str = str(date)
                tasks_by_date.append({
                    'date': date_str,
                    'count': tasks_by_date_dict.get(date_str, 0)
                })
                personas_by_date.append({
                    'date': date_str,
                    'count': personas_by_date_dict.get(date_str, 0)
                })
                images_by_date.append({
                    'date': date_str,
                    'count': images_by_date_dict.get(date_str, 0)
                })

            # Build response
            response_data = {
                'overview': {
                    'total_tasks': total_tasks,
                    'total_personas': total_personas,
                    'total_images': total_images,
                    'completed_tasks': completed_tasks,
                    'failed_tasks': failed_tasks,
                    'tasks_in_progress': tasks_in_progress,
                    'average_personas_per_task': average_personas_per_task,
                    'average_images_per_persona': average_images_per_persona
                },
                'last_7_days': {
                    'tasks_by_date': tasks_by_date,
                    'personas_by_date': personas_by_date,
                    'images_by_date': images_by_date
                }
            }

            return jsonify(response_data), 200

        except Exception as e:
            # Log error
            logging.error(f"Error generating dashboard stats: {e}", exc_info=True)

            return jsonify({
                'success': False,
                'error': 'An error occurred while generating dashboard statistics'
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
