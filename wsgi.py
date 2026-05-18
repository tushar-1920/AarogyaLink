import sys, os

# Add backend/ to Python path so 'app', 'models', 'config' etc. are importable
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)