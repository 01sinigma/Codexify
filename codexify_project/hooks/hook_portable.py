import os, sys

def ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass

if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(app_dir)
ensure_dir(os.path.join(app_dir, 'logs'))
ensure_dir(os.path.join(app_dir, 'presets'))
ensure_dir(os.path.join(app_dir, 'templates'))

os.environ.setdefault('CODEXIFY_PORTABLE', '1')
os.environ.setdefault('CODEXIFY_BASE_DIR', app_dir)
