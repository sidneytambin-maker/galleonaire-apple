"""Deterministic original audio and platform asset-catalog export. No sampled media."""
import json
import math
import random
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "Apple/App"
RATE = 22050


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def render_audio(name, duration, notes, noise=0.0):
    rng = random.Random(name)
    samples = [0.0] * int(duration * RATE)
    for onset, pitch, length, amplitude in notes:
        frequency = 440 * 2 ** ((pitch - 69) / 12)
        start = int(onset * RATE)
        for offset in range(min(int(length * RATE), len(samples) - start)):
            t = offset / RATE
            attack = min(1, t / 0.018)
            release = min(1, (length - t) / 0.10)
            envelope = attack * max(0, release) * math.exp(-t * 3 / max(length, .1))
            tone = (math.sin(2 * math.pi * frequency * t) + .22 * math.sin(2 * math.pi * frequency * 2.003 * t) + .09 * math.sin(2 * math.pi * frequency * 3.01 * t))
            samples[start + offset] += amplitude * envelope * tone
    if noise:
        previous = 0
        for i in range(len(samples)):
            t = i / RATE
            previous = .87 * previous + .13 * rng.uniform(-1, 1)
            samples[i] += noise * previous * math.sin(math.pi * min(1, t / duration)) ** 2
    write_audio(name, samples)


def write_audio(name, samples):
    peak = max(max(abs(v) for v in samples), 1)
    path = APP / "Audio" / f"{name}.wav"
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(RATE)
        audio.writeframes(b"".join(struct.pack("<h", round(max(-1, min(1, v / peak)) * 18000)) for v in samples))


def make_character_effects():
    # Contrasting instruments and textures, not pitch-shifted copies of one cue.
    samples = []
    for i in range(int(.85 * RATE)):
        t = i / RATE
        pulse = t if t < .34 else t - .43
        envelope = min(1, max(0, pulse) / .015) * max(0, 1 - pulse / .34) if 0 <= pulse < .34 else 0
        phase = 2 * math.pi * (135 * t - 24 * t * t)
        buzz = math.sin(phase) + .35 * math.sin(3 * phase) + .18 * math.sin(5 * phase)
        samples.append(.55 * envelope * buzz)
    write_audio("incorrect", samples)

    rng = random.Random("galleonaire-original-applause")
    samples = [0.0] * int(1.65 * RATE)
    for onset in sorted(rng.uniform(.02, 1.25) for _ in range(28)):
        amplitude = rng.uniform(.18, .38)
        previous = 0
        for offset in range(int(.16 * RATE)):
            t = offset / RATE
            raw = rng.uniform(-1, 1)
            high = raw - previous
            previous = .65 * previous + .35 * raw
            samples[int(onset * RATE) + offset] += amplitude * high * math.exp(-t * 38) * min(1, t / .002)
    write_audio("audience", samples)

    rng = random.Random("galleonaire-two-vanishing-answers")
    samples = [0.0] * int(.65 * RATE)
    for onset in (.02, .31):
        for offset in range(int(.22 * RATE)):
            t = offset / RATE
            phase = 2 * math.pi * (520 * t - 700 * t * t)
            tone = .55 * math.sin(phase) + .18 * rng.uniform(-1, 1)
            samples[int(onset * RATE) + offset] += tone * math.exp(-t * 22) * min(1, t / .005)
    write_audio("fiftyFifty", samples)

    rng = random.Random("galleonaire-page-swap")
    samples = []
    previous = 0
    for i in range(RATE):
        t = i / RATE
        raw = rng.uniform(-1, 1)
        previous = .82 * previous + .18 * raw
        envelope = math.sin(math.pi * t) ** 2
        shimmer = math.sin(2 * math.pi * (450 * t + 750 * t * t))
        samples.append(envelope * (.65 * previous + .16 * shimmer))
    write_audio("swapQuestion", samples)


def make_audio():
    # An original 24-second, six-bar celesta/pad loop. No external recordings or melodies.
    notes = []
    chords = [(45, 52, 57, 60), (41, 48, 53, 57), (48, 55, 60, 64), (43, 50, 55, 59), (41, 48, 57, 60), (40, 47, 56, 59)]
    for bar, chord in enumerate(chords):
        for note in chord: notes.append((bar * 4, note, 3.95, .08))
        for beat, offset in enumerate([0, 2, 1, 3, 2, 0]):
            notes.append((bar * 4 + beat * .5 + .1, chord[offset] + 24, 1.1, .10))
    render_audio("magical-library", 24, notes)
    events = {
        "selected": (.18, [(0, 84, .17, .40)], 0),
        "locked": (.38, [(0, 48, .16, .38), (.08, 60, .28, .35)], .25),
        "correct": (.95, [(0, 84, .32, .40), (.13, 88, .32, .40), (.26, 91, .65, .38), (.26, 84, .65, .22)], 0),
        "lifelineSelected": (.26, [(0, 81, .22, .32), (.055, 88, .20, .18)], 0),
        "lifelineActivated": (.62, [(0, 60, .4, .22), (.12, 67, .38, .24), (.24, 86, .35, .3)], .5),
        "lifelineResult": (.45, [(0, 79, .25, .3), (.15, 84, .29, .3)], 0),
        "nextQuestion": (.52, [(0, 55, .25, .18), (.15, 74, .32, .24)], .25),
        "milestone": (1.05, [(0, 60, .7, .22), (0, 64, .7, .22), (.18, 79, .65, .28), (.40, 84, .6, .28)], 0),
        "majorMilestone": (1.45, [(0, 48, 1, .2), (0, 55, 1, .2), (.2, 72, .7, .3), (.4, 76, .7, .3), (.6, 84, .8, .3)], .06),
        "victory": (2.0, [(0, 48, 1.6, .18), (0, 60, 1.5, .18), (.12, 72, .4, .25), (.3, 76, .4, .25), (.5, 79, .4, .25), (.7, 84, 1.2, .28), (.7, 88, 1.2, .18)], 0),
    }
    for name, (duration, notes, noise) in events.items(): render_audio(name, duration, notes, noise)
    make_character_effects()


def export_icon(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "darwin":
        subprocess.run(["sips", "-s", "format", "png", "-z", "1024", "1024", str(source), "--out", str(destination)], check=True, stdout=subprocess.DEVNULL)
    else:
        from PIL import Image
        with Image.open(source) as icon: icon.convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS).save(destination)


def make_icons():
    for catalog, platform in [("Assets", "ios"), ("WatchAssets", "watchos")]:
        root = APP / f"{catalog}.xcassets"
        metadata = {"author": "xcode", "version": 1}
        write_json(root / "Contents.json", {"info": metadata})
        path = root / "AppIcon.appiconset"
        export_icon(APP / "GalleonMaster.png", path / "AppIcon.png")
        write_json(path / "Contents.json", {"images": [{"filename": "AppIcon.png", "idiom": "universal", "platform": platform, "size": "1024x1024"}], "info": metadata})
        path = root / "GalleonMark.imageset"
        path.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / "AppIcon.appiconset/AppIcon.png", path / "GalleonMark.png")
        write_json(path / "Contents.json", {"images": [{"filename": "GalleonMark.png", "idiom": "universal"}], "info": metadata})


if __name__ == "__main__":
    make_audio()
    make_icons()
    print("Exported original music, fourteen distinct effects and iOS/watchOS icon catalogs.")
