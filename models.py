"""
Database models for Avatar Data Generator application.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt
import uuid

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    User model for authentication and user management.

    Attributes:
        id: Primary key
        email: Unique email address for login
        password_hash: Bcrypt hashed password
        created_at: Timestamp of user creation
        last_login: Timestamp of last successful login
        is_active: Boolean flag for account status
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password: str) -> None:
        """
        Hash and set the user's password using bcrypt.

        Args:
            password: Plain text password to hash
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    def update_last_login(self) -> None:
        """Update the last_login timestamp to current time."""
        self.last_login = datetime.utcnow()

    def get_id(self) -> str:
        """
        Return the user ID as a string (required by Flask-Login).

        Returns:
            User ID as string
        """
        return str(self.id)

    @property
    def is_authenticated(self) -> bool:
        """Return True if user is authenticated."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Return False as this is not an anonymous user."""
        return False


class Settings(db.Model):
    """
    Settings model for storing application configuration.

    Attributes:
        id: Primary key
        key: Unique setting key
        value: Setting value (stored as text)
        created_at: Timestamp of setting creation
        updated_at: Timestamp of last update
    """
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.text('NOW()'))
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.text('NOW()'), onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Settings {self.key}>'

    @classmethod
    def get_value(cls, key: str, default: str = None) -> str:
        """
        Get a setting value by key.

        Args:
            key: Setting key to retrieve
            default: Default value if setting doesn't exist

        Returns:
            Setting value or default
        """
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default

    @classmethod
    def set_value(cls, key: str, value: str) -> 'Settings':
        """
        Set a setting value by key. Creates if doesn't exist, updates if exists.

        Args:
            key: Setting key
            value: Setting value

        Returns:
            Settings object
        """
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = cls(key=key, value=value)
            db.session.add(setting)
        return setting


class Config(db.Model):
    """
    Config model for storing global boolean configuration settings.

    Attributes:
        id: Primary key
        key: Unique config key
        value: Boolean config value (TRUE/FALSE)
        created_at: Timestamp of config creation
        updated_at: Timestamp of last update
    """
    __tablename__ = 'config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    value = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.text('NOW()'))
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.text('NOW()'), onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Config {self.key}={self.value}>'

    @classmethod
    def get_value(cls, key: str, default: bool = False) -> bool:
        """
        Get a boolean config value by key.

        Args:
            key: Config key to retrieve
            default: Default value if config doesn't exist

        Returns:
            Boolean config value or default
        """
        config = cls.query.filter_by(key=key).first()
        return config.value if config else default

    @classmethod
    def set_value(cls, key: str, value: bool) -> 'Config':
        """
        Set a boolean config value by key. Creates if doesn't exist, updates if exists.

        Args:
            key: Config key
            value: Boolean config value

        Returns:
            Config object
        """
        config = cls.query.filter_by(key=key).first()
        if config:
            config.value = value
            config.updated_at = datetime.utcnow()
        else:
            config = cls(key=key, value=value)
            db.session.add(config)
        return config


class IntConfig(db.Model):
    """
    IntConfig model for storing global integer configuration settings.

    Attributes:
        id: Primary key
        key: Unique config key
        value: Integer config value
        created_at: Timestamp of config creation
        updated_at: Timestamp of last update
    """
    __tablename__ = 'int_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    value = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.text('NOW()'))
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.text('NOW()'), onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<IntConfig {self.key}={self.value}>'

    @classmethod
    def get_value(cls, key: str, default: int = 1) -> int:
        """
        Get an integer config value by key.

        Args:
            key: Config key to retrieve
            default: Default value if config doesn't exist

        Returns:
            Integer config value or default
        """
        config = cls.query.filter_by(key=key).first()
        return config.value if config else default

    @classmethod
    def set_value(cls, key: str, value: int) -> 'IntConfig':
        """
        Set an integer config value by key. Creates if doesn't exist, updates if exists.

        Args:
            key: Config key
            value: Integer config value

        Returns:
            IntConfig object
        """
        config = cls.query.filter_by(key=key).first()
        if config:
            config.value = value
            config.updated_at = datetime.utcnow()
        else:
            config = cls(key=key, value=value)
            db.session.add(config)
        return config


