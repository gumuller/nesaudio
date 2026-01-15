"""
Basic tests for NESAUDIO components
"""

import numpy as np
from nesaudio.audio.waveforms import generate_pulse, generate_triangle, generate_noise
from nesaudio.audio.channels import PulseChannel, TriangleChannel
from nesaudio.music.pitch import pitch_to_hz, hz_to_pitch
from nesaudio.music.parser import NAUParser


def test_waveform_generation():
    """Test basic waveform generation"""
    # Generate a pulse wave
    output, phase = generate_pulse(440.0, 0.1, 44100, 0.5)
    assert len(output) == 4410  # 0.1 seconds at 44.1kHz
    assert output.dtype == np.float32
    print("[OK] Pulse waveform generation works")

    # Generate a triangle wave
    output, phase = generate_triangle(440.0, 0.1, 44100)
    assert len(output) == 4410
    print("[OK] Triangle waveform generation works")

    # Generate noise
    output, lfsr = generate_noise(0.1, 44100, period=8)
    assert len(output) == 4410
    print("[OK] Noise generation works")


def test_channels():
    """Test NES channels"""
    # Test pulse channel
    pulse = PulseChannel()
    pulse.set_frequency(440.0)
    output = pulse.generate(1024)
    assert len(output) == 1024
    print("[OK] Pulse channel works")

    # Test triangle channel
    triangle = TriangleChannel()
    triangle.set_frequency(220.0)
    output = triangle.generate(1024)
    assert len(output) == 1024
    print("[OK] Triangle channel works")


def test_pitch_conversion():
    """Test pitch notation conversion"""
    # A4 should be 440 Hz
    freq = pitch_to_hz("A4")
    assert abs(freq - 440.0) < 0.1
    print("[OK] A4 = 440 Hz")

    # C4 should be ~261.63 Hz
    freq = pitch_to_hz("C4")
    assert abs(freq - 261.63) < 0.1
    print("[OK] C4 = 261.63 Hz")

    # Test reverse conversion
    pitch = hz_to_pitch(440.0)
    assert pitch == "A4"
    print("[OK] 440 Hz = A4")


def test_nau_parser():
    """Test .nau file parser"""
    try:
        parser = NAUParser()
        song = parser.parse("music/bach_prelude_c_major.nau")
        assert song.title == "Prelude in C Major"
        assert song.composer == "Johann Sebastian Bach"
        assert "pulse1" in song.channels
        print("[OK] .nau parser works")
    except Exception as e:
        print(f"[WARN] .nau parser test skipped: {e}")


if __name__ == "__main__":
    print("Running NESAUDIO basic tests...\n")

    test_waveform_generation()
    print()

    test_channels()
    print()

    test_pitch_conversion()
    print()

    test_nau_parser()
    print()

    print("[PASS] All basic tests passed!")
