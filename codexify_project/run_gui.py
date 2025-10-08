import time
from codexify.engine import CodexifyEngine
from codexify.events import PROJECT_LOADED, FILES_UPDATED
from codexify.clients.gui.main_window import MainWindow
from codexify.utils.logger import get_logger

# Initialize logger
logger = get_logger("run_gui")

def handle_project_loaded(data=None):
    """Callback function for the PROJECT_LOADED event."""
    # Note: engine is now properly accessible through the MainWindow instance
    logger.info("GUI_Client: Received event PROJECT_LOADED")

def handle_files_updated(data=None):
    """Callback function for the FILES_UPDATED event."""
    # Note: engine is now properly accessible through the MainWindow instance
    logger.info("GUI_Client: Received event FILES_UPDATED")

def main():
    """
    Initializes and runs the main GUI window for the application.
    """
    try:
        logger.info("Starting Codexify GUI application")
        app = MainWindow()
        app.run()
    except Exception as e:
        logger.exception("Failed to start GUI application: %s", e)
        raise

if __name__ == "__main__":
    main()
