"""
Deterministic offline rendering of .nau songs.

Renders a song through the *exact* same channel/scheduler/mixer path the live
engine uses, but without a sound device.  Because it is driven purely by the
sample clock it is fully reproducible, which makes it ideal for validation,
regression testing and exporting WAVs for A/B comparison against references.
"""

import wave
from pathlib import Path

import numpy as np

from .engine import AudioEngine
from ..music.player import MusicPlayer
from ..config import SAMPLE_RATE, BUFFER_SIZE


def render_file(filepath: str, sample_rate: int = SAMPLE_RATE,
                block: int = BUFFER_SIZE, max_seconds: float = 900.0) -> np.ndarray:
    """Render a .nau file to a mono float32 numpy array in [-1, 1]."""
    engine = AudioEngine(sample_rate, block)
    player = MusicPlayer(engine)
    player.load(str(filepath))
    engine.play_song(loop=False)

    blocks = []
    max_samples = int(max_seconds * sample_rate)
    total = 0
    while engine.scheduler.playing and total < max_samples:
        chunk = engine._render_song_block(block)
        blocks.append(chunk)
        total += len(chunk)

    if not blocks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(blocks).astype(np.float32)


def write_wav(path: str, audio: np.ndarray, sample_rate: int = SAMPLE_RATE):
    """Write a mono float32 array to a 16-bit PCM WAV file."""
    clipped = np.clip(audio, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def render_file_to_wav(filepath: str, out_path: str = None,
                       sample_rate: int = SAMPLE_RATE) -> tuple[str, np.ndarray]:
    """Render a .nau file and write it to a WAV, returning (path, audio)."""
    audio = render_file(filepath, sample_rate=sample_rate)
    if out_path is None:
        out_dir = Path("recordings")
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / (Path(filepath).stem + ".wav")
    write_wav(out_path, audio, sample_rate)
    return str(out_path), audio


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    if not args:
        print("Usage: python -m nesaudio.audio.render <file.nau> [out.wav]")
        print("       python -m nesaudio.audio.render --all")
        raise SystemExit(1)

    if args[0] == "--all":
        music_dir = Path("music")
        out_dir = Path("recordings")
        out_dir.mkdir(exist_ok=True)
        for nau in sorted(music_dir.glob("*.nau")):
            try:
                dest = out_dir / (nau.stem + ".wav")
                _, audio = render_file_to_wav(str(nau), str(dest))
                peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
                print(f"OK   {nau.name:34s} {len(audio) / SAMPLE_RATE:6.2f}s  peak={peak:.3f}")
            except Exception as exc:  # noqa: BLE001 - report and continue
                print(f"FAIL {nau.name:34s} {exc}")
        raise SystemExit(0)

    out = args[1] if len(args) > 1 else None
    path, audio = render_file_to_wav(args[0], out)
    peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
    print(f"Rendered {len(audio)} samples ({len(audio) / SAMPLE_RATE:.2f}s) -> {path}")
    print(f"Peak level: {peak:.3f}")
