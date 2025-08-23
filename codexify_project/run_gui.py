import time
from codexify.engine import CodexifyEngine
from codexify.events import PROJECT_LOADED, FILES_UPDATED
from codexify.clients.gui.main_window import MainWindow

def handle_project_loaded(data=None):
    """Callback function for the PROJECT_LOADED event."""
    print(f"GUI_Client: Received event PROJECT_LOADED. Project path is: {engine.state.project_path}")

def handle_files_updated(data=None):
    """Callback function for the FILES_UPDATED event."""
    print(f"GUI_Client: Received event FILES_UPDATED. {len(engine.state.include_files)} files to include.")

def main():
    """
    Initializes and runs the main GUI window for the application.
    """
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()
