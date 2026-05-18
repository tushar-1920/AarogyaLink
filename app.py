"""
Root-level app.py — Render's default gunicorn command 'gunicorn app:app' finds this.
It simply adds backend/ to the path and imports the real app.
"""
import sys, os

# Add backend/ to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)