"""
Renders a MIDI file the way Immersive Melodies would play it on one of this mod's instruments, so a sound can be
judged without starting Minecraft.

It follows the mod's playback rules (0.8.x): each note picks the c1..c8 sample whose octave holds it and is
pitch-shifted from there, volume follows velocity with the default perceived-loudness adjustment, and every note
rings for its length plus the instrument's 300 ms sustain, fading out over that sustain. Humanization is skipped.

Usage: python tools/preview_melody.py <instrument> <song.mid> <out.mp3> [seconds]
Needs ffmpeg on PATH.
"""

import math
import os
import struct
import subprocess
import sys
import tempfile
import wave

RATE = 44100
SUSTAIN = 0.3            # seconds, the sustain every instrument in this mod registers (300)
LOUDNESS_FACTOR = 0.5    # Immersive Melodies' default perceivedLoudnessAdjustmentFactor
SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "main", "resources", "assets",
                          "immersive_electric_guitar", "sounds", "instruments")


def read_midi(path):
    """Returns (start seconds, length seconds, note, velocity) for every note in every track."""
    data = open(path, "rb").read()
    _, ntracks, division = struct.unpack(">HHH", data[8:14])
    pos, tracks = 14, []
    for _ in range(ntracks):
        length = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        tracks.append(data[pos + 8:pos + 8 + length])
        pos += 8 + length

    # Tempo map (in ticks) from every track, then notes converted to seconds through it
    tempos, raw_notes = [(0, 500000)], []
    for track in tracks:
        i, tick, running, held = 0, 0, None, {}

        def vlq():
            nonlocal i
            value = 0
            while True:
                byte = track[i]
                i += 1
                value = (value << 7) | (byte & 0x7F)
                if byte < 0x80:
                    return value

        while i < len(track):
            tick += vlq()
            status = track[i]
            if status == 0xFF:
                kind = track[i + 1]
                i += 2
                size = vlq()
                if kind == 0x51:
                    tempos.append((tick, int.from_bytes(track[i:i + size], "big")))
                i += size
                continue
            if status in (0xF0, 0xF7):
                i += 1
                size = vlq()
                i += size
                continue
            if status >= 0x80:
                running = status
                i += 1
            kind, channel = running >> 4, running & 0x0F
            if kind in (0xC, 0xD):
                i += 1
                continue
            a, b = track[i], track[i + 1]
            i += 2
            key = (channel, a)
            if kind == 0x9 and b > 0:
                held[key] = (tick, b)
            elif kind in (0x8, 0x9) and key in held:
                start, velocity = held.pop(key)
                raw_notes.append((start, tick, a, velocity))

    tempos.sort()

    def seconds(tick):
        total, last_tick, tempo = 0.0, 0, 500000
        for t, new_tempo in tempos:
            if t > tick:
                break
            total += (t - last_tick) * tempo / division / 1e6
            last_tick, tempo = t, new_tempo
        return total + (tick - last_tick) * tempo / division / 1e6

    return sorted((seconds(s), seconds(e) - seconds(s), n, v) for s, e, n, v in raw_notes)


def load_samples(instrument):
    samples = {}
    with tempfile.TemporaryDirectory() as tmp:
        for octave in range(1, 9):
            raw = os.path.join(tmp, f"c{octave}.raw")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i",
                            os.path.join(SOUNDS_DIR, instrument, f"c{octave}.ogg"),
                            "-f", "f32le", "-ac", "1", "-ar", str(RATE), raw], check=True)
            data = open(raw, "rb").read()
            samples[octave] = struct.unpack(f"<{len(data) // 4}f", data)
    return samples


def render(notes, samples, limit):
    end = min(limit, max(s + l for s, l, _, _ in notes) + SUSTAIN + 0.5)
    mix = [0.0] * int(end * RATE)
    for start, length, note, velocity in notes:
        if start >= end:
            continue
        # Same octave choice and loudness adjustment as InstrumentItem.playNote
        pitch = 2 ** ((note - 24) / 12)
        octave = 1
        while octave < 8 and pitch > 4 / 3:
            pitch /= 2
            octave += 1
        volume = velocity / 255 * 2
        adjusted = volume / math.sqrt(pitch * 2 ** (octave - 4))
        volume = min(1.0, volume * (1 - LOUDNESS_FACTOR) + adjusted * LOUDNESS_FACTOR)

        sample = samples[octave]
        total = min(int((max(length, 0.001) + SUSTAIN) * RATE), int((len(sample) - 2) / pitch))
        fade = int(SUSTAIN * RATE)
        base = int(start * RATE)
        for k in range(min(total, len(mix) - base)):
            x = k * pitch
            j = int(x)
            f = x - j
            gain = min(1.0, (total - k) / fade) * volume
            mix[base + k] += (sample[j] * (1 - f) + sample[j + 1] * f) * gain
    return mix


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    instrument, midi_path, out_path = sys.argv[1:4]
    limit = float(sys.argv[4]) if len(sys.argv) > 4 else float("inf")
    mix = render(read_midi(midi_path), load_samples(instrument), limit)
    peak = max(abs(s) for s in mix) or 1.0
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = os.path.join(tmp, "preview.wav")
        with wave.open(wav_path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(b"".join(struct.pack("<h", int(s / peak * 0.89 * 32767)) for s in mix))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path, "-c:a", "libmp3lame", "-q:a", "3",
                        out_path], check=True)
    print(f"Rendered {len(mix) / RATE:.1f} s -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
