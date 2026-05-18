import sys, os

# Add backend/ to Python path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_path)

# Now import
try:
    from app import create_app
    app = create_app()
except Exception as e:
    import traceback
    print("=== STARTUP ERROR ===")
    traceback.print_exc()
    print("=== END ERROR ===")
    raise