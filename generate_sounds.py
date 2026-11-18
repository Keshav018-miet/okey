"""
generate_sounds.py - Generates synthetic, miserable sound effects for Ugh.
Uses only the Python standard library because installing yet another audio synthesis library
would probably push me into early retirement.
"""

import math
import os
import struct
import wave

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")


def create_pcm_wav(filename: str, sample_rate: int, duration_sec: float, sample_func):
    """
    Spits out an uncompressed PCM 16-bit mono WAV file.
    Does it have high acoustic fidelity? Absolutely not.
    Does it sound like the slow death of a CRT monitor? Yes.
    """
    total_samples = int(sample_rate * duration_sec)
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    filepath = os.path.join(SOUNDS_DIR, filename)

    with wave.open(filepath, "w") as wav_file:
        # Mono, 2 bytes (16-bit), sample_rate
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(total_samples):
            t = float(i) / sample_rate
            amplitude = sample_func(t, duration_sec)
            # Clamp to 16-bit signed integer range
            sample_val = int(max(-32767, min(32767, amplitude * 32767)))
            frames.extend(struct.pack("<h", sample_val))

        wav_file.writeframes(frames)
    print(f"Synthesized acoustic misery: {filepath}")


def miserable_sigh(t: float, total: float) -> float:
    """Downwards sliding frequency with decreasing amplitude. The acoustic equivalent of giving up."""
    decay = (1.0 - (t / total)) ** 1.5
    # Pitch drops from 280Hz down to 80Hz
    freq = 280.0 - (200.0 * (t / total))
    return 0.4 * math.sin(2.0 * math.pi * freq * t) * decay


def flatline_buzz(t: float, total: float) -> float:
    """A monotonous, irritating low frequency drone. Sounds like an ungrounded cable."""
    # 60Hz hum + 120Hz harmonic with jitter
    decay = 0.5 if t < (total - 0.1) else (total - t) / 0.1
    return 0.3 * (math.sin(2 * math.pi * 75 * t) + 0.5 * math.sin(2 * math.pi * 150 * t)) * decay


def disappointment_descend(t: float, total: float) -> float:
    """Two-tone 'wah-wah' of utter disillusionment."""
    phase = t / total
    freq = 220.0 if phase < 0.5 else 165.0
    mod = math.sin(2.0 * math.pi * 6.0 * t) * 0.1  # Vibrato of despair
    return 0.35 * math.sin(2.0 * math.pi * (freq + mod) * t) * (1.0 - phase)


if __name__ == "__main__":
    print("Generating emergency dummy sounds so you don't have to record your own sighs...")
    create_pcm_wav("sigh_of_the_void.wav", 22050, 1.8, miserable_sigh)
    create_pcm_wav("ungrounded_existential_hum.wav", 22050, 1.5, flatline_buzz)
    create_pcm_wav("corporate_disappointment.wav", 22050, 2.0, disappointment_descend)
    print("Done. You now have 3 auditory punishments in ./sounds/")
