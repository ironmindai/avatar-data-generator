"""
Avatar Data Generator - Flask Application
Main application file with authentication and routing.
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import get_config
from models import db, User, Settings, Config, IntConfig, GenerationTask, GenerationResult, WorkflowLog, WorkflowNodeLog, ImageDataset, DatasetImage, DatasetPermission, DatasetImageUsage
import os
import atexit
import logging
import io
import csv
import zipfile
import requests
import tempfile
import shutil
import time
import asyncio
import json
import uuid
from datetime import datetime
from urllib.parse import urlparse, unquote
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import func
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Global lock for image regeneration (prevents concurrent regeneration of same image)
REGENERATION_LOCKS = {}

# Flickr import job tracking (in-memory storage)
flickr_import_jobs = {}
flickr_import_jobs_lock = threading.Lock()


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

        # Add data generation task processor job (supports configurable concurrent tasks)
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
                # Get max concurrent tasks from config (default: 1)
                with app.app_context():
                    max_concurrent = IntConfig.get_value('max_concurrent_tasks', default=1)

                # Count currently processing tasks
                with app.app_context():
                    processing_count = GenerationTask.query.filter(
                        GenerationTask.status.in_(['generating-data', 'generating-images'])
                    ).count()

                # Check if we have capacity to start new tasks
                available_slots = max_concurrent - processing_count

                if available_slots <= 0:
                    logging.info(f"[SCHEDULER] Max concurrent tasks ({max_concurrent}) reached. Currently processing: {processing_count}. Skipping new tasks.")
                    return

                # Process up to available_slots tasks in parallel
                # But limit to 3 max to avoid overwhelming the thread pool
                max_parallel_tasks = min(available_slots, 3)
                logging.info(f"[SCHEDULER] Available slots: {available_slots}, will process up to {max_parallel_tasks} tasks")

                futures = []

                with ThreadPoolExecutor(max_workers=max_parallel_tasks) as executor:
                    # Submit up to max_parallel_tasks
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

        # Add image generation task processor job (supports configurable concurrent tasks)
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
                # Get max concurrent tasks from config (default: 1)
                with app.app_context():
                    max_concurrent = IntConfig.get_value('max_concurrent_tasks', default=1)

                # Count currently processing tasks
                with app.app_context():
                    processing_count = GenerationTask.query.filter(
                        GenerationTask.status.in_(['generating-data', 'generating-images'])
                    ).count()

                # Check if we have capacity to start new tasks
                available_slots = max_concurrent - processing_count

                if available_slots <= 0:
                    logging.info(f"[SCHEDULER] Max concurrent tasks ({max_concurrent}) reached. Currently processing: {processing_count}. Skipping new tasks.")
                    return

                # Process up to available_slots tasks in parallel
                # But limit to 3 max to avoid overwhelming the thread pool
                max_parallel_tasks = min(available_slots, 3)
                logging.info(f"[SCHEDULER] Available slots: {available_slots}, will process up to {max_parallel_tasks} tasks")

                futures = []

                with ThreadPoolExecutor(max_workers=max_parallel_tasks) as executor:
                    # Submit up to max_parallel_tasks
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
        POST: Process avatar generation request with image-set selection
              Accepts: persona_description, bio_language, number_to_generate,
                       images_per_persona, image_set_ids[] (array)
              Validates: image-set ownership, image-set has images, all required fields
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

            # Get image_set_ids as array (can be sent as multiple params or JSON array)
            image_set_ids = request.form.getlist('image_set_ids[]')
            if not image_set_ids and request.is_json:
                image_set_ids = request.json.get('image_set_ids', [])

            # Convert to integers and filter out empty values
            try:
                image_set_ids = [int(id) for id in image_set_ids if id]
            except (ValueError, TypeError):
                image_set_ids = []

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
                    if images_per_persona < 1 or images_per_persona > 20:
                        validation_errors.append('Images per persona must be between 1 and 20.')
                except ValueError:
                    validation_errors.append('Images per persona must be a valid number.')

            # Validation: Require at least 1 image-set
            if not image_set_ids:
                validation_errors.append('At least one image set must be selected.')

            # Validation: Check all image-sets exist and belong to user
            if image_set_ids:
                valid_sets = ImageDataset.query.filter(
                    ImageDataset.id.in_(image_set_ids),
                    ImageDataset.user_id == current_user.id,
                    ImageDataset.status == 'active'
                ).all()

                if len(valid_sets) != len(image_set_ids):
                    validation_errors.append('One or more selected image sets are invalid or do not belong to you.')
                else:
                    # Validation: Check each set has at least 1 image
                    for image_set in valid_sets:
                        # Use image_set.id (INTEGER PK) not image_set.dataset_id (UUID string)
                        image_count = DatasetImage.query.filter_by(dataset_id=image_set.id).count()
                        if image_count == 0:
                            validation_errors.append(f'Image set "{image_set.name}" has no images. Please add images first.')
                            break

            # If validation errors exist, flash error and re-render form
            if validation_errors:
                # Get user's active image datasets for re-rendering
                from sqlalchemy import func

                user_image_datasets = db.session.query(
                    ImageDataset.id,
                    ImageDataset.name,
                    ImageDataset.dataset_id,
                    func.count(DatasetImage.id).label('image_count')
                ).outerjoin(
                    DatasetImage, ImageDataset.id == DatasetImage.dataset_id
                ).filter(
                    ImageDataset.user_id == current_user.id,
                    ImageDataset.status == 'active'
                ).group_by(
                    ImageDataset.id,
                    ImageDataset.name,
                    ImageDataset.dataset_id
                ).having(
                    func.count(DatasetImage.id) > 0
                ).all()

                user_name = current_user.email.split('@')[0]
                for error in validation_errors:
                    flash(error, 'error')
                return render_template('generate.html', user_name=user_name, user_image_datasets=user_image_datasets)

            # Create new generation task
            try:
                new_task = GenerationTask(
                    user_id=current_user.id,
                    persona_description=persona_description,
                    bio_language=bio_language,
                    number_to_generate=number_to_generate,
                    images_per_persona=images_per_persona,
                    image_set_ids=image_set_ids
                )

                db.session.add(new_task)
                db.session.commit()

                # Flash success message with task ID and image-set info
                flash(f'Avatar generation task created successfully! Task ID: {new_task.task_id} with {len(image_set_ids)} image set(s)', 'success')

                # Redirect to history page to view the task
                return redirect(url_for('history'))

            except Exception as e:
                # Rollback on database error
                db.session.rollback()

                # Log error
                app.logger.error(f"Error creating generation task: {str(e)}")

                # Get user's active image datasets for re-rendering
                from sqlalchemy import func

                user_image_datasets = db.session.query(
                    ImageDataset.id,
                    ImageDataset.name,
                    ImageDataset.dataset_id,
                    func.count(DatasetImage.id).label('image_count')
                ).outerjoin(
                    DatasetImage, ImageDataset.id == DatasetImage.dataset_id
                ).filter(
                    ImageDataset.user_id == current_user.id,
                    ImageDataset.status == 'active'
                ).group_by(
                    ImageDataset.id,
                    ImageDataset.name,
                    ImageDataset.dataset_id
                ).having(
                    func.count(DatasetImage.id) > 0
                ).all()

                user_name = current_user.email.split('@')[0]
                flash('An error occurred while creating the generation task. Please try again.', 'error')
                return render_template('generate.html', user_name=user_name, user_image_datasets=user_image_datasets)

        # GET request - show generation form
        # Extract user name from email
        user_name = current_user.email.split('@')[0]

        # Get user's active image datasets with image counts
        from sqlalchemy import func

        user_image_datasets = db.session.query(
            ImageDataset.id,
            ImageDataset.name,
            ImageDataset.dataset_id,
            func.count(DatasetImage.id).label('image_count')
        ).outerjoin(
            DatasetImage, ImageDataset.id == DatasetImage.dataset_id
        ).filter(
            ImageDataset.user_id == current_user.id,
            ImageDataset.status == 'active'
        ).group_by(
            ImageDataset.id,
            ImageDataset.name,
            ImageDataset.dataset_id
        ).having(
            func.count(DatasetImage.id) > 0  # Only show sets with images
        ).all()

        return render_template('generate.html', user_name=user_name, user_image_datasets=user_image_datasets)

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
        # Import degradation prompts map
        from services.style_degradation_prompts import DEGRADATION_PROMPTS_MAP

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
        crop_white_borders = Config.get_value('crop_white_borders', False)
        randomize_image_style = Config.get_value('randomize_image_style', False)
        obfuscate_exif_metadata = Config.get_value('obfuscate_exif_metadata', False)
        show_base_images = Config.get_value('show_base_images', True)

        # Load concurrency settings from IntConfig table (stored as integer values)
        max_concurrent_tasks = IntConfig.get_value('max_concurrent_tasks', 1)

        # Load degradation prompt enabled states
        degradation_states = {}
        for prompt_id in DEGRADATION_PROMPTS_MAP.keys():
            config_key = f'degradation_{prompt_id}'
            degradation_states[config_key] = Config.get_value(config_key, True)

        return render_template(
            'settings.html',
            user_name=user_name,
            bio_prompts=bio_prompts,
            randomize_face_base=randomize_face_base,
            randomize_face_gender_lock=randomize_face_gender_lock,
            crop_white_borders=crop_white_borders,
            randomize_image_style=randomize_image_style,
            obfuscate_exif_metadata=obfuscate_exif_metadata,
            show_base_images=show_base_images,
            max_concurrent_tasks=max_concurrent_tasks,
            degradation_states=degradation_states,
            degradation_prompts=DEGRADATION_PROMPTS_MAP
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
            # Import degradation prompts map for dynamic key generation
            from services.style_degradation_prompts import DEGRADATION_PROMPTS_MAP

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

            # Build boolean keys list dynamically (includes degradation prompts)
            expected_boolean_keys = [
                'randomize_face_base',
                'randomize_face_gender_lock',
                'crop_white_borders',
                'randomize_image_style',
                'obfuscate_exif_metadata',
                'show_base_images',
                # Add all degradation prompt keys dynamically
                *[f'degradation_{prompt_id}' for prompt_id in DEGRADATION_PROMPTS_MAP.keys()]
            ]

            expected_integer_keys = [
                'max_concurrent_tasks'
            ]

            # Validate that at least one expected key is present
            all_expected_keys = expected_string_keys + expected_boolean_keys + expected_integer_keys
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

            # Save integer settings (concurrency) to IntConfig table
            for key in expected_integer_keys:
                if key in data:
                    value = data[key]

                    # Validate value type (should be integer)
                    if not isinstance(value, int):
                        return jsonify({
                            'success': False,
                            'error': f'Invalid value type for {key} - expected integer'
                        }), 400

                    # Validate max_concurrent_tasks range (1-5)
                    if key == 'max_concurrent_tasks':
                        if value < 1 or value > 5:
                            return jsonify({
                                'success': False,
                                'error': 'max_concurrent_tasks must be between 1 and 5'
                            }), 400

                    # Save or update integer config setting
                    IntConfig.set_value(key, value)
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

        # Calculate ethnicity and age statistics from all results (not just current page)
        all_results = GenerationResult.query.filter_by(task_id=task.id).all()

        # Ethnicity distribution
        ethnicity_counts = {}
        for result in all_results:
            if result.ethnicity:
                ethnicity = result.ethnicity.strip()
                ethnicity_counts[ethnicity] = ethnicity_counts.get(ethnicity, 0) + 1

        # Age statistics
        ages = [result.age for result in all_results if result.age is not None]
        age_stats = {}
        if ages:
            age_stats = {
                'min': min(ages),
                'max': max(ages),
                'avg': round(sum(ages) / len(ages), 1)
            }

        # Build results array
        results_data = []
        for result in pagination.items:
            results_data.append({
                'id': result.id,
                'firstname': result.firstname,
                'lastname': result.lastname,
                'gender': result.gender,
                'base_image_url': result.base_image_url,
                'bios': {
                    'facebook': result.bio_facebook,
                    'instagram': result.bio_instagram,
                    'x': result.bio_x,
                    'tiktok': result.bio_tiktok
                },
                'supplementary': {
                    'ethnicity': result.ethnicity,
                    'age': result.age,
                    'job_title': result.job_title,
                    'workplace': result.workplace,
                    'edu_establishment': result.edu_establishment,
                    'edu_study': result.edu_study,
                    'current_city': result.current_city,
                    'current_state': result.current_state,
                    'prev_city': result.prev_city,
                    'prev_state': result.prev_state,
                    'about': result.about
                },
                'images': result.images or []
            })

        # Get show_base_images setting from Config
        show_base_images = Config.get_value('show_base_images', True)

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
                'error_log': task.error_log,
                'ethnicity_distribution': ethnicity_counts,
                'age_stats': age_stats,
                'show_base_images': show_base_images
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
                'supplementary': {
                    'ethnicity': result.ethnicity,
                    'age': result.age,
                    'job_title': result.job_title,
                    'workplace': result.workplace,
                    'edu_establishment': result.edu_establishment,
                    'edu_study': result.edu_study,
                    'current_city': result.current_city,
                    'current_state': result.current_state,
                    'prev_city': result.prev_city,
                    'prev_state': result.prev_state,
                    'about': result.about
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
            'ethnicity', 'age',
            'bio_facebook', 'bio_instagram', 'bio_x', 'bio_tiktok',
            'job_title', 'workplace',
            'edu_establishment', 'edu_study',
            'current_city', 'current_state',
            'prev_city', 'prev_state',
            'about'
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
                'ethnicity': result.ethnicity or '',
                'age': result.age if result.age is not None else '',
                'bio_facebook': result.bio_facebook or '',
                'bio_instagram': result.bio_instagram or '',
                'bio_x': result.bio_x or '',
                'bio_tiktok': result.bio_tiktok or '',
                'job_title': result.job_title or '',
                'workplace': result.workplace or '',
                'edu_establishment': result.edu_establishment or '',
                'edu_study': result.edu_study or '',
                'current_city': result.current_city or '',
                'current_state': result.current_state or '',
                'prev_city': result.prev_city or '',
                'prev_state': result.prev_state or '',
                'about': result.about or ''
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
                    },
                    'supplementary': {
                        'ethnicity': result.ethnicity,
                        'age': result.age,
                        'job_title': result.job_title,
                        'workplace': result.workplace,
                        'edu_establishment': result.edu_establishment,
                        'edu_study': result.edu_study,
                        'current_city': result.current_city,
                        'current_state': result.current_state,
                        'prev_city': result.prev_city,
                        'prev_state': result.prev_state,
                        'about': result.about
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
                    writer.writerow({'field': 'ethnicity', 'value': result.ethnicity or ''})
                    writer.writerow({'field': 'age', 'value': result.age if result.age is not None else ''})
                    writer.writerow({'field': 'bio_facebook', 'value': result.bio_facebook or ''})
                    writer.writerow({'field': 'bio_instagram', 'value': result.bio_instagram or ''})
                    writer.writerow({'field': 'bio_x', 'value': result.bio_x or ''})
                    writer.writerow({'field': 'bio_tiktok', 'value': result.bio_tiktok or ''})
                    writer.writerow({'field': 'job_title', 'value': result.job_title or ''})
                    writer.writerow({'field': 'workplace', 'value': result.workplace or ''})
                    writer.writerow({'field': 'edu_establishment', 'value': result.edu_establishment or ''})
                    writer.writerow({'field': 'edu_study', 'value': result.edu_study or ''})
                    writer.writerow({'field': 'current_city', 'value': result.current_city or ''})
                    writer.writerow({'field': 'current_state', 'value': result.current_state or ''})
                    writer.writerow({'field': 'prev_city', 'value': result.prev_city or ''})
                    writer.writerow({'field': 'prev_state', 'value': result.prev_state or ''})
                    writer.writerow({'field': 'about', 'value': result.about or ''})

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

    @app.route('/datasets/<task_id>/delete', methods=['DELETE', 'POST'])
    @login_required
    def delete_dataset(task_id):
        """
        Delete a dataset and all associated S3 files.

        Accepts both DELETE and POST methods for compatibility.
        DELETE method is preferred for RESTful API design.
        POST method allows deletion from HTML forms (which don't support DELETE).

        Args:
            task_id: Task ID (short UUID string)

        Returns:
            JSON response with success status or redirect on error
        """
        try:
            # Find task by task_id string
            task = GenerationTask.query.filter_by(task_id=task_id).first()

            # Return 404 if task not found
            if not task:
                if request.method == 'DELETE' or request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'Task not found'
                    }), 404
                else:
                    flash('Dataset not found.', 'error')
                    return redirect(url_for('datasets'))

            # Verify task belongs to current user
            if task.user_id != current_user.id:
                if request.method == 'DELETE' or request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'Access denied'
                    }), 403
                else:
                    flash('Access denied.', 'error')
                    return redirect(url_for('datasets'))

            # Get all results for this task to delete S3 files
            results = GenerationResult.query.filter_by(task_id=task.id).all()

            # Track deletion statistics
            deleted_base_images = 0
            deleted_split_images = 0
            failed_deletions = []

            # Import S3 deletion function
            from services.image_utils import delete_s3_url

            # Delete S3 files for each result
            for result in results:
                # Delete base image if exists
                if result.base_image_url:
                    try:
                        delete_s3_url(result.base_image_url)
                        deleted_base_images += 1
                        logging.info(f"Deleted base image: {result.base_image_url}")
                    except Exception as e:
                        logging.warning(f"Failed to delete base image {result.base_image_url}: {e}")
                        failed_deletions.append(result.base_image_url)

                # Delete split images if exist
                if result.images and isinstance(result.images, list):
                    for image_url in result.images:
                        try:
                            delete_s3_url(image_url)
                            deleted_split_images += 1
                            logging.info(f"Deleted split image: {image_url}")
                        except Exception as e:
                            logging.warning(f"Failed to delete split image {image_url}: {e}")
                            failed_deletions.append(image_url)

            # Delete all GenerationResult records (CASCADE will handle this automatically,
            # but we can be explicit for clarity)
            GenerationResult.query.filter_by(task_id=task.id).delete()

            # Delete the GenerationTask record
            db.session.delete(task)
            db.session.commit()

            # Log deletion summary
            logging.info(
                f"Dataset {task_id} deleted - "
                f"Base images: {deleted_base_images}, "
                f"Split images: {deleted_split_images}, "
                f"Failed deletions: {len(failed_deletions)}"
            )

            # Return appropriate response based on request type
            if request.method == 'DELETE' or request.is_json:
                response_data = {
                    'success': True,
                    'message': f'Dataset deleted successfully',
                    'deleted_base_images': deleted_base_images,
                    'deleted_split_images': deleted_split_images,
                    'total_deleted': deleted_base_images + deleted_split_images
                }

                if failed_deletions:
                    response_data['warning'] = f'{len(failed_deletions)} file(s) failed to delete from S3'
                    response_data['failed_deletions'] = failed_deletions

                return jsonify(response_data), 200
            else:
                # HTML form submission - redirect with flash message
                if failed_deletions:
                    flash(
                        f'Dataset deleted successfully. '
                        f'Warning: {len(failed_deletions)} file(s) could not be deleted from S3.',
                        'warning'
                    )
                else:
                    flash('Dataset deleted successfully.', 'success')
                return redirect(url_for('datasets'))

        except Exception as e:
            # Rollback database changes on error
            db.session.rollback()

            logging.error(f"Error deleting dataset {task_id}: {str(e)}", exc_info=True)

            if request.method == 'DELETE' or request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'An error occurred while deleting the dataset'
                }), 500
            else:
                flash('An error occurred while deleting the dataset. Please try again.', 'error')
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

    @app.route('/api/regenerate-image', methods=['POST'])
    @login_required
    def regenerate_image():
        """
        Regenerate a single image in a dataset using SeeDream img2img.

        POST: Generate a temporary preview image based on user prompt
        Returns: JSON with new temporary image URL

        Request Body:
            {
                "result_id": 123,
                "image_url": "https://s3.../image_2.png",
                "image_index": 2,
                "prompt": "user prompt for regeneration"
            }

        Returns:
            JSON: {"success": true, "new_image_url": "https://s3.../temp_regenerated.png"}
        """
        lock_key = None
        try:
            # Get JSON payload
            data = request.get_json()

            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No JSON payload provided'
                }), 400

            # Extract and validate required fields
            result_id = data.get('result_id')
            image_url = data.get('image_url')
            image_index = data.get('image_index')
            prompt = data.get('prompt')

            # Validate all fields are present
            if result_id is None:
                return jsonify({
                    'success': False,
                    'error': 'result_id is required'
                }), 400

            if image_url is None:
                return jsonify({
                    'success': False,
                    'error': 'image_url is required'
                }), 400

            if image_index is None:
                return jsonify({
                    'success': False,
                    'error': 'image_index is required'
                }), 400

            if not prompt:
                return jsonify({
                    'success': False,
                    'error': 'prompt is required'
                }), 400

            # Validate types
            if not isinstance(result_id, int):
                return jsonify({
                    'success': False,
                    'error': 'result_id must be an integer'
                }), 400

            if not isinstance(image_index, int):
                return jsonify({
                    'success': False,
                    'error': 'image_index must be an integer'
                }), 400

            if not isinstance(prompt, str):
                return jsonify({
                    'success': False,
                    'error': 'prompt must be a string'
                }), 400

            # Validate prompt length
            if len(prompt) > 2000:
                return jsonify({
                    'success': False,
                    'error': 'prompt must be 2000 characters or less'
                }), 400

            # Sanitize prompt (remove null bytes)
            prompt = prompt.replace('\x00', '')

            # Find result in database
            result = GenerationResult.query.get(result_id)

            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Result not found'
                }), 404

            # Verify ownership
            if result.task.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'error': 'Access denied'
                }), 403

            # Verify task is completed
            if result.task.status != 'completed':
                return jsonify({
                    'success': False,
                    'error': 'Task must be completed before regenerating images'
                }), 400

            # Validate image_index bounds
            if not result.images or image_index < 0 or image_index >= len(result.images):
                return jsonify({
                    'success': False,
                    'error': f'image_index must be between 0 and {len(result.images)-1 if result.images else 0}'
                }), 400

            # Concurrency control: check if this image is already being regenerated
            lock_key = (result_id, image_index)

            if lock_key in REGENERATION_LOCKS:
                lock_timestamp = REGENERATION_LOCKS[lock_key]
                # Check if lock is less than 5 minutes old
                if time.time() - lock_timestamp < 300:
                    return jsonify({
                        'success': False,
                        'error': 'This image is already being regenerated. Please wait.'
                    }), 409

            # Set lock before generation
            REGENERATION_LOCKS[lock_key] = time.time()

            # Import necessary functions
            from services.seedream_service import generate_image_with_reference
            from services.image_utils import upload_to_s3, generate_presigned_url, S3_PUBLIC_URL_BASE, S3_BUCKET_NAME

            # Extract S3 key from image_url
            # URL format: https://s3-api.dev.iron-mind.ai/avatar-images/avatars/task_101/...
            # We need to remove: base_url + '/' + bucket_name + '/'
            if not image_url.startswith(S3_PUBLIC_URL_BASE):
                return jsonify({
                    'success': False,
                    'error': 'Invalid image URL format'
                }), 400

            # Remove base URL and bucket name to get the object key
            # Example: https://s3-api.../avatar-images/avatars/... -> avatars/...
            url_without_base = image_url[len(S3_PUBLIC_URL_BASE):].lstrip('/')

            # Remove bucket name if present
            if url_without_base.startswith(S3_BUCKET_NAME + '/'):
                s3_key = url_without_base[len(S3_BUCKET_NAME) + 1:]
            else:
                s3_key = url_without_base

            logging.info(f"Extracted S3 key: {s3_key}")

            # Generate presigned URL for SeeDream to access the image
            try:
                presigned_url = generate_presigned_url(s3_key, expiration=3600)
            except Exception as e:
                logging.error(f"Error generating presigned URL: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate presigned URL for image'
                }), 500

            # Get original image dimensions by downloading it from S3
            # We need this to preserve the original size in the regeneration
            logging.info(f"Getting original image dimensions from S3")
            try:
                import httpx
                from PIL import Image
                from io import BytesIO

                # Download the original image to get its dimensions
                async def get_image_dimensions(url):
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(url)
                        response.raise_for_status()
                        img = Image.open(BytesIO(response.content))
                        return f"{img.width}x{img.height}"

                original_size = asyncio.run(get_image_dimensions(presigned_url))
                logging.info(f"Original image size: {original_size}")

            except Exception as e:
                logging.warning(f"Could not determine original image size, using default: {e}")
                original_size = None  # Will use default SEEDREAM_IMAGE_SIZE

            # Call SeeDream to generate new image with original dimensions
            logging.info(f"Regenerating image for result_id={result_id}, image_index={image_index}")
            logging.info(f"Prompt: {prompt}")
            logging.info(f"Size: {original_size or 'default (2560x1440)'}")

            try:
                image_bytes = asyncio.run(generate_image_with_reference(
                    prompt=prompt,
                    base_image_url=presigned_url,
                    size=original_size  # Preserve original dimensions
                ))
            except httpx.HTTPStatusError as e:
                logging.error(f"SeeDream HTTP error: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f'Image generation failed: HTTP {e.response.status_code}'
                }), 502
            except httpx.TimeoutException as e:
                logging.error(f"SeeDream timeout: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': 'Image generation timed out'
                }), 504
            except Exception as e:
                logging.error(f"SeeDream generation error: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f'Image generation failed: {str(e)}'
                }), 500

            # Upload to S3 with temporary name
            task_id = result.task.id
            timestamp = int(time.time())
            temp_key = f"avatars/task_{task_id}/result_{result_id}/temp_regenerated_{timestamp}.png"

            try:
                _, new_image_url = upload_to_s3(
                    image_bytes=image_bytes,
                    object_key=temp_key,
                    content_type='image/png'
                )
            except Exception as e:
                logging.error(f"S3 upload error: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': 'Failed to upload regenerated image'
                }), 500

            logging.info(f"Successfully regenerated image: {new_image_url}")

            return jsonify({
                'success': True,
                'new_image_url': new_image_url
            }), 200

        except Exception as e:
            # Log unexpected errors
            logging.error(f"Unexpected error in regenerate_image: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred'
            }), 500

        finally:
            # Always release lock
            if lock_key and lock_key in REGENERATION_LOCKS:
                del REGENERATION_LOCKS[lock_key]

    @app.route('/api/save-regenerated-image', methods=['POST'])
    @login_required
    def save_regenerated_image():
        """
        Save a regenerated image to replace the original in the dataset.

        POST: Replace the original image URL with the new regenerated image URL
        Returns: JSON with success status

        Request Body:
            {
                "result_id": 123,
                "image_index": 2,
                "new_image_url": "https://s3.../temp_regenerated.png"
            }

        Returns:
            JSON: {"success": true, "message": "Image replaced successfully"}
        """
        try:
            # Get JSON payload
            data = request.get_json()

            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No JSON payload provided'
                }), 400

            # Extract and validate required fields
            result_id = data.get('result_id')
            image_index = data.get('image_index')
            new_image_url = data.get('new_image_url')

            # Validate all fields are present
            if result_id is None:
                return jsonify({
                    'success': False,
                    'error': 'result_id is required'
                }), 400

            if image_index is None:
                return jsonify({
                    'success': False,
                    'error': 'image_index is required'
                }), 400

            if not new_image_url:
                return jsonify({
                    'success': False,
                    'error': 'new_image_url is required'
                }), 400

            # Validate types
            if not isinstance(result_id, int):
                return jsonify({
                    'success': False,
                    'error': 'result_id must be an integer'
                }), 400

            if not isinstance(image_index, int):
                return jsonify({
                    'success': False,
                    'error': 'image_index must be an integer'
                }), 400

            if not isinstance(new_image_url, str):
                return jsonify({
                    'success': False,
                    'error': 'new_image_url must be a string'
                }), 400

            # Find result in database with row-level lock
            result = GenerationResult.query.with_for_update().get(result_id)

            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Result not found'
                }), 404

            # Verify ownership
            if result.task.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'error': 'Access denied'
                }), 403

            # Verify task is completed
            if result.task.status != 'completed':
                return jsonify({
                    'success': False,
                    'error': 'Task must be completed before saving regenerated images'
                }), 400

            # Validate image_index bounds
            if not result.images or image_index < 0 or image_index >= len(result.images):
                return jsonify({
                    'success': False,
                    'error': f'image_index must be between 0 and {len(result.images)-1 if result.images else 0}'
                }), 400

            # Store old image URL for cleanup
            old_image_url = result.images[image_index]

            # Update the image URL atomically
            result.images[image_index] = new_image_url
            flag_modified(result, 'images')

            # Commit the change
            db.session.commit()

            logging.info(f"Successfully replaced image at index {image_index} for result_id={result_id}")

            # Try to delete old image from S3 (non-critical - log warning if fails)
            try:
                from services.image_utils import delete_s3_url
                delete_s3_url(old_image_url)
                logging.info(f"Successfully deleted old image: {old_image_url}")
            except Exception as e:
                logging.warning(f"Failed to delete old image {old_image_url}: {e}")

            return jsonify({
                'success': True,
                'message': 'Image replaced successfully'
            }), 200

        except Exception as e:
            # Rollback on error
            db.session.rollback()

            # Log error
            logging.error(f"Error in save_regenerated_image: {e}", exc_info=True)

            return jsonify({
                'success': False,
                'error': 'An error occurred while saving the regenerated image'
            }), 500

    @app.route('/workflow-logs')
    @login_required
    def workflow_logs():
        """
        Workflow logs page - displays all workflow execution logs with filtering and pagination.

        GET: Display workflow logs table

        Query Parameters:
            page: Page number (default: 1)
            workflow_name: Filter by workflow name (optional)
            status: Filter by status (optional)
        """
        user_name = current_user.email.split('@')[0]

        # Get query parameters
        page = request.args.get('page', 1, type=int)
        workflow_name_filter = request.args.get('workflow_name', '', type=str)
        status_filter = request.args.get('status', '', type=str)

        # Build query
        query = WorkflowLog.query

        # Apply filters
        if workflow_name_filter:
            query = query.filter(WorkflowLog.workflow_name == workflow_name_filter)

        if status_filter:
            query = query.filter(WorkflowLog.status == status_filter)

        # Order by newest first
        query = query.order_by(WorkflowLog.started_at.desc())

        # Paginate (25 per page)
        pagination = query.paginate(page=page, per_page=25, error_out=False)

        # Get unique workflow names for filter dropdown
        workflow_names = db.session.query(WorkflowLog.workflow_name)\
            .distinct()\
            .order_by(WorkflowLog.workflow_name)\
            .all()
        workflow_names = [name[0] for name in workflow_names]

        return render_template(
            'workflow_logs.html',
            user_name=user_name,
            logs=pagination.items,
            pagination=pagination,
            workflow_names=workflow_names,
            current_workflow_filter=workflow_name_filter,
            current_status_filter=status_filter
        )

    @app.route('/workflow-logs/<workflow_run_id>')
    @login_required
    def workflow_log_detail(workflow_run_id):
        """
        Workflow log detail page - displays detailed view of a specific workflow execution.

        Args:
            workflow_run_id: Workflow run UUID (full or first 8 chars)

        Returns:
            HTML page with workflow details and node execution logs
        """
        user_name = current_user.email.split('@')[0]

        # Find workflow log by workflow_run_id (support both full UUID and first 8 chars)
        workflow_log = WorkflowLog.query.filter(
            WorkflowLog.workflow_run_id.like(f"{workflow_run_id}%")
        ).first()

        if not workflow_log:
            flash('Workflow log not found.', 'error')
            return redirect(url_for('workflow_logs'))

        # Get all node logs for this workflow, ordered by node_order
        node_logs = WorkflowNodeLog.query.filter_by(workflow_log_id=workflow_log.id)\
            .order_by(WorkflowNodeLog.node_order)\
            .all()

        # Debug logging
        logging.info(f"[WORKFLOW LOG DETAIL] Workflow: {workflow_log.workflow_run_id}, Nodes: {len(node_logs)}")
        for node in node_logs:
            logging.info(
                f"  Node {node.node_order}: {node.node_name} - "
                f"system_prompt={'YES' if node.system_prompt else 'NO'}, "
                f"user_prompt={'YES' if node.user_prompt else 'NO'}, "
                f"output_data={'YES' if node.output_data else 'NO'}"
            )

        return render_template(
            'workflow_log_detail.html',
            user_name=user_name,
            workflow_log=workflow_log,
            node_logs=node_logs
        )

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

    # ========================================================================
    # IMAGE DATASETS FEATURE ROUTES
    # ========================================================================

    def _has_dataset_access(dataset, user_id, required_level='view'):
        """
        Check if user has access to a dataset.

        Args:
            dataset: ImageDataset object
            user_id: User ID to check
            required_level: 'view' or 'edit'

        Returns:
            bool: True if user has access
        """
        # Owner always has full access
        if dataset.user_id == user_id:
            return True

        # Public datasets are viewable by all
        if dataset.is_public and required_level == 'view':
            return True

        # Check for explicit permission
        permission = DatasetPermission.query.filter_by(
            dataset_id=dataset.id,
            user_id=user_id
        ).first()

        if permission:
            if required_level == 'view':
                return True  # Any permission level grants view access
            elif required_level == 'edit':
                return permission.permission_level == 'edit'

        return False

    def _get_dataset_or_404(dataset_id, user_id, required_level='view'):
        """
        Get dataset by UUID and verify user has access.

        Args:
            dataset_id: Dataset UUID string
            user_id: User ID to check access
            required_level: 'view' or 'edit'

        Returns:
            ImageDataset object

        Raises:
            404 if not found, 403 if no access
        """
        dataset = ImageDataset.query.filter_by(dataset_id=dataset_id).first()

        if not dataset:
            flash('Dataset not found.', 'error')
            return None

        if not _has_dataset_access(dataset, user_id, required_level):
            flash('You do not have permission to access this dataset.', 'error')
            return None

        return dataset

    @app.route('/image-datasets')
    @login_required
    def image_datasets():
        """List all datasets accessible to the user."""
        try:
            user_name = current_user.email.split('@')[0]

            # Query owned datasets
            owned_datasets = ImageDataset.query.filter_by(
                user_id=current_user.id,
                status='active'
            ).all()

            # Query shared datasets (via permissions)
            shared_dataset_ids = db.session.query(DatasetPermission.dataset_id).filter_by(
                user_id=current_user.id
            ).subquery()

            shared_datasets = ImageDataset.query.filter(
                ImageDataset.id.in_(shared_dataset_ids),
                ImageDataset.status == 'active'
            ).all()

            # Query public datasets (not owned by user)
            public_datasets = ImageDataset.query.filter(
                ImageDataset.is_public == True,
                ImageDataset.user_id != current_user.id,
                ImageDataset.status == 'active'
            ).all()

            # Combine and add image counts
            all_datasets = []

            for dataset in owned_datasets:
                image_count = DatasetImage.query.filter_by(dataset_id=dataset.id).count()
                dataset.is_owner = True
                dataset.permission_level = 'edit'
                all_datasets.append({
                    'dataset': dataset,
                    'image_count': image_count,
                    'access_type': 'owner'
                })

            for dataset in shared_datasets:
                image_count = DatasetImage.query.filter_by(dataset_id=dataset.id).count()
                permission = DatasetPermission.query.filter_by(
                    dataset_id=dataset.id,
                    user_id=current_user.id
                ).first()
                dataset.is_owner = False
                dataset.permission_level = permission.permission_level
                all_datasets.append({
                    'dataset': dataset,
                    'image_count': image_count,
                    'access_type': f'shared ({permission.permission_level})'
                })

            for dataset in public_datasets:
                image_count = DatasetImage.query.filter_by(dataset_id=dataset.id).count()
                dataset.is_owner = False
                dataset.permission_level = 'view'
                all_datasets.append({
                    'dataset': dataset,
                    'image_count': image_count,
                    'access_type': 'public'
                })

            logging.info(f"User {current_user.email} viewing datasets: "
                        f"{len(owned_datasets)} owned, {len(shared_datasets)} shared, "
                        f"{len(public_datasets)} public")

            return render_template(
                'image_datasets.html',
                user_name=user_name,
                datasets=all_datasets
            )

        except Exception as e:
            logging.error(f"Error loading image datasets: {e}", exc_info=True)
            logging.error(f"Error type: {type(e).__name__}")
            logging.error(f"Error details: {str(e)}")
            flash('Error loading datasets. Please try again.', 'error')
            return redirect(url_for('dashboard'))

    @app.route('/api/image-datasets', methods=['POST'])
    @login_required
    def create_dataset():
        """Create a new image dataset."""
        try:
            data = request.get_json()

            # Validate input
            name = data.get('name', '').strip()
            if not name:
                return jsonify({
                    'success': False,
                    'message': 'Dataset name is required'
                }), 400

            description = (data.get('description') or '').strip()
            is_public = data.get('is_public', False)

            # Create dataset
            dataset = ImageDataset(
                user_id=current_user.id,
                name=name,
                description=description if description else None,
                is_public=is_public,
                status='active'
            )

            db.session.add(dataset)
            db.session.commit()

            logging.info(f"User {current_user.email} created dataset: {dataset.dataset_id} ({name})")

            return jsonify({
                'success': True,
                'dataset_id': dataset.dataset_id,
                'message': 'Dataset created successfully'
            }), 201

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating dataset: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Failed to create dataset'
            }), 500

    @app.route('/image-datasets/<dataset_id>')
    @login_required
    def image_dataset_detail(dataset_id):
        """View dataset details with paginated images."""
        try:
            user_name = current_user.email.split('@')[0]

            # Get dataset and verify access
            dataset = _get_dataset_or_404(dataset_id, current_user.id, required_level='view')
            if not dataset:
                return redirect(url_for('image_datasets'))

            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = 50
            source_type_filter = request.args.get('source_type', None)

            # Build query for images
            images_query = DatasetImage.query.filter_by(dataset_id=dataset.id)

            # Apply source type filter if provided
            if source_type_filter:
                images_query = images_query.filter_by(source_type=source_type_filter)

            # Get paginated images
            images_pagination = images_query.order_by(DatasetImage.added_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            # Add usage count to each image
            for image in images_pagination.items:
                image.usage_count = DatasetImageUsage.query.filter_by(dataset_image_id=image.id).count()

            # Get total image count
            total_images = DatasetImage.query.filter_by(dataset_id=dataset.id).count()

            # Get unique source types for filter dropdown
            source_types = db.session.query(DatasetImage.source_type).filter_by(
                dataset_id=dataset.id
            ).distinct().all()
            source_types = [st[0] for st in source_types if st[0]]

            # Check if user is owner or has edit access
            is_owner = dataset.user_id == current_user.id

            # Determine permission level
            if is_owner:
                permission_level = 'edit'
            else:
                permission = DatasetPermission.query.filter_by(
                    dataset_id=dataset.id,
                    user_id=current_user.id
                ).first()
                permission_level = permission.permission_level if permission else 'view'

            logging.info(f"User {current_user.email} viewing dataset {dataset_id} "
                        f"(page {page}, filter: {source_type_filter})")

            return render_template(
                'image_dataset_detail.html',
                user_name=user_name,
                dataset=dataset,
                images=images_pagination.items,
                pagination=images_pagination,
                total_images=total_images,
                source_types=source_types,
                source_type_filter=source_type_filter,
                is_owner=is_owner,
                permission_level=permission_level
            )

        except Exception as e:
            logging.error(f"Error loading dataset detail: {e}", exc_info=True)
            flash('Error loading dataset. Please try again.', 'error')
            return redirect(url_for('image_datasets'))

    @app.route('/api/image-datasets/<dataset_id>', methods=['PUT'])
    @login_required
    def update_dataset(dataset_id):
        """Update dataset metadata."""
        try:
            # Get dataset and verify ownership
            dataset = _get_dataset_or_404(dataset_id, current_user.id, required_level='edit')
            if not dataset:
                return jsonify({
                    'success': False,
                    'message': 'Dataset not found or access denied'
                }), 403

            # Only owner can update
            if dataset.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Only the owner can update dataset settings'
                }), 403

            data = request.get_json()

            # Update fields
            if 'name' in data:
                name = data['name'].strip()
                if not name:
                    return jsonify({
                        'success': False,
                        'message': 'Dataset name cannot be empty'
                    }), 400
                dataset.name = name

            if 'description' in data:
                dataset.description = data['description'].strip() or None

            if 'is_public' in data:
                dataset.is_public = bool(data['is_public'])

            dataset.updated_at = datetime.utcnow()
            db.session.commit()

            logging.info(f"User {current_user.email} updated dataset {dataset_id}")

            return jsonify({
                'success': True,
                'message': 'Dataset updated successfully'
            }), 200

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating dataset: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Failed to update dataset'
            }), 500

    @app.route('/api/image-datasets/<dataset_id>', methods=['DELETE'])
    @login_required
    def delete_image_dataset(dataset_id):
        """Delete a dataset and all its images."""
        try:
            # Get dataset and verify ownership
            dataset = ImageDataset.query.filter_by(dataset_id=dataset_id).first()

            if not dataset:
                return jsonify({
                    'success': False,
                    'message': 'Dataset not found'
                }), 404

            # Only owner can delete
            if dataset.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Only the owner can delete this dataset'
                }), 403

            # Get all images for S3 deletion
            images = DatasetImage.query.filter_by(dataset_id=dataset.id).all()
            deleted_count = 0

            # Delete images from S3
            from services.image_utils import delete_s3_url

            for image in images:
                try:
                    delete_s3_url(image.image_url)
                    deleted_count += 1
                except Exception as e:
                    logging.warning(f"Failed to delete S3 image {image.image_url}: {e}")

            # Delete database records (CASCADE will handle images and permissions)
            db.session.delete(dataset)
            db.session.commit()

            logging.info(f"User {current_user.email} deleted dataset {dataset_id} "
                        f"({deleted_count} S3 images deleted)")

            return jsonify({
                'success': True,
                'deleted_images': deleted_count,
                'message': f'Dataset deleted successfully ({deleted_count} images removed)'
            }), 200

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting dataset: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Failed to delete dataset'
            }), 500

    @app.route('/api/image-datasets/<dataset_id>/search-flickr', methods=['POST'])
    @login_required
    def search_flickr(dataset_id):
        """Search Flickr for images with simple filtering."""
        try:
            # Get dataset and verify edit access
            dataset = _get_dataset_or_404(dataset_id, current_user.id, required_level='edit')
            if not dataset:
                return jsonify({
                    'success': False,
                    'message': 'Dataset not found or access denied'
                }), 403

            data = request.get_json()

            keyword = data.get('keyword', '').strip()
            if not keyword:
                return jsonify({
                    'success': False,
                    'message': 'Keyword is required'
                }), 400

            page = data.get('page', 1)
            per_page = min(int(data.get('per_page', 50)), 100)  # Cap at 100
            exclude_used = data.get('exclude_used', True)
            license_filter = data.get('license_filter')  # 'cc' or None
            search_mode = data.get('search_mode', 'tags')  # 'tags' or 'text'
            tag_mode = data.get('tag_mode', 'any')  # 'any' or 'all'

            # Search Flickr
            from services import flickr_service

            results = flickr_service.search_photos(
                keyword=keyword,
                per_page=per_page,
                page=page,
                exclude_used=exclude_used,
                license_filter=license_filter,
                search_mode=search_mode,
                tag_mode=tag_mode
            )

            # Format photos for response (remove internal Flickr fields)
            formatted_photos = []
            for photo in results['photos']:
                formatted_photos.append({
                    'id': photo.get('id'),
                    'url': photo.get('url_m') or photo.get('url_l') or photo.get('url_o'),
                    'url_o': photo.get('url_o'),
                    'url_l': photo.get('url_l'),
                    'url_m': photo.get('url_m'),
                    'title': photo.get('title', ''),
                    'tags': photo.get('tags', ''),
                    'owner_name': photo.get('ownername', ''),
                    'license': photo.get('license_name', 'Unknown'),
                    'date_taken': photo.get('datetaken', ''),
                    'views': photo.get('views', 0)
                })

            logging.info(f"User {current_user.email} searched Flickr in dataset {dataset_id}: "
                        f"'{keyword}' - {len(formatted_photos)} results")

            return jsonify({
                'success': True,
                'photos': formatted_photos,
                'total': results['total'],
                'page': results['page'],
                'pages': results['pages']
            }), 200

        except Exception as e:
            logging.error(f"Error searching Flickr: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'Flickr search failed: {str(e)}'
            }), 500

    @app.route('/api/proxy-image', methods=['GET'])
    @login_required
    def proxy_image():
        """
        CORS proxy for external images (Flickr thumbnails).

        Proxies image requests from allowed domains to enable canvas/WebGL access
        for face detection. Adds proper CORS headers and caching.

        Query Parameters:
            url: The URL-encoded image URL to fetch

        Returns:
            Image bytes with CORS headers, or error response

        Security:
            - Only allows Flickr domains (flickr.com, staticflickr.com)
            - Requires authentication
            - Returns 400 for invalid/disallowed domains
            - Returns 404 if image fetch fails
        """
        try:
            # Get and decode the URL parameter
            image_url = request.args.get('url')
            if not image_url:
                return jsonify({
                    'success': False,
                    'message': 'Missing url parameter'
                }), 400

            # URL might be double-encoded, decode it
            image_url = unquote(image_url)

            # Parse URL and validate domain
            parsed_url = urlparse(image_url)
            allowed_domains = ['flickr.com', 'staticflickr.com']

            # Check if domain ends with any allowed domain (supports subdomains)
            is_allowed = any(
                parsed_url.netloc == domain or parsed_url.netloc.endswith('.' + domain)
                for domain in allowed_domains
            )

            if not is_allowed:
                logging.warning(f"Proxy request denied for domain: {parsed_url.netloc}")
                return jsonify({
                    'success': False,
                    'message': f'Domain not allowed: {parsed_url.netloc}'
                }), 400

            # Fetch the image
            logging.debug(f"Proxying image from: {image_url}")
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()

            # Get content type from original response
            content_type = response.headers.get('Content-Type', 'image/jpeg')

            # Create response with image bytes
            img_response = Response(
                response.content,
                mimetype=content_type
            )

            # Add CORS headers to allow canvas/WebGL access
            img_response.headers['Access-Control-Allow-Origin'] = '*'
            img_response.headers['Access-Control-Allow-Methods'] = 'GET'
            img_response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

            # Add caching headers (1 hour cache)
            img_response.headers['Cache-Control'] = 'public, max-age=3600'

            return img_response

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch proxied image: {e}")
            return jsonify({
                'success': False,
                'message': 'Failed to fetch image'
            }), 404

        except Exception as e:
            logging.error(f"Error in image proxy: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Internal server error'
            }), 500

    def _flickr_import_background_worker(job_id, dataset_id, user_id, photos, app_instance):
        """Background worker function for Flickr import.

        Args:
            job_id: Unique job identifier
            dataset_id: Target dataset ID
            user_id: User ID for access verification
            photos: List of photo metadata from frontend
            app_instance: Flask app instance for app context
        """
        with app_instance.app_context():
            try:
                from services import flickr_service
                from services.image_utils import upload_dataset_image_to_s3, compute_image_hash

                # Update job status to processing
                with flickr_import_jobs_lock:
                    flickr_import_jobs[job_id]['status'] = 'processing'

                imported_count = 0
                failed_count = 0

                logging.info(f"[Job {job_id}] Starting Flickr import for dataset {dataset_id}: {len(photos)} photos")

                # Prepare for batch download using photo data from frontend
                photo_data_list = []
                for photo in photos:
                    try:
                        photo_id = photo.get('id')

                        if not photo_id:
                            logging.warning(f"[Job {job_id}] Photo missing ID, skipping")
                            failed_count += 1
                            continue

                        # Check if already imported
                        existing = DatasetImage.query.filter_by(
                            dataset_id=dataset_id,
                            source_type='flickr',
                            source_id=photo_id
                        ).first()

                        if existing:
                            logging.debug(f"[Job {job_id}] Photo {photo_id} already in dataset, skipping")
                            continue

                        # Use photo data directly from frontend
                        photo_data_list.append({
                            'id': photo_id,
                            'info': photo,
                            'url_o': photo.get('url_o'),
                            'url_l': photo.get('url_l'),
                            'url_m': photo.get('url_m')
                        })

                    except Exception as e:
                        logging.error(f"[Job {job_id}] Failed to prepare photo data: {e}")
                        failed_count += 1

                # Update total count
                total_to_process = len(photo_data_list)
                with flickr_import_jobs_lock:
                    flickr_import_jobs[job_id]['total'] = total_to_process

                # Helper function for parallel S3 upload processing
                def _process_flickr_image(result, dataset_id, app):
                    """Process a single Flickr download result: compute hash, upload to S3."""
                    with app.app_context():
                        try:
                            if not result['success']:
                                return False, None, result.get('error', 'Download failed')

                            photo_id = result['photo_id']
                            image_bytes = result['image_bytes']
                            metadata = result['metadata']

                            # Compute hash
                            image_hash = compute_image_hash(image_bytes)

                            # Check for duplicate hash
                            existing_hash = DatasetImage.query.filter_by(
                                dataset_id=dataset_id,
                                image_hash=image_hash
                            ).first()

                            if existing_hash:
                                return False, None, f"Duplicate hash detected for photo {photo_id}"

                            # Upload to S3
                            object_key, public_url = upload_dataset_image_to_s3(
                                image_bytes=image_bytes,
                                dataset_id=dataset_id,
                                source_id=f"flickr_{photo_id}",
                                file_extension='jpg'
                            )

                            # Prepare database record data
                            image_data = {
                                'dataset_id': dataset_id,
                                'image_url': public_url,
                                'source_type': 'flickr',
                                'source_id': photo_id,
                                'source_metadata': {
                                    'title': metadata.get('title', ''),
                                    'tags': metadata.get('tags', ''),
                                    'owner_name': metadata.get('owner_name', ''),
                                    'license': metadata.get('license', ''),
                                    'date_taken': metadata.get('date_taken', ''),
                                    'views': metadata.get('views', 0),
                                    'score': metadata.get('_score', 0)
                                },
                                'image_hash': image_hash
                            }

                            return True, image_data, None

                        except Exception as e:
                            return False, None, f"Processing error for {result.get('photo_id', 'unknown')}: {str(e)}"

                # Process in batches for progress updates
                if photo_data_list:
                    batch_size = 10
                    for batch_start in range(0, len(photo_data_list), batch_size):
                        batch_end = min(batch_start + batch_size, len(photo_data_list))
                        batch = photo_data_list[batch_start:batch_end]

                        # Download batch
                        download_results = flickr_service.batch_download_photos(
                            batch,
                            max_workers=3
                        )

                        # Process each download result in parallel
                        with ThreadPoolExecutor(max_workers=5) as executor:
                            futures = {
                                executor.submit(_process_flickr_image, result, dataset_id, app_instance): result
                                for result in download_results
                            }

                            # Collect results as they complete
                            for future in as_completed(futures):
                                try:
                                    success, image_data, error = future.result()

                                    if success:
                                        # Create database record and add to session
                                        dataset_image = DatasetImage(**image_data)
                                        db.session.add(dataset_image)
                                        imported_count += 1
                                    else:
                                        failed_count += 1
                                        if error:
                                            logging.error(f"[Job {job_id}] Failed to process image: {error}")

                                except Exception as e:
                                    failed_count += 1
                                    logging.error(f"[Job {job_id}] Error in parallel processing: {e}", exc_info=True)

                        # Commit batch
                        db.session.commit()

                        # Update progress
                        current_progress = batch_end
                        with flickr_import_jobs_lock:
                            flickr_import_jobs[job_id]['current'] = current_progress
                            flickr_import_jobs[job_id]['imported'] = imported_count
                            flickr_import_jobs[job_id]['failed'] = failed_count

                        logging.info(f"[Job {job_id}] Progress: {current_progress}/{total_to_process} processed")

                # Mark job as completed
                with flickr_import_jobs_lock:
                    flickr_import_jobs[job_id]['status'] = 'completed'
                    flickr_import_jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()
                    flickr_import_jobs[job_id]['imported'] = imported_count
                    flickr_import_jobs[job_id]['failed'] = failed_count

                logging.info(f"[Job {job_id}] Flickr import complete: {imported_count} imported, {failed_count} failed")

            except Exception as e:
                db.session.rollback()
                logging.error(f"[Job {job_id}] Error in Flickr import worker: {e}", exc_info=True)

                # Mark job as failed
                with flickr_import_jobs_lock:
                    flickr_import_jobs[job_id]['status'] = 'failed'
                    flickr_import_jobs[job_id]['error'] = str(e)
                    flickr_import_jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()

    @app.route('/api/image-datasets/<dataset_id>/import-flickr', methods=['POST'])
    @login_required
    def import_flickr(dataset_id):
        """Start async Flickr import job."""
        try:
            # Get dataset and verify edit access
            dataset = _get_dataset_or_404(dataset_id, current_user.id, required_level='edit')
            if not dataset:
                return jsonify({
                    'success': False,
                    'message': 'Dataset not found or access denied'
                }), 403

            data = request.get_json()
            photos = data.get('photos', [])

            if not photos:
                return jsonify({
                    'success': False,
                    'message': 'No photos provided'
                }), 400

            # Create unique job ID
            job_id = str(uuid.uuid4())

            # Initialize job status
            with flickr_import_jobs_lock:
                flickr_import_jobs[job_id] = {
                    'status': 'queued',
                    'current': 0,
                    'total': len(photos),
                    'imported': 0,
                    'failed': 0,
                    'started_at': datetime.utcnow().isoformat(),
                    'completed_at': None,
                    'error': None
                }

            # Start background thread
            thread = threading.Thread(
                target=_flickr_import_background_worker,
                args=(job_id, dataset.id, current_user.id, photos, current_app._get_current_object()),
                daemon=True
            )
            thread.start()

            logging.info(f"Started Flickr import job {job_id} for dataset {dataset_id} with {len(photos)} photos")

            return jsonify({
                'success': True,
                'job_id': job_id,
                'message': 'Import started'
            }), 200

        except Exception as e:
            logging.error(f"Error starting Flickr import: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'Failed to start import: {str(e)}'
            }), 500

    @app.route('/api/image-datasets/<dataset_id>/import-flickr/<job_id>/progress', methods=['GET'])
    @login_required
    def import_flickr_progress(dataset_id, job_id):
        """Get progress of Flickr import job."""
        try:
            # Verify dataset access
            dataset = _get_dataset_or_404(dataset_id, current_user.id, required_level='view')
            if not dataset:
                return jsonify({
                    'success': False,
                    'message': 'Dataset not found or access denied'
                }), 403

            # Get job status
            with flickr_import_jobs_lock:
                job_status = flickr_import_jobs.get(job_id)

            if not job_status:
                return jsonify({
                    'success': False,
                    'message': 'Job not found'
                }), 404

            # Auto-cleanup completed jobs after 5 minutes
            if job_status['status'] in ['completed', 'failed'] and job_status['completed_at']:
                completed_time = datetime.fromisoformat(job_status['completed_at'])
                if (datetime.utcnow() - completed_time).total_seconds() > 300:  # 5 minutes
                    with flickr_import_jobs_lock:
                        del flickr_import_jobs[job_id]
                    logging.info(f"Auto-cleaned up job {job_id} after 5 minutes")

            return jsonify({
                'success': True,
                'status': job_status['status'],
                'current': job_status['current'],
                'total': job_status['total'],
                'imported': job_status['imported'],
                'failed': job_status['failed'],
                'error': job_status.get('error')
            }), 200

        except Exception as e:
            logging.error(f"Error getting Flickr import progress: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'Failed to get progress: {str(e)}'
            }), 500

    @app.route('/api/image-datasets/<dataset_id>/import-urls', methods=['POST'])
    @login_required
    def import_urls(dataset_id):
        """Import images from external URLs."""
        try:
            # Get dataset and verify edit access
            dataset = _get_dataset_or_404(dataset_id, current_user.id, required_level='edit')
            if not dataset:
                return jsonify({
                    'success': False,
                    'message': 'Dataset not found or access denied'
                }), 403

            data = request.get_json()
            urls = data.get('urls', [])

            if not urls:
                return jsonify({
                    'success': False,
                    'message': 'No URLs provided'
                }), 400

            # Import using url_import_service
            from services import url_import_service

            result = url_import_service.batch_import_urls(
                urls=urls,
                dataset_id=dataset.id,
                app=current_app._get_current_object(),
                max_workers=5
            )

            logging.info(f"User {current_user.email} imported URLs to dataset {dataset_id}: "
                        f"{result['imported']} imported, {result['failed']} failed")

            return jsonify({
                'success': True,
                'imported_count': result['imported'],
                'failed_count': result['failed'],
                'failed_urls': result.get('failed_urls', []),
                'message': f"Import complete: {result['imported']} imported, {result['failed']} failed"
            }), 200

        except Exception as e:
            logging.error(f"Error importing URLs: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'Import failed: {str(e)}'
            }), 500

    @app.route('/api/image-datasets/<dataset_id>/images/<int:image_id>', methods=['DELETE'])
    @login_required
    def delete_dataset_image(dataset_id, image_id):
        """Remove an image from a dataset."""
        try:
            # Get dataset and verify edit access
            dataset = _get_dataset_or_404(dataset_id, current_user.id, required_level='edit')
            if not dataset:
                return jsonify({
                    'success': False,
                    'message': 'Dataset not found or access denied'
                }), 403

            # Get image
            image = DatasetImage.query.filter_by(
                id=image_id,
                dataset_id=dataset.id
            ).first()

            if not image:
                return jsonify({
                    'success': False,
                    'message': 'Image not found'
                }), 404

            # Delete from S3
            from services.image_utils import delete_s3_url

            try:
                delete_s3_url(image.image_url)
            except Exception as e:
                logging.warning(f"Failed to delete S3 image {image.image_url}: {e}")

            # Delete from database
            db.session.delete(image)
            db.session.commit()

            logging.info(f"User {current_user.email} deleted image {image_id} from dataset {dataset_id}")

            return jsonify({
                'success': True,
                'message': 'Image deleted successfully'
            }), 200

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting image: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Failed to delete image'
            }), 500

    @app.route('/api/image-datasets/<dataset_id>/permissions', methods=['GET'])
    @login_required
    def get_permissions(dataset_id):
        """Get list of users with access to dataset."""
        try:
            # Get dataset and verify ownership
            dataset = ImageDataset.query.filter_by(dataset_id=dataset_id).first()

            if not dataset:
                return jsonify({
                    'success': False,
                    'message': 'Dataset not found'
                }), 404

            # Only owner can view permissions
            if dataset.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Only the owner can view permissions'
                }), 403

            # Get permissions with user data
            permissions = db.session.query(
                DatasetPermission, User
            ).join(
                User, DatasetPermission.user_id == User.id
            ).filter(
                DatasetPermission.dataset_id == dataset.id
            ).all()

            permissions_list = []
            for permission, user in permissions:
                permissions_list.append({
                    'user_id': user.id,
                    'email': user.email,
                    'permission_level': permission.permission_level,
                    'created_at': permission.created_at.isoformat()
                })

            return jsonify({
                'success': True,
                'permissions': permissions_list
            }), 200

        except Exception as e:
            logging.error(f"Error getting permissions: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Failed to get permissions'
            }), 500

    @app.route('/api/image-datasets/<dataset_id>/permissions', methods=['POST'])
    @login_required
    def grant_permission(dataset_id):
        """Grant access to a user."""
        try:
            # Get dataset and verify ownership
            dataset = ImageDataset.query.filter_by(dataset_id=dataset_id).first()

            if not dataset:
                return jsonify({
                    'success': False,
                    'message': 'Dataset not found'
                }), 404

            # Only owner can grant permissions
            if dataset.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Only the owner can grant permissions'
                }), 403

            data = request.get_json()

            user_email = data.get('user_email', '').strip()
            permission_level = data.get('permission_level', 'view')

            if not user_email:
                return jsonify({
                    'success': False,
                    'message': 'User email is required'
                }), 400

            if permission_level not in ['view', 'edit']:
                return jsonify({
                    'success': False,
                    'message': 'Permission level must be "view" or "edit"'
                }), 400

            # Look up user
            user = User.query.filter_by(email=user_email).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': f'User not found: {user_email}'
                }), 404

            # Don't allow granting permission to self
            if user.id == current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Cannot grant permission to yourself'
                }), 400

            # Check if permission already exists
            existing = DatasetPermission.query.filter_by(
                dataset_id=dataset.id,
                user_id=user.id
            ).first()

            if existing:
                # Update existing permission
                existing.permission_level = permission_level
                message = f'Updated permission for {user_email} to {permission_level}'
            else:
                # Create new permission
                permission = DatasetPermission(
                    dataset_id=dataset.id,
                    user_id=user.id,
                    permission_level=permission_level
                )
                db.session.add(permission)
                message = f'Granted {permission_level} access to {user_email}'

            db.session.commit()

            logging.info(f"User {current_user.email} granted {permission_level} permission "
                        f"to {user_email} for dataset {dataset_id}")

            return jsonify({
                'success': True,
                'message': message
            }), 200

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error granting permission: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Failed to grant permission'
            }), 500

    @app.route('/api/image-datasets/<dataset_id>/permissions/<int:user_id>', methods=['DELETE'])
    @login_required
    def revoke_permission(dataset_id, user_id):
        """Revoke a user's access to dataset."""
        try:
            # Get dataset and verify ownership
            dataset = ImageDataset.query.filter_by(dataset_id=dataset_id).first()

            if not dataset:
                return jsonify({
                    'success': False,
                    'message': 'Dataset not found'
                }), 404

            # Only owner can revoke permissions
            if dataset.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Only the owner can revoke permissions'
                }), 403

            # Get permission
            permission = DatasetPermission.query.filter_by(
                dataset_id=dataset.id,
                user_id=user_id
            ).first()

            if not permission:
                return jsonify({
                    'success': False,
                    'message': 'Permission not found'
                }), 404

            # Delete permission
            db.session.delete(permission)
            db.session.commit()

            logging.info(f"User {current_user.email} revoked permission for user {user_id} "
                        f"from dataset {dataset_id}")

            return jsonify({
                'success': True,
                'message': 'Permission revoked successfully'
            }), 200

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error revoking permission: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Failed to revoke permission'
            }), 500

    @app.route('/api/image-datasets/<dataset_id>/export/json')
    @login_required
    def export_image_dataset_json(dataset_id):
        """Export dataset as JSON."""
        try:
            # Get dataset and verify access
            dataset = _get_dataset_or_404(dataset_id, current_user.id, required_level='view')
            if not dataset:
                flash('Dataset not found or access denied.', 'error')
                return redirect(url_for('image_datasets'))

            # Get all images
            images = DatasetImage.query.filter_by(dataset_id=dataset.id).all()

            # Build export data
            export_data = {
                'dataset': {
                    'dataset_id': dataset.dataset_id,
                    'name': dataset.name,
                    'description': dataset.description,
                    'is_public': dataset.is_public,
                    'created_at': dataset.created_at.isoformat(),
                    'updated_at': dataset.updated_at.isoformat(),
                    'image_count': len(images)
                },
                'images': []
            }

            for image in images:
                export_data['images'].append({
                    'image_url': image.image_url,
                    'source_type': image.source_type,
                    'source_id': image.source_id,
                    'source_metadata': image.source_metadata,
                    'image_hash': image.image_hash,
                    'added_at': image.added_at.isoformat()
                })

            # Create JSON response
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)

            # Create filename
            filename = f"{dataset.name.replace(' ', '_')}_export.json"

            logging.info(f"User {current_user.email} exported dataset {dataset_id} as JSON")

            # Return as downloadable file
            return Response(
                json_str,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )

        except Exception as e:
            logging.error(f"Error exporting JSON: {e}", exc_info=True)
            flash('Failed to export dataset.', 'error')
            return redirect(url_for('image_dataset_detail', dataset_id=dataset_id))

    @app.route('/api/image-datasets/<dataset_id>/export/zip')
    @login_required
    def export_image_dataset_zip(dataset_id):
        """Export dataset as ZIP with images and metadata."""
        try:
            # Get dataset and verify access
            dataset = _get_dataset_or_404(dataset_id, current_user.id, required_level='view')
            if not dataset:
                flash('Dataset not found or access denied.', 'error')
                return redirect(url_for('image_datasets'))

            # Get all images
            images = DatasetImage.query.filter_by(dataset_id=dataset.id).all()

            if not images:
                flash('Dataset has no images to export.', 'error')
                return redirect(url_for('image_dataset_detail', dataset_id=dataset_id))

            # Create temporary directory for download
            temp_dir = tempfile.mkdtemp(prefix='dataset_export_')

            try:
                # Create images subdirectory
                images_dir = os.path.join(temp_dir, 'images')
                os.makedirs(images_dir)

                # Build metadata
                export_data = {
                    'dataset': {
                        'dataset_id': dataset.dataset_id,
                        'name': dataset.name,
                        'description': dataset.description,
                        'is_public': dataset.is_public,
                        'created_at': dataset.created_at.isoformat(),
                        'updated_at': dataset.updated_at.isoformat(),
                        'image_count': len(images)
                    },
                    'images': []
                }

                # Download images
                for idx, image in enumerate(images):
                    try:
                        # Determine file extension from URL
                        url_parts = image.image_url.split('.')
                        ext = url_parts[-1] if len(url_parts) > 1 else 'jpg'

                        # Create filename
                        image_filename = f"image_{idx:04d}.{ext}"
                        image_path = os.path.join(images_dir, image_filename)

                        # Download image
                        response = requests.get(image.image_url, timeout=30)
                        response.raise_for_status()

                        # Save to file
                        with open(image_path, 'wb') as f:
                            f.write(response.content)

                        # Add to metadata
                        export_data['images'].append({
                            'filename': image_filename,
                            'original_url': image.image_url,
                            'source_type': image.source_type,
                            'source_id': image.source_id,
                            'source_metadata': image.source_metadata,
                            'image_hash': image.image_hash,
                            'added_at': image.added_at.isoformat()
                        })

                    except Exception as e:
                        logging.warning(f"Failed to download image {image.image_url}: {e}")
                        continue

                # Write metadata JSON
                metadata_path = os.path.join(temp_dir, 'data.json')
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

                # Create ZIP file
                zip_path = os.path.join(temp_dir, 'export.zip')
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add metadata
                    zipf.write(metadata_path, 'data.json')

                    # Add images
                    for root, dirs, files in os.walk(images_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join('images', file)
                            zipf.write(file_path, arcname)

                # Create filename
                filename = f"{dataset.name.replace(' ', '_')}_export.zip"

                logging.info(f"User {current_user.email} exported dataset {dataset_id} as ZIP "
                            f"({len(export_data['images'])} images)")

                # Send file and clean up after
                return send_file(
                    zip_path,
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name=filename
                )

            finally:
                # Clean up temporary directory after a delay
                # (Flask will serve the file first)
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logging.warning(f"Failed to clean up temp directory {temp_dir}: {e}")

        except Exception as e:
            logging.error(f"Error exporting ZIP: {e}", exc_info=True)
            flash('Failed to export dataset.', 'error')
            return redirect(url_for('image_dataset_detail', dataset_id=dataset_id))

    # ========================================================================
    # END IMAGE DATASETS FEATURE ROUTES
    # ========================================================================

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
