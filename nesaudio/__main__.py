"""
NESAUDIO - Main entry point
"""

import sys
from .ui.app import NESAudioApp


def main():
    """Main entry point for NESAUDIO application"""
    try:
        app = NESAudioApp()
        app.run()
    except KeyboardInterrupt:
        print("\nExiting NESAUDIO...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting NESAUDIO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
