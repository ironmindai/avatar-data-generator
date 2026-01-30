"""
Database models for Avatar Data Generator application.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt

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
