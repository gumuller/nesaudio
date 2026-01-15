"""
Simple music player for .nau files
"""

import sys
import time
from pathlib import Path
from nesaudio.audio.engine import AudioEngine
from nesaudio.music.player import MusicPlayer

def play_nau_file(filepath):
    """Play a .nau music file"""
    filepath = Path(filepath)

    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        return

    print(f"\nNESAUDIO Music Player")
    print(f"{'='*50}")

    # Create audio engine and music player
    print("Starting audio engine...")
    engine = AudioEngine()
    engine.start()

    player = MusicPlayer(engine)

    try:
        # Load the music file
        print(f"Loading: {filepath.name}")
        player.load(str(filepath))

        # Get song info
        info = player.get_song_info()
        print(f"\nTitle: {info['title']}")
        print(f"Composer: {info['composer']}")
        print(f"Tempo: {info['tempo']} BPM")
        print(f"Duration: {info['duration']:.1f} seconds")
        print(f"\nPlaying... (Press Ctrl+C to stop)\n")

        # Start playback
        player.play(loop=False)

        # Update loop
        start_time = time.time()
        duration = player.get_duration()

        while player.is_playing():
            player.update()

            # Show progress
            current = player.get_current_time()
            progress = player.get_progress()
            bar_length = 40
            filled = int(bar_length * progress)
            bar = '#' * filled + '-' * (bar_length - filled)

            elapsed = time.time() - start_time
            print(f"\r[{bar}] {current:.1f}s / {duration:.1f}s", end='', flush=True)

            time.sleep(0.033)  # ~30 FPS

        print("\n\n[OK] Playback finished!")

    except KeyboardInterrupt:
        print("\n\n[STOP] Playback stopped by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        player.stop()
        engine.stop()
        print("Audio engine stopped.")


def list_music_files():
    """List available .nau files"""
    music_dir = Path("music")
    if not music_dir.exists():
        print("Error: music/ directory not found")
        return []

    nau_files = list(music_dir.glob("*.nau"))
    return sorted(nau_files)


def main():
    """Main function"""
    print("\nNESAUDIO Music Player")
    print("="*50)

    # List available songs
    songs = list_music_files()

    if not songs:
        print("No .nau files found in music/ directory")
        return

    print("\nAvailable songs:")
    for i, song in enumerate(songs, 1):
        print(f"  {i}. {song.name}")

    # Check if file was provided as argument
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        play_nau_file(filepath)
    else:
        # Interactive selection
        print("\nUsage:")
        print("  python play_music.py <filename.nau>")
        print("  python play_music.py music/mario_overworld.nau")
        print("\nOr run with a song number:")

        try:
            choice = input("\nEnter song number (1-6) or press Enter to play first song: ").strip()
            if choice == "":
                choice = "1"

            idx = int(choice) - 1
            if 0 <= idx < len(songs):
                play_nau_file(songs[idx])
            else:
                print("Invalid choice")
        except (ValueError, KeyboardInterrupt):
            print("\nCancelled")


if __name__ == "__main__":
    main()
