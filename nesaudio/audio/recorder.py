"""
Audio recorder for saving output to WAV files
"""

import numpy as np
from scipy.io import wavfile
from pathlib import Path
from datetime import datetime
from typing import Optional
from ..config import SAMPLE_RATE, RECORDING_DIR


class Recorder:
    """Records audio output to WAV files"""

    def __init__(self, sample_rate: int = SAMPLE_RATE, output_dir: str = RECORDING_DIR):
        self.sample_rate = sample_rate
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.is_recording = False
        self.buffer: list = []
        self.current_filename: Optional[str] = None

    def start(self, filename: Optional[str] = None):
        """
        Start recording.

        Args:
            filename: Optional filename. If None, generates timestamp-based name
        """
        if self.is_recording:
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"

        self.current_filename = filename
        self.buffer = []
        self.is_recording = True

    def write(self, audio_data: np.ndarray):
        """
        Write audio data to recording buffer.

        Args:
            audio_data: Audio samples to record
        """
        if self.is_recording:
            self.buffer.append(audio_data.copy())

    def stop(self) -> Optional[str]:
        """
        Stop recording and save to file.

        Returns:
            Path to saved file, or None if recording wasn't active
        """
        if not self.is_recording:
            return None

        self.is_recording = False

        if not self.buffer:
            return None

        # Concatenate all buffers
        full_audio = np.concatenate(self.buffer)

        # Convert to int16 for WAV file
        # Scale from [-1.0, 1.0] to int16 range
        audio_int16 = np.int16(full_audio * 32767)

        # Save to file
        filepath = self.output_dir / self.current_filename
        wavfile.write(str(filepath), self.sample_rate, audio_int16)

        self.buffer = []
        return str(filepath)

    def cancel(self):
        """Cancel recording without saving"""
        self.is_recording = False
        self.buffer = []
        self.current_filename = None

    def get_duration(self) -> float:
        """
        Get current recording duration in seconds.

        Returns:
            Duration in seconds
        """
        if not self.buffer:
            return 0.0

        total_samples = sum(len(buf) for buf in self.buffer)
        return total_samples / self.sample_rate

    def get_buffer_size_mb(self) -> float:
        """
        Get current buffer size in MB.

        Returns:
            Buffer size in megabytes
        """
        if not self.buffer:
            return 0.0

        total_samples = sum(len(buf) for buf in self.buffer)
        # float32 = 4 bytes per sample
        bytes_size = total_samples * 4
        return bytes_size / (1024 * 1024)
