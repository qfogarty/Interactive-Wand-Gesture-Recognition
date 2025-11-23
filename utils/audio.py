"""
Audio utilities for spell sound effects and background music.

Handles sound playback with volume ducking during spell casting.
"""

from pygame import mixer


def play_spell_sound(sound_effect, background_volume=0.6):
    """
    Play spell sound effect with background music ducking.

    Args:
        sound_effect: pygame.mixer.Sound instance to play
        background_volume: Normal background music volume (0.0-1.0)
    """
    mixer.music.set_volume(background_volume * 0.67)  # Duck to 67% during spell
    sound_effect.play()
    import time
    time.sleep(0.1)
    mixer.music.set_volume(background_volume)
