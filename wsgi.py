"""
Render / Gunicorn entry point.
This file lives at the project root.
"""
import sys, os

# Make sure backend/ is on the path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)