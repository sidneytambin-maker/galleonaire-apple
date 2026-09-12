"""Check the shipped media itself; device listening remains a separate test."""
import hashlib
import json
import struct
import unittest
import wave
from pathlib import Path

from release import AUDIO

APP = Path(__file__).resolve().parents[1] / "Apple/App"


class AssetTests(unittest.TestCase):
    def test_both_icons_are_opaque_1024_pixel_rgb(self):
        for catalog, platform in [("Assets", "ios"), ("WatchAssets", "watchos")]:
            with self.subTest(platform=platform):
                folder = APP / (catalog + ".xcassets") / "AppIcon.appiconset"
                metadata = json.loads((folder / "Contents.json").read_text())
                self.assertEqual(metadata["images"][0]["platform"], platform)
                data = (folder / metadata["images"][0]["filename"]).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(data[12:16], b"IHDR")
                width, height, depth, color = struct.unpack(">IIBB", data[16:26])
                self.assertEqual((width, height, depth, color), (1024, 1024, 8, 2))

    def test_every_event_has_a_different_recording(self):
        effects = [name for name in AUDIO if name != "magical-library"]
        fingerprints = {hashlib.sha256((APP / "Audio" / (name + ".wav")).read_bytes()).hexdigest() for name in effects}
        self.assertEqual(len(effects), 14)
        self.assertEqual(len(fingerprints), len(effects))

    def test_audio_is_non_silent_unclipped_pcm_with_bounded_duration(self):
        for name in AUDIO:
            with self.subTest(name=name), wave.open(str(APP / "Audio" / (name + ".wav"))) as audio:
                self.assertEqual((audio.getnchannels(), audio.getsampwidth(), audio.getcomptype()), (1, 2, "NONE"))
                self.assertEqual(audio.getframerate(), 22050)
                duration = audio.getnframes() / audio.getframerate()
                self.assertGreater(duration, 0.1)
                self.assertLessEqual(duration, 24 if name == "magical-library" else 2.0)
                samples = [value[0] for value in struct.iter_unpack("<h", audio.readframes(audio.getnframes()))]
                peak = max(map(abs, samples))
                self.assertGreater(peak, 100)
                self.assertLess(peak, 32767)

    def test_correct_and_incorrect_use_contrasting_frequency_ranges(self):
        crossings = {}
        for name in ("correct", "incorrect"):
            with wave.open(str(APP / "Audio" / (name + ".wav"))) as audio:
                samples = [v[0] for v in struct.iter_unpack("<h", audio.readframes(audio.getnframes()))]
            crossings[name] = sum(a < 0 <= b or b < 0 <= a for a, b in zip(samples, samples[1:])) / (len(samples) / 22050)
        self.assertGreater(crossings["correct"], 4 * crossings["incorrect"])

    def test_runtime_events_all_have_packaged_audio(self):
        import re
        source = (APP / "GameFeedback.swift").read_text()
        events = re.search(r"enum FeedbackEvent: String, CaseIterable \{\s+case ([^\n]+)", source).group(1).split(", ")
        for event in events:
            self.assertIn(event, AUDIO)
            self.assertTrue((APP / "Audio" / (event + ".wav")).is_file())


if __name__ == "__main__": unittest.main()
