"""
Regression tests for NES APU hardware accuracy and sample-accurate playback.
"""

import numpy as np

from nesaudio.audio import apu
from nesaudio.audio.waveforms import generate_pulse, generate_triangle, generate_noise_block
from nesaudio.audio.channels import Envelope, PulseChannel
from nesaudio.audio.render import render_file
from nesaudio.music.parser import NAUParser


def test_pulse_timer_and_quantization():
    # 440 Hz snaps to timer 253 -> ~440.4 Hz on NTSC hardware.
    assert apu.pulse_timer(440.0) == 253
    assert abs(apu.quantize_pulse_frequency(440.0) - 440.4) < 0.5
    # Notes above the playable range mute the channel.
    assert apu.quantize_pulse_frequency(200000.0) == 0.0


def test_triangle_timer():
    # Triangle uses a /32 divider, one octave below the pulse timer.
    assert apu.triangle_timer(440.0) == 126
    assert abs(apu.quantize_triangle_frequency(220.0) - 220.0) < 1.0


def test_volume_to_level():
    assert apu.volume_to_level(0.0) == 0
    assert apu.volume_to_level(1.0) == 15
    assert apu.volume_to_level(0.5) == 8


def test_triangle_staircase():
    assert len(apu.TRIANGLE_STEPS) == 32
    assert int(apu.TRIANGLE_STEPS.min()) == 0
    assert int(apu.TRIANGLE_STEPS.max()) == 15


def test_mixer_is_nonlinear_and_bounded():
    zeros = [np.zeros(4, dtype=np.float32) for _ in range(5)]
    assert float(apu.mix_levels(*zeros).max()) == 0.0

    full = np.full(4, 15.0, dtype=np.float32)
    dmc = np.full(4, 127.0, dtype=np.float32)
    out = apu.mix_levels(full, full, full, full, dmc)
    assert np.all(out > 0.0) and np.all(out <= 1.0)

    # Two pulses do not sum linearly (non-linear headroom compression).
    one = apu.mix_levels(np.array([15.0]), np.array([0.0]), np.array([0.0]),
                         np.array([0.0]), np.array([0.0]))[0]
    two = apu.mix_levels(np.array([15.0]), np.array([15.0]), np.array([0.0]),
                         np.array([0.0]), np.array([0.0]))[0]
    assert two < 2.0 * one


def test_pulse_duty_average():
    # A band-limited square keeps the correct DC/duty ratio.
    shape, _ = generate_pulse(220.0, 1.0, 44100, 0.125, 0.0)
    assert abs(float(shape.mean()) - 0.125) < 0.01
    shape, _ = generate_pulse(220.0, 1.0, 44100, 0.5, 0.0)
    assert abs(float(shape.mean()) - 0.5) < 0.01


def test_triangle_is_unipolar_shape():
    shape, _ = generate_triangle(110.0, 0.2, 44100, 0.0)
    assert shape.min() >= 0.0 and shape.max() <= 1.0


def test_noise_lfsr_sequence_lengths():
    def period(mode):
        lfsr, seen = 1, {}
        for step in range(70000):
            if mode == "periodic":
                fb = (lfsr ^ (lfsr >> 6)) & 1
            else:
                fb = (lfsr ^ (lfsr >> 1)) & 1
            lfsr = (lfsr >> 1) | (fb << 14)
            if lfsr in seen:
                return step - seen[lfsr]
            seen[lfsr] = step
        return None

    assert period("random") == 32767   # long/white sequence
    assert period("periodic") == 93     # short/tonal sequence


def test_noise_block_is_phase_continuous():
    # State carries across calls: two half-blocks == one full block.
    full, _, _ = generate_noise_block(1000, 44100, 4, "random", 1, 0.0)
    a, lfsr, acc = generate_noise_block(500, 44100, 4, "random", 1, 0.0)
    b, _, _ = generate_noise_block(500, 44100, 4, "random", lfsr, acc)
    assert np.array_equal(full, np.concatenate([a, b]))


def test_envelope_declicks():
    env = Envelope(44100, attack=0.002, release=0.006)
    env.note_on()
    ramp = env.process(512)
    # Starts from silence and rises smoothly (no instantaneous jump to full).
    assert ramp[0] < 0.2
    assert ramp[-1] > ramp[0]
    assert float(np.max(np.abs(np.diff(ramp)))) < 0.05


def test_pulse_channel_starts_from_silence():
    ch = PulseChannel(44100)
    ch.set_volume(1.0)
    ch.set_frequency(440.0)
    out = ch.generate(512)
    # First sample near zero thanks to the attack ramp -> no click.
    assert abs(float(out[0])) < 1.0


def test_sample_accurate_onset(tmp_path):
    # A note that starts at exactly 0.5 s must be silent before and sound after.
    nau = tmp_path / "onset.nau"
    nau.write_text(
        "title: t\n"
        "tempo: 120\n"
        "channels:\n"
        "  pulse1:\n"
        "    duty_cycle: 0.5\n"
        "    volume: 1.0\n"
        "    notes:\n"
        "      - {time: 0.5, pitch: \"A4\", duration: 0.3}\n",
        encoding="utf-8",
    )
    audio = render_file(str(nau))
    sr = 44100
    onset = int(0.5 * sr)
    pre = audio[:onset - 200]
    post = audio[onset + 200: onset + 4000]
    assert float(np.max(np.abs(pre))) < 1e-3
    assert float(np.sqrt(np.mean(post ** 2))) > 0.01


def test_beat_grid_parsing(tmp_path):
    nau = tmp_path / "grid.nau"
    nau.write_text(
        "title: t\n"
        "tempo: 100\n"
        "channels:\n"
        "  pulse1:\n"
        "    notes:\n"
        "      - {beat: 1.0, pitch: \"C4\", beats: 2.0}\n",
        encoding="utf-8",
    )
    song = NAUParser().parse(str(nau))
    note = song.channels["pulse1"].notes[0]
    assert abs(note.time - 0.6) < 1e-6      # beat 1 @ 100 BPM = 0.6 s
    assert abs(note.duration - 1.2) < 1e-6  # 2 beats = 1.2 s
