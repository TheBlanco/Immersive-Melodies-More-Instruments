"""
Builds the acoustic guitar's c1.ogg .. c8.ogg from recorded single notes.

Source: "Shinyguitar" by Karoryfer Samples (archtop guitar, microphone samples), CC0 1.0 / public domain:
https://github.com/sfzinstruments/karoryfer.shinyguitar
Download these files from Samples/acoustic/ into one folder, renamed as shown:
    db2_vl2_rr1_1.wav -> db2.wav    c3_vl2_rr1_1.wav -> c3.wav    c4_vl2_rr1_1.wav -> c4.wav
    c5_vl2_rr1_1.wav  -> c5.wav     c6_vl2_rr1_1.wav -> c6.wav

Each octave sample is resampled to an exact C (the recordings are a few cents off, measured below), cut to the
same lengths as the other instruments, faded out and normalized to the same peak level. Octaves the recording
does not cover are pitched from the nearest note: c1-c2 down from D-flat 2, c7-c8 up from C6.

Usage: python tools/import_acoustic_samples.py <folder with the wav files>
Needs ffmpeg on PATH.
"""

import os
import struct
import subprocess
import sys
import tempfile

RATE = 44100
PEAK_DB = -5.0  # same headroom as the other instruments
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "main", "resources", "assets",
                       "immersive_electric_guitar", "sounds", "instruments", "acoustic_guitar")

# Measured pitch of each recording (Hz)
SOURCES = {"db2": 69.53, "c3": 130.26, "c4": 261.59, "c5": 523.22, "c6": 1045.49}
# Which recording each octave sample is made from
OCTAVES = {1: "db2", 2: "db2", 3: "c3", 4: "c4", 5: "c5", 6: "c6", 7: "c6", 8: "c6"}


def c_frequency(octave):
    return 440.0 * 2 ** ((octave * 12 - 57) / 12)


def note_seconds(octave):
    # Low strings ring longer; very high notes are short plinks (matches the electric guitar's samples)
    return max(0.6, min(4.5, 4.5 * (130.0 / c_frequency(octave)) ** 0.35))


def build(folder, octave, out_path):
    source = OCTAVES[octave]
    ratio = c_frequency(octave) / SOURCES[source]
    seconds = note_seconds(octave)
    fade = 0.15
    shape = (f"asetrate={RATE * ratio:.3f},aresample={RATE}:resampler=soxr,"
             f"atrim=0:{seconds:.3f},afade=t=out:st={seconds - fade:.3f}:d={fade}")
    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, "note.f32")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(folder, f"{source}.wav"),
                        "-af", shape, "-ac", "1", "-f", "f32le", raw], check=True)
        data = open(raw, "rb").read()
        samples = struct.unpack(f"<{len(data) // 4}f", data)
        peak = max(abs(s) for s in samples) or 1.0
        gain = 10 ** (PEAK_DB / 20) / peak
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(RATE), "-ac", "1",
                        "-i", raw, "-af", f"volume={gain:.6f}", "-c:a", "libvorbis", "-q:a", "5", out_path],
                       check=True)
    return source, ratio


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = sys.argv[1]
    os.makedirs(OUT_DIR, exist_ok=True)
    for octave in range(1, 9):
        path = os.path.join(OUT_DIR, f"c{octave}.ogg")
        source, ratio = build(folder, octave, path)
        print(f"c{octave}: from {source} x{ratio:.4f} -> {os.path.normpath(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