class GenerationTask(db.Model):
    """
    GenerationTask model for tracking avatar generation requests.

    Attributes:
        id: Primary key
        task_id: Short UUID for user-facing task identification (8-12 chars)
        user_id: Foreign key to users table
        persona_description: The persona description from form
        bio_language: Selected language for bios
        number_to_generate: Number of avatars to generate
        images_per_persona: Images per persona (4 or 8)
        status: Task status (pending, generating-data, generating-images, completed, failed)
        error_log: Error messages if task fails
        created_at: Timestamp of task creation
        updated_at: Timestamp of last update
        completed_at: Timestamp of task completion
    """
    __tablename__ = 'generation_tasks'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(12), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    persona_description = db.Column(db.Text, nullable=False)
    bio_language = db.Column(db.String(100), nullable=False)
    number_to_generate = db.Column(db.Integer, nullable=False)
    images_per_persona = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)
    error_log = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationship to User
    user = db.relationship('User', backref=db.backref('generation_tasks', lazy='dynamic'))

    def __init__(self, **kwargs):
        """Initialize GenerationTask with auto-generated task_id if not provided."""
        if 'task_id' not in kwargs:
            kwargs['task_id'] = self.generate_task_id()
        super(GenerationTask, self).__init__(**kwargs)

    def __repr__(self):
        return f'<GenerationTask {self.task_id} status={self.status}>'

    @staticmethod
    def generate_task_id() -> str:
        """
        Generate a short, unique task ID using UUID4.

        Returns:
            8-character alphanumeric task ID
        """
        return str(uuid.uuid4())[:8]

    def mark_completed(self, success: bool = True, error_message: str = None) -> None:
        """
        Mark task as completed or failed.

        Args:
            success: True if completed successfully, False if failed
            error_message: Error message if task failed
        """
        self.status = 'completed' if success else 'failed'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if error_message:
            self.error_log = error_message

    def update_status(self, new_status: str) -> None:
        """
        Update task status.

        Args:
            new_status: New status value
        """
        self.status = new_status
        self.updated_at = datetime.utcnow()

    @property
    def personas_generated(self) -> int:
        """
        Get the count of personas generated for this task.

        Returns:
            Number of GenerationResult entries for this task
        """
        from models import GenerationResult
        return GenerationResult.query.filter_by(task_id=self.id).count()

    @property
    def images_generated(self) -> int:
        """
        Get the total count of images generated for this task.

        Returns:
            Total number of split images (base_image excluded - it's for generation only)
        """
        from models import GenerationResult

        total_images = 0
        results_with_images = GenerationResult.query.filter_by(task_id=self.id)\
            .filter(GenerationResult.images.isnot(None)).all()

        for result in results_with_images:
            # Count only split images (base_image is for generation, not part of dataset)
            if result.images:
                total_images += len(result.images)

        return total_images


class GenerationResult(db.Model):
    """
    GenerationResult model for storing persona data generated from Flowise.

    Attributes:
        id: Primary key
        task_id: Foreign key to generation_tasks table (references id, not task_id string)
        batch_number: Which batch this result came from (for tracking parallel requests)
        firstname: Generated first name
        lastname: Generated last name
        gender: Gender (f/m)
        bio_facebook: Facebook bio text
        bio_instagram: Instagram bio text
        bio_x: X (Twitter) bio text
        bio_tiktok: TikTok bio text
        job_title: Job title/occupation
        workplace: Workplace/company name
        edu_establishment: Educational establishment name
        edu_study: Field of study/degree
        current_city: Current city of residence
        current_state: Current state of residence
        prev_city: Previous city of residence
        prev_state: Previous state of residence
        about: About/bio text
        base_image_url: Public S3 URL for base selfie image
        images: JSONB array of public S3 URLs for split images (flexible array: 4, 8, or any number)
        created_at: Timestamp of result creation
    """
    __tablename__ = 'generation_results'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('generation_tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    batch_number = db.Column(db.Integer, nullable=False, index=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    bio_facebook = db.Column(db.Text, nullable=True)
    bio_instagram = db.Column(db.Text, nullable=True)
    bio_x = db.Column(db.Text, nullable=True)
    bio_tiktok = db.Column(db.Text, nullable=True)
    job_title = db.Column(db.Text, nullable=True)
    workplace = db.Column(db.Text, nullable=True)
    edu_establishment = db.Column(db.Text, nullable=True)
    edu_study = db.Column(db.Text, nullable=True)
    current_city = db.Column(db.String(255), nullable=True)
    current_state = db.Column(db.String(255), nullable=True)
    prev_city = db.Column(db.String(255), nullable=True)
    prev_state = db.Column(db.String(255), nullable=True)
    about = db.Column(db.Text, nullable=True)
    base_image_url = db.Column(db.Text, nullable=True)
    images = db.Column(db.JSON, nullable=True)  # JSONB array of image URLs
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.text('NOW()'))

    # Relationship to GenerationTask
    task = db.relationship('GenerationTask', backref=db.backref('results', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        job_info = f' ({self.job_title})' if self.job_title else ''
        location_info = f' in {self.current_city}, {self.current_state}' if self.current_city and self.current_state else ''
        return f'<GenerationResult {self.firstname} {self.lastname}{job_info}{location_info} task_id={self.task_id} batch={self.batch_number}>'
