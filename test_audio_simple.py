"""
Simple audio test without UI
"""

import time
from nesaudio.audio.engine import AudioEngine
from nesaudio.music.pitch import pitch_to_hz

print("Testing NESAUDIO audio engine...")
print()

try:
    # Create and start audio engine
    print("1. Starting audio engine...")
    engine = AudioEngine()
    engine.start()
    print("   Audio engine started successfully!")

    # Test pulse channel
    print("\n2. Testing Pulse 1 channel...")
    pulse1 = engine.channels.pulse1
    pulse1.set_frequency(440.0)  # A4
    print("   Playing A4 (440 Hz) for 2 seconds...")
    time.sleep(2)
    pulse1.note_off()

    # Test triangle channel
    print("\n3. Testing Triangle channel...")
    triangle = engine.channels.triangle
    triangle.set_frequency(220.0)  # A3
    print("   Playing A3 (220 Hz) for 2 seconds...")
    time.sleep(2)
    triangle.note_off()

    # Test noise channel
    print("\n4. Testing Noise channel...")
    noise = engine.channels.noise
    noise.set_period(8)
    noise.trigger(duration=1.0)
    print("   Playing noise for 1 second...")
    time.sleep(1.5)

    # Test spectrum analyzer
    print("\n5. Testing spectrum analyzer...")
    pulse1.set_frequency(880.0)  # A5
    time.sleep(0.5)
    spectrum = engine.get_spectrum_data(32)
    print(f"   Spectrum data shape: {spectrum.shape}")
    print(f"   Max value: {spectrum.max():.3f}")
    pulse1.note_off()

    print("\n6. Stopping audio engine...")
    engine.stop()
    print("   Audio engine stopped.")

    print("\n✓ All audio tests passed!")
    print("\nIf you heard sounds, the audio engine is working correctly.")
    print("The issue might be with the terminal UI initialization.")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
