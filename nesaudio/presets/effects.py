"""
Preset NES sound effects
"""

from typing import Callable


class SoundEffect:
    """Represents a sound effect that can be triggered"""

    def __init__(self, name: str, trigger_func: Callable):
        self.name = name
        self.trigger_func = trigger_func

    def trigger(self, audio_engine):
        """Trigger the sound effect on the audio engine"""
        self.trigger_func(audio_engine)


def jump_effect(audio_engine):
    """Classic jump sound - quick rising tone on pulse channel"""
    pulse = audio_engine.channels.pulse1

    # Save current state
    original_duty = pulse.duty_cycle
    original_vol = pulse.volume

    # Configure for jump sound
    pulse.set_duty_cycle(0.125)  # Thin sound
    pulse.set_volume(0.6)

    # Rising frequency sweep (simulated with quick frequency change)
    # In a real implementation, you might want to use a sweep unit
    pulse.set_frequency(200)  # Start low

    # Note: For a proper sweep, you'd need to implement it in the engine
    # This is a simplified version
    import threading

    def sweep():
        import time
        for freq in range(200, 800, 50):
            pulse.set_frequency(freq)
            time.sleep(0.01)
        pulse.note_off()
        pulse.set_duty_cycle(original_duty)
        pulse.set_volume(original_vol)

    threading.Thread(target=sweep, daemon=True).start()


def coin_effect(audio_engine):
    """Coin pickup sound - dual-tone arpeggio"""
    pulse = audio_engine.channels.pulse1

    original_duty = pulse.duty_cycle
    original_vol = pulse.volume

    pulse.set_duty_cycle(0.5)
    pulse.set_volume(0.7)

    import threading

    def arpeggio():
        import time
        # B5 -> E6 arpeggio
        frequencies = [987.77, 1318.51]  # B5, E6
        for _ in range(2):
            for freq in frequencies:
                pulse.set_frequency(freq)
                time.sleep(0.05)

        pulse.note_off()
        pulse.set_duty_cycle(original_duty)
        pulse.set_volume(original_vol)

    threading.Thread(target=arpeggio, daemon=True).start()


def powerup_effect(audio_engine):
    """Power-up sound - ascending scale"""
    pulse = audio_engine.channels.pulse1

    original_duty = pulse.duty_cycle
    original_vol = pulse.volume

    pulse.set_duty_cycle(0.25)
    pulse.set_volume(0.8)

    import threading

    def scale():
        import time
        # Ascending major scale
        frequencies = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]  # C4-C5
        for freq in frequencies:
            pulse.set_frequency(freq)
            time.sleep(0.08)

        pulse.note_off()
        pulse.set_duty_cycle(original_duty)
        pulse.set_volume(original_vol)

    threading.Thread(target=scale, daemon=True).start()


def shoot_effect(audio_engine):
    """Shoot sound - short noise burst"""
    noise = audio_engine.channels.noise

    original_vol = noise.volume
    original_mode = noise.mode

    noise.set_volume(0.5)
    noise.set_mode("random")
    noise.set_period(2)  # Higher pitch
    noise.trigger(duration=0.08)

    # Reset after a delay
    import threading

    def reset():
        import time
        time.sleep(0.1)
        noise.set_volume(original_vol)
        noise.set_mode(original_mode)

    threading.Thread(target=reset, daemon=True).start()


def hit_effect(audio_engine):
    """Hit/damage sound - short noise impact"""
    noise = audio_engine.channels.noise

    original_vol = noise.volume
    original_mode = noise.mode

    noise.set_volume(0.7)
    noise.set_mode("periodic")  # Tonal noise
    noise.set_period(10)  # Lower pitch for impact
    noise.trigger(duration=0.15)

    import threading

    def reset():
        import time
        time.sleep(0.2)
        noise.set_volume(original_vol)
        noise.set_mode(original_mode)

    threading.Thread(target=reset, daemon=True).start()


def explosion_effect(audio_engine):
    """Explosion sound - descending noise sweep"""
    noise = audio_engine.channels.noise

    original_vol = noise.volume
    original_mode = noise.mode

    noise.set_volume(0.8)
    noise.set_mode("random")

    import threading

    def sweep():
        import time
        # Descending period (pitch goes down)
        for period in range(1, 15):
            noise.set_period(period)
            noise.trigger(duration=0.04)
            time.sleep(0.03)

        noise.note_off()
        noise.set_volume(original_vol)
        noise.set_mode(original_mode)

    threading.Thread(target=sweep, daemon=True).start()


# Registry of all sound effects
EFFECTS = {
    'jump': SoundEffect('Jump', jump_effect),
    'coin': SoundEffect('Coin', coin_effect),
    'powerup': SoundEffect('Power-up', powerup_effect),
    'shoot': SoundEffect('Shoot', shoot_effect),
    'hit': SoundEffect('Hit', hit_effect),
    'explosion': SoundEffect('Explosion', explosion_effect),
}


class PresetManager:
    """Manages preset sound effects"""

    def __init__(self, audio_engine):
        self.audio_engine = audio_engine
        self.effects = EFFECTS

    def trigger(self, effect_name: str):
        """
        Trigger a sound effect by name.

        Args:
            effect_name: Name of the effect (e.g., 'jump', 'coin')
        """
        effect_name = effect_name.lower()
        if effect_name in self.effects:
            self.effects[effect_name].trigger(self.audio_engine)
        else:
            print(f"Unknown effect: {effect_name}")

    def get_effect_names(self) -> list[str]:
        """Get list of available effect names"""
        return list(self.effects.keys())

    def get_effect(self, name: str) -> SoundEffect:
        """Get a sound effect by name"""
        return self.effects.get(name.lower())
