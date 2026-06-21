import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── Core ──────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smartvax-secret-key-change-in-production!'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Prefer DATABASE_URL env var; default to SQLite
    _db_url = os.environ.get('DATABASE_URL', '')
    if _db_url.startswith('postgres://'):
        # Render/Railway fix: psycopg2 requires postgresql://
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url or 'sqlite:///' + os.path.join(BASE_DIR, 'smartvax.db')

    # ── Session ───────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set True in production (HTTPS)

    # ── Email (Flask-Mail) ────────────────────────────────
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get(
        'MAIL_DEFAULT_SENDER',
        f'SmartVax <{os.environ.get("MAIL_USERNAME", "noreply@smartvax.com")}>'
    )
    MAIL_SUPPRESS_SEND = not bool(os.environ.get('MAIL_USERNAME', ''))  # suppress if no creds

    # ── CSRF ─────────────────────────────────────────────
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    WTF_CSRF_SSL_STRICT = False

    # ── Rate Limiting ─────────────────────────────────────
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    # ── APScheduler ───────────────────────────────────────
    SCHEDULER_API_ENABLED = False
    SCHEDULER_TIMEZONE = 'Asia/Kolkata'


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False   # Set True to log SQL queries


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True   # Requires HTTPS
    WTF_CSRF_SSL_STRICT = True

    # Use a strong secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or (_ for _ in ()).throw(
        ValueError("SECRET_KEY environment variable MUST be set in production!")
    )


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
