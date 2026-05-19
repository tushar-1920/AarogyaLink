import sys, os, traceback

print("=== SERVER.PY STARTING ===", flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"Working dir: {os.getcwd()}", flush=True)
print(f"Files: {os.listdir('.')}", flush=True)

try:
    backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    print(f"Backend path: {backend_path}", flush=True)
    print(f"Backend files: {os.listdir(backend_path)}", flush=True)
    sys.path.insert(0, backend_path)
    
    print("Importing create_app...", flush=True)
    from app import create_app
    
    print("Creating app...", flush=True)
    app = create_app()
    
    print("=== APP CREATED SUCCESSFULLY ===", flush=True)

except Exception as e:
    print(f"=== FATAL ERROR: {e} ===", flush=True)
    traceback.print_exc()
    sys.exit(1)