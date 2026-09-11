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
        self.assertEqual(len(effects), 11)
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


if __name__ == "__main__": unittest.main()
