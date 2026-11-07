"""Exercise real Duo display transitions using idb's active-display accessibility route."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import time

BUNDLE = "com.sidneytambin.galleonaire"


class DuoCheck:
    def __init__(self, device, output):
        self.device, self.output = device, Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.captures = []

    def command(self, *args, timeout=60):
        result = subprocess.run(["idb", *args, "--udid", self.device], capture_output=True, text=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError(f"idb {args}: {result.stderr or result.stdout}")
        return result.stdout

    def tree(self):
        return json.loads(self.command("ui", "describe-all", "--json"))

    @staticmethod
    def nodes(value):
        if isinstance(value, dict):
            if "AXLabel" in value or "AXUniqueId" in value: yield value
            for child in value.values(): yield from DuoCheck.nodes(child)
        elif isinstance(value, list):
            for child in value: yield from DuoCheck.nodes(child)

    def find(self, marker, key="AXUniqueId", scroll=False):
        for direction in (["down", "up"] if scroll else [None]):
            for _ in range(12 if scroll else 3):
                matches = [node for node in self.nodes(self.tree()) if node.get(key) == marker]
                if matches: return matches
                if direction:
                    try: self.command("ui", "scroll", direction)
                    except RuntimeError: break  # The native list may already be at this edge; search the other direction.
                else: time.sleep(0.5)
        raise AssertionError(f"Accessible element is missing: {marker}")

    def tap(self, marker, key="AXUniqueId"):
        self.find(marker, key, scroll=True)
        self.command("ui", "tap", marker, "--match-key", key, "--depth", "40")

    def fold(self, angle):
        self.command("hinge", str(angle))
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            measurement = json.loads(self.command("hinge", "--json"))
            if abs(measurement["angle"] - angle) <= 0.5:
                time.sleep(3)  # The display switch settles after the hinge sensor reaches its target.
                return
        raise AssertionError(f"Duo hinge did not reach {angle} degrees")

    def capture(self, name):
        path = self.output / (name + ".png")
        self.command("screenshot", str(path))
        data = path.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n": raise AssertionError("Screen capture is not a PNG")
        size = struct.unpack(">II", data[16:24])
        if min(size) < 300: raise AssertionError("Screen capture has unexpected dimensions")
        (self.output / (name + ".json")).write_text(json.dumps(self.tree(), indent=2))
        self.captures.append({"name": name, "pixels": size})
        return size

    def launch(self, *args):
        # Launch takes the remaining arguments verbatim; --udid must precede the bundle.
        subprocess.run(["idb", "launch", "--udid", self.device, BUNDLE, *args], check=True, timeout=60)

    def run(self, app):
        self.command("install", str(app), timeout=120)
        self.fold(0)
        self.launch("--ui-testing", "--reset-test-game")
        self.tap("newGame")
        question = self.find("questionText")[0]["AXLabel"]
        outer = self.capture("classic-outer")
        self.fold(180)
        assert self.find("questionText", scroll=True)[0]["AXLabel"] == question
        inner = self.capture("classic-inner")
        assert outer != inner, "Folding did not change the active display geometry"

        self.command("terminate", BUNDLE)
        self.launch("--ui-testing", "--reset-test-game", "--exam-fixture-ready", "--legacy-statistics",
                    "-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL")
        self.tap("resumeExam")
        question = self.find("examQuestion")[0]["AXLabel"]
        assert question.startswith("Question 20 of 20")
        self.tap("examAnswer0")
        for angle in [0, 180, 90, 0]:
            self.fold(angle)
            assert self.find("examQuestion", scroll=True)[0]["AXLabel"] == question
            answer = self.find("examAnswer0", scroll=True)[0]
            assert answer.get("AXValue") == "Recorded answer", "Display transition discarded the recorded answer"
            self.capture(f"large-exam-{angle}")
        self.tap("submitExam")
        self.tap("Submit Saved Answers", "AXLabel")
        result = self.find("examResult")[0]["AXLabel"]
        assert "Outstanding. Pass" in result
        self.capture("large-result-outer")
        self.fold(180)
        assert self.find("examResult", scroll=True)[0]["AXLabel"] == result
        self.capture("large-result-inner")
        self.tap("closeExam")
        self.tap("Statistics", "AXLabel")
        for angle in [180, 0]:
            self.fold(angle)
            accuracy = self.find("answerAccuracy", scroll=True)
            assert len(accuracy) == 1, "Accuracy appears as multiple accessibility stops"
            assert "73 correct out of 100 answered" in accuracy[0]["AXLabel"]
            self.capture(f"large-statistics-{angle}")
        self.command("terminate", BUNDLE)
        self.launch("--ui-testing")
        self.tap("Statistics", "AXLabel")
        for angle in [0, 180, 90]:
            self.fold(angle)
            assert "73 correct out of 100 answered" in self.find("answerAccuracy", scroll=True)[0]["AXLabel"]
            self.capture(f"statistics-{angle}")
        report = {"passed": True, "device": "iPhone Duo", "runtime": "27.2", "captures": self.captures,
                  "physicalVoiceOverTested": False, "checks": ["Classic display transition", "exam answer retention across folds",
                  "submission and result retention", "legacy statistics accuracy", "one accessible accuracy summary", "normal and largest text"]}
        (self.output / "duo-verification.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", required=True)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    DuoCheck(args.device, args.output).run(args.app)
