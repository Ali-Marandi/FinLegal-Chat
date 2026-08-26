"""
FinLegal-Chat Ultimate v5.0.0
Commercial-Grade AI-Powered Legal & Financial Intelligence Platform

Entry point for the desktop application.
"""

import sys
import os
import logging

# Configure logging before anything else
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("FinLegal")

# Add the application root to the Python path
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)


def main():
    import flet as ft
    from src.ui.app import FinLegalApp

    logger.info("Starting FinLegal-Chat Ultimate v5.0.0...")

    def app_entry(page: ft.Page):
        """Flet application entry point."""
        # Prevent the default right-click context menu on Windows
        page.on_keyboard_event = lambda e: None
        FinLegalApp(page)

    ft.app(
        target=app_entry,
        name="FinLegal-Chat Ultimate",
    )


if __name__ == "__main__":
    main()
