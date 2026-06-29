"""
NESAUDIO - Main entry point
"""

import sys
import logging
from pathlib import Path
from .ui.app import NESAudioApp


def _configure_logging():
    """Send logs to a file so they don't corrupt the terminal UI."""
    log_path = Path.home() / ".nesaudio.log"
    logging.basicConfig(
        filename=str(log_path),
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def main():
    """Main entry point for NESAUDIO application"""
    _configure_logging()
    try:
        app = NESAudioApp()
        app.run()
    except KeyboardInterrupt:
        print("\nExiting NESAUDIO...")
        sys.exit(0)
    except Exception as e:
        logging.getLogger(__name__).exception("Error starting NESAUDIO")
        print(f"Error starting NESAUDIO: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
