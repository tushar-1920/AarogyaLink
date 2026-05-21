import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'aarogyalink-secret-2025')

    # Database - use /tmp on Render (always writable), local database/ folder otherwise
    _db_url = os.environ.get('DATABASE_URL', '')
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    # Always use /tmp for SQLite - works on Render and locally
    SQLALCHEMY_DATABASE_URI = (
        _db_url or "sqlite:////tmp/aarogyalink.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TEMPLATE_FOLDER = os.path.join(ROOT_DIR, 'frontend', 'templates')
    STATIC_FOLDER   = os.path.join(ROOT_DIR, 'frontend', 'static')
    QR_OUTPUT_DIR   = os.path.join(ROOT_DIR, 'frontend', 'static', 'qrcodes')
    CARD_OUTPUT_DIR = os.path.join(ROOT_DIR, 'frontend', 'static', 'cards')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'frontend', 'static', 'uploads')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False