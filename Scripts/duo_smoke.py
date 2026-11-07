"""Exercise real Duo display transitions using idb's active-display accessibility route."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import time

BUNDLE = "com.sidneytambin.galleonaire"


class DuoCheck:
    def __init__(self, device, output, backend="ax"):
        self.device, self.output = device, Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.captures = []
        self.pid = None
        self.backend = backend
        self.poses = []

    def command(self, *args, timeout=60):
        result = subprocess.run(["idb", *args, "--udid", self.device], capture_output=True, text=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError(f"idb {args}: {result.stderr or result.stdout}")
        return result.stdout

    def tree(self):
        deadline = time.monotonic() + 180
        last_error = None
        foregrounded = False
        while time.monotonic() < deadline:
            try:
                return json.loads(self.command("ui", "describe-all", "--api", self.backend,
                                               "--client-type", "voiceOver", "--json"))
            except RuntimeError as error:
                if not any(message in str(error) for message in [
                    "display is still changing", "no frontmost application",
                    "retry the read", "frontmost returned no application object",
                ]):
                    raise
                last_error = error
                print("Waiting for the simulator's active display to become accessible.", flush=True)
                if not foregrounded and time.monotonic() > deadline - 150:
                    # Reactivate the existing process; never relaunch or reset the saved game.
                    result = subprocess.run(["idb", "launch", "--foreground-if-running", "--udid", self.device, BUNDLE],
                                            check=True, capture_output=True, text=True, timeout=60)
                    if json.loads(result.stdout)["pid"] != self.pid:
                        raise AssertionError("Galleonaire's process changed during display transition")
                    foregrounded = True
                time.sleep(3)
        raise RuntimeError("The simulator's active display never became ready") from last_error

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
        # AX includes off-screen SwiftUI list children. Presence does not imply
        # that their centre is inside the active display, especially at XXXL.
        for direction in ["down", "up"]:
            for _ in range(12):
                try:
                    self.command("ui", "tap", marker, "--match-key", key, "--depth", "40")
                    return
                except RuntimeError as error:
                    if "outside the display's point bounds" not in str(error):
                        raise
                    self.command("ui", "scroll", direction)
                    time.sleep(0.5)
        raise AssertionError(f"Accessible element could not be scrolled into view: {marker}")

    def fold(self, angle):
        print(f"Setting Duo hinge to {angle} degrees", flush=True)
        self.command("hinge", str(angle))
        deadline = time.monotonic() + 30
        previous = None
        while time.monotonic() < deadline:
            measurement = json.loads(self.command("hinge", "--json"))
            actual = measurement["angle"]
            print(f"Duo hinge read-back: requested {angle}, measured {actual}", flush=True)
            # The middle-pose check needs a stable partially open device, not
            # an exact sensor calibration. Closed and flat endpoints stay exact.
            settled_middle = angle == 90 and 30 <= actual <= 150 and previous is not None and abs(actual - previous) <= 1
            if abs(actual - angle) <= 0.5 or settled_middle:
                self.poses.append({"requestedAngle": angle, "measuredAngle": actual})
                time.sleep(3)  # The display switch settles after the hinge sensor reaches its target.
                return
            previous = actual
            time.sleep(2)
        raise AssertionError(f"Duo hinge did not reach {angle} degrees")

    def capture(self, name):
        path = self.output / (name + ".png")
        (self.output / (name + ".json")).write_text(json.dumps(self.tree(), indent=2))
        for attempt in range(2):
            try:
                self.command("screenshot", str(path))
                break
            except subprocess.TimeoutExpired:
                if attempt: raise
                print("Retrying the simulator screen capture after its service timed out.", flush=True)
                time.sleep(3)
        data = path.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n": raise AssertionError("Screen capture is not a PNG")
        size = struct.unpack(">II", data[16:24])
        if min(size) < 300: raise AssertionError("Screen capture has unexpected dimensions")
        self.captures.append({"name": name, "pixels": size})
        return size

    def launch(self, *args):
        # Launch takes the remaining arguments verbatim; --udid must precede the bundle.
        result = subprocess.run(["idb", "launch", "--udid", self.device, BUNDLE, *args],
                                check=True, capture_output=True, text=True, timeout=60)
        self.pid = json.loads(result.stdout)["pid"]
        print("Galleonaire process launched; waiting for its accessible interface.", flush=True)

    def statistics(self):
        for angle in [0, 180, 90]:
            self.fold(angle)
            accuracy = self.find("answerAccuracy", scroll=True)
            assert len(accuracy) == 1, "Accuracy appears as multiple accessibility stops"
            assert "73 correct out of 100 answered" in accuracy[0]["AXLabel"]
            self.capture(f"statistics-{angle}")

    def run(self, app, statistics_only=False):
        self.command("install", str(app), timeout=120)
        self.fold(0)
        if statistics_only:
            self.launch("--ui-testing", "--reset-test-game", "--legacy-statistics")
            self.tap("Statistics", "AXLabel")
            self.statistics()
            self.report(["normal-text statistics across closed, flat and intermediate poses",
                         "legacy statistics accuracy", "one accessible accuracy summary"])
            return
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
        self.statistics()
        self.report(["Classic display transition", "exam answer retention across folds",
                     "submission and result retention", "legacy statistics accuracy", "one accessible accuracy summary", "normal and largest text"])

    def report(self, checks):
        report = {"passed": True, "device": "iPhone Duo", "runtime": "27.2", "captures": self.captures,
                  "poses": self.poses,
                  "accessibilityBackend": self.backend,
                  "physicalVoiceOverTested": False, "checks": checks}
        (self.output / "duo-verification.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", required=True)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    DuoCheck(args.device, args.output).run(args.app)
