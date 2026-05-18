import os
from dotenv import load_dotenv

load_dotenv()

# Base directory = backend/
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
# Root directory = one level up from backend/
ROOT_DIR  = os.path.dirname(BASE_DIR)

class Config:
    # ── Security ──────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'aarogyalink-super-secret-2025-change-me')

    # ── Database ───────────────────────────────────────────────
    # Render sets DATABASE_URL for PostgreSQL; fallback to SQLite locally
    _db_url = os.environ.get('DATABASE_URL', '')
    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _db_url or \
        f"sqlite:///{os.path.join(ROOT_DIR, 'database', 'aarogyalink.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle':  300,
    }

    # ── Folders ────────────────────────────────────────────────
    TEMPLATE_FOLDER = os.path.join(ROOT_DIR, 'frontend', 'templates')
    STATIC_FOLDER   = os.path.join(ROOT_DIR, 'frontend', 'static')
    QR_OUTPUT_DIR   = os.path.join(ROOT_DIR, 'frontend', 'static', 'qrcodes')
    CARD_OUTPUT_DIR = os.path.join(ROOT_DIR, 'frontend', 'static', 'cards')

    # ── Upload settings ────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB max upload
    UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'frontend', 'static', 'uploads')

    # ── Production flag ────────────────────────────────────────
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False