"""
Synthesizes the electric guitar samples (c1.ogg .. c8.ogg) used by Immersive Melodies.

Each octave is rendered at its exact C pitch instead of speed-shifting one sample, so the tone
and decay stay natural across the whole range. Pure standard library; needs ffmpeg on PATH.

Usage: python tools/generate_sounds.py
"""

import math
import os
import random
import struct
import subprocess
import sys
import tempfile
import wave

RATE = 44100
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "main", "resources", "assets",
                       "immersive_electric_guitar", "sounds", "instruments", "electric_guitar")

PEAK_DB = -5.0  # matches the headroom of the built-in instruments
# Immersive Melodies plays MIDI notes 31-41 from c2, which covers a drop-D guitar's low strings (D2 = 38),
# so only c1 (MIDI 30 and below, under any guitar string) plays as a bass
BASS_OCTAVES = (1,)

# Tones modelled on the intro of Foo Fighters' "Everlong": a bright, double-tracked, mid-gain humbucker
# crunch, and a gritty picked bass underneath.
GUITAR = {
    "pluck": 0.12,             # fraction of string length where the pick hits
    "pickups": (0.16, 0.20),   # humbucker: two coils side by side, averaged
    "brightness": 9000.0,      # highest partial rendered before the amp
    "decay": (0.8, 0.45),      # base damping and extra damping per harmonic
    "pick": (0.35, 3200.0),    # pick attack noise level and colour
    "drive": 2.6,
    "bias": 0.15,              # asymmetric clipping gives the tube-amp crunch
    "highpass": 55.0,          # low enough to keep the drop-D low string (73 Hz)
    "cabinet": 4200.0,
    "doubled": True,           # two takes, slightly out of tune and time, like a double-tracked part
}
BASS = {
    "pluck": 0.2,
    "pickups": (0.24, 0.27),   # split-coil pickup near the middle: round and punchy
    "brightness": 4000.0,
    "decay": (0.5, 0.35),
    "pick": (0.3, 2000.0),
    "drive": 1.8,
    "bias": 0.1,
    "highpass": 28.0,
    "cabinet": 2200.0,
    "doubled": False,
}


def c_frequency(octave):
    # C4 = 261.63 Hz
    return 440.0 * 2 ** ((octave * 12 + 0 - 57) / 12)


def one_pole_lowpass(samples, cutoff):
    a = math.exp(-2 * math.pi * cutoff / RATE)
    y = 0.0
    out = []
    for x in samples:
        y = (1 - a) * x + a * y
        out.append(y)
    return out


def one_pole_highpass(samples, cutoff):
    a = math.exp(-2 * math.pi * cutoff / RATE)
    y = 0.0
    prev = 0.0
    out = []
    for x in samples:
        y = a * (y + x - prev)
        prev = x
        out.append(y)
    return out


def pluck_string(f0, n, tone, detune_cents=0.0, delay=0):
    f0 *= 2 ** (detune_cents / 1200)
    coils = tone["pickups"]
    decay_base, decay_per_harmonic = tone["decay"]

    # Plucked-string harmonic series, shaped by pluck and pickup position
    out = [0.0] * n
    for k in range(1, 64):
        freq = f0 * k * math.sqrt(1 + 0.00008 * k * k)  # string stiffness pushes upper partials sharp
        if freq > tone["brightness"]:
            break
        amp = abs(math.sin(math.pi * k * tone["pluck"])) / k
        amp *= abs(sum(math.sin(math.pi * k * c) for c in coils) / len(coils)) * 3.0
        decay = decay_base + decay_per_harmonic * k + f0 / 250.0
        omega = 2 * math.pi * freq / RATE
        phase = random.uniform(0, 2 * math.pi)

        # Recursive oscillator: y[t] = 2cos(w) y[t-1] - y[t-2], with exponential damping folded in
        r = math.exp(-decay / RATE)
        c = 2 * r * math.cos(omega)
        r2 = r * r
        y1 = amp * math.sin(phase - omega) / r
        y2 = amp * math.sin(phase - 2 * omega) / r2
        for t in range(delay, n):
            y = c * y1 - r2 * y2
            out[t] += y
            y2 = y1
            y1 = y

    # Pick attack: a short burst of filtered noise
    level, colour = tone["pick"]
    attack = int(0.012 * RATE)
    noise = one_pole_lowpass([random.uniform(-1, 1) for _ in range(attack)], colour)
    for t in range(min(attack, n - delay)):
        out[delay + t] += noise[t] * level * (1 - t / attack)

    peak = max(abs(s) for s in out) or 1.0
    return [s / peak for s in out]


def amp(samples, tone, octave):
    # Asymmetric soft clip; backed off on the top octaves where clipping would just alias
    drive = tone["drive"] * (1.0 if octave <= 5 else 0.6 ** (octave - 5))
    bias = tone["bias"]
    offset = math.tanh(drive * bias)
    out = [math.tanh(drive * (s + bias)) - offset for s in samples]
    out = one_pole_highpass(out, tone["highpass"])
    return one_pole_lowpass(one_pole_lowpass(out, tone["cabinet"]), tone["cabinet"] * 1.4)


def render(octave):
    tone = BASS if octave in BASS_OCTAVES else GUITAR
    f0 = c_frequency(octave)
    # Low strings ring longer; very high notes are short plinks
    duration = max(0.6, min(4.5, 4.5 * (130.0 / f0) ** 0.35))
    n = int(duration * RATE)

    if tone["doubled"]:
        # Each take goes through its own amp, then the two are layered
        first = amp(pluck_string(f0, n, tone, -4.0), tone, octave)
        second = amp(pluck_string(f0, n, tone, 5.0, int(0.014 * RATE)), tone, octave)
        out = [a + 0.8 * b for a, b in zip(first, second)]
    else:
        out = amp(pluck_string(f0, n, tone), tone, octave)

    # Short fade in/out to avoid clicks
    fade_in = int(0.002 * RATE)
    fade_out = int(0.15 * RATE)
    for t in range(fade_in):
        out[t] *= t / fade_in
    for t in range(fade_out):
        out[n - 1 - t] *= t / fade_out

    target = 10 ** (PEAK_DB / 20)
    peak = max(abs(s) for s in out) or 1.0
    return [s * target / peak for s in out]


def write_ogg(samples, path):
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = os.path.join(tmp, "note.wav")
        with wave.open(wav_path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path,
                        "-c:a", "libvorbis", "-q:a", "4", "-ac", "1", path], check=True)


def main():
    random.seed(1337)
    os.makedirs(OUT_DIR, exist_ok=True)
    for octave in range(1, 9):
        path = os.path.join(OUT_DIR, f"c{octave}.ogg")
        write_ogg(render(octave), path)
        print(f"c{octave}: {c_frequency(octave):.2f} Hz -> {os.path.normpath(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
