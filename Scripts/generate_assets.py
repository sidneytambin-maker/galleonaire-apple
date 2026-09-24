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
    for i in range(int(2.8 * RATE)):
        t = i / RATE
        impact = .7 * math.sin(2 * math.pi * (68 * t + 22 * (1 - math.exp(-t * 12)))) * math.exp(-t * 5)
        brass = 0
        for onset, frequency in [(0, 174.61), (.38, 155.56), (.76, 130.81)]:
            dt = t - onset
            if dt >= 0:
                envelope = min(1, dt / .035) * math.exp(-dt * 2.3)
                phase = 2 * math.pi * frequency * dt
                brass += .22 * envelope * (math.sin(phase) + .22 * math.sin(3 * phase))
        tail = .16 * math.sin(2 * math.pi * 65.41 * t) * math.exp(-t * 1.5)
        samples.append((impact + brass + tail) * min(1, t / .004) * min(1, (2.8 - t) / .25))
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


def make_victory():
    # Original major-key fanfare, layered bells, timpani and synthesized applause; no sampled music.
    duration = 6.6
    samples = [0.0] * int(duration * RATE)
    melody = [(0, 72, .42), (.45, 72, .20), (.70, 76, .34), (1.10, 79, .40),
              (1.55, 84, .75), (2.40, 81, .35), (2.80, 83, .35), (3.20, 84, 2.8)]
    voices = [(onset, note, length, .23, True) for onset, note, length in melody]
    for onset, chord in [(0, [48, 55, 60, 64]), (1.55, [53, 60, 65, 69]), (2.8, [55, 62, 67, 71]), (3.2, [48, 55, 60, 64, 67])]:
        voices.extend((onset, note, 2.6, .085, False) for note in chord)
    voices.extend((3.25 + i * .13, note, 1.4, .12, False) for i, note in enumerate([84, 88, 91, 96, 100, 103]))
    for onset, note, length, amplitude, brass in voices:
        frequency = 440 * 2 ** ((note - 69) / 12)
        for offset in range(min(int(length * RATE), len(samples) - int(onset * RATE))):
            t = offset / RATE
            phase = 2 * math.pi * frequency * t
            tone = math.sin(phase) + (0.32 if brass else 0.13) * math.sin(2 * phase) + .1 * math.sin(3 * phase)
            envelope = min(1, t / .025) * min(1, (length - t) / .2) * math.exp(-t * (1.4 if brass else .9))
            samples[int(onset * RATE) + offset] += amplitude * envelope * tone
    rng = random.Random('galleonaire-million-galleon-celebration')
    for onset in [.0, .7, 1.55, 2.8, 3.2]:
        for offset in range(int(.45 * RATE)):
            t = offset / RATE
            samples[int(onset * RATE) + offset] += .3 * math.sin(2 * math.pi * (62 * t + 1.6 * (1 - math.exp(-t * 30)))) * math.exp(-t * 10) * min(1, t / .002)
    for onset in sorted(rng.uniform(3.45, 5.85) for _ in range(70)):
        previous = 0
        for offset in range(int(.14 * RATE)):
            t = offset / RATE
            raw = rng.uniform(-1, 1)
            high = raw - previous
            previous = .7 * previous + .3 * raw
            samples[int(onset * RATE) + offset] += .1 * high * math.exp(-t * 40) * min(1, t / .002)
    dry = samples.copy()
    for delay, gain in [(.11, .18), (.23, .10), (.37, .06)]:
        offset = int(delay * RATE)
        for i in range(offset, len(samples)): samples[i] += dry[i - offset] * gain
    write_audio('victory', samples)


def make_audio():
    from compose_soundtrack import compose
    compose()
    events = {
        "selected": (.18, [(0, 84, .17, .40)], 0),
        "locked": (.38, [(0, 48, .16, .38), (.08, 60, .28, .35)], .25),
        "correct": (.95, [(0, 84, .32, .40), (.13, 88, .32, .40), (.26, 91, .65, .38), (.26, 84, .65, .22)], 0),
        "lifelineSelected": (.26, [(0, 81, .22, .32), (.055, 88, .20, .18)], 0),
        "lifelineActivated": (.62, [(0, 60, .4, .22), (.12, 67, .38, .24), (.24, 86, .35, .3)], .5),
        "lifelineResult": (.45, [(0, 79, .25, .3), (.15, 84, .29, .3)], 0),
        "nextQuestion": (.52, [(0, 55, .25, .18), (.15, 74, .32, .24)], .25),
        "finalQuestion": (1.8, [(0, 43, 1.7, .18), (0, 50, 1.7, .14), (.2, 67, 1.4, .20), (.55, 74, 1.1, .24), (.9, 81, .8, .24)], .03),
        "milestone": (1.05, [(0, 60, .7, .22), (0, 64, .7, .22), (.18, 79, .65, .28), (.40, 84, .6, .28)], 0),
        "majorMilestone": (1.45, [(0, 48, 1, .2), (0, 55, 1, .2), (.2, 72, .7, .3), (.4, 76, .7, .3), (.6, 84, .8, .3)], .06),
        "victory": (2.0, [(0, 48, 1.6, .18), (0, 60, 1.5, .18), (.12, 72, .4, .25), (.3, 76, .4, .25), (.5, 79, .4, .25), (.7, 84, 1.2, .28), (.7, 88, 1.2, .18)], 0),
    }
    for name, (duration, notes, noise) in events.items(): render_audio(name, duration, notes, noise)
    make_character_effects()
    make_victory()


def make_scene_assets():
    for catalog in ('Assets', 'WatchAssets'):
        path = APP / (catalog + '.xcassets') / 'QuizChamber.imageset'
        path.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(APP / 'QuizChamber.png', path / 'QuizChamber.png')
        write_json(path / 'Contents.json', {'images': [{'filename': 'QuizChamber.png', 'idiom': 'universal'}], 'info': {'author': 'xcode', 'version': 1}})


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
    make_scene_assets()
    print("Exported original music, fifteen distinct effects and iOS/watchOS icon catalogs.")
