"""Migrate the original structured bank without modifying the handheld game."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def migrate(source):
    raw = source.read_bytes()
    original = json.loads(raw.decode("utf-8-sig"))
    questions = []
    for item in original["questions"]:
        questions.append({
            "id": item["id"], "level": item["prize_level"],
            "difficulty": item["difficulty"], "category": item["category"],
            "text": item["question_text"],
            "answers": [item[f"answer_{key}"] for key in "abcd"],
            "correctIndex": "ABCD".index(item["correct_answer"]),
            "explanation": item["explanation"], "source": item["source_note"],
        })
    bank = {"schemaVersion": 1, "ladder": original["ladder"], "questions": questions}
    validate(bank)
    reference = ROOT / "Reference"
    reference.mkdir(exist_ok=True)
    (reference / "original-questions.json").write_bytes(raw)
    destination = ROOT / "Apple/Sources/GalleonaireCore/Resources"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "questions.json").write_text(json.dumps(bank, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    (reference / "provenance.json").write_text(json.dumps({
        "source": str(source), "sha256": hashlib.sha256(raw).hexdigest(),
        "questionCount": len(questions), "migration": "Same IDs, question text, choices, correct answers and sources. No recorded speech or user saves imported."
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Migrated and validated {len(questions)} questions across 15 levels.")


def validate(bank):
    assert bank["schemaVersion"] == 1
    assert bank["ladder"] == [100, 200, 300, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000, 125000, 250000, 500000, 1000000]
    ids, texts = set(), set()
    counts = [0] * 15
    for item in bank["questions"]:
        assert item["id"] not in ids, f"Duplicate ID {item['id']}"
        ids.add(item["id"])
        text = " ".join(item["text"].casefold().split())
        assert text and text not in texts, f"Duplicate question {item['id']}"
        texts.add(text)
        answers = [" ".join(a.casefold().split()) for a in item["answers"]]
        assert len(answers) == 4 and len(set(answers)) == 4 and all(answers), item["id"]
        assert 0 <= item["correctIndex"] < 4 and 1 <= item["level"] <= 15, item["id"]
        assert item["explanation"] and item["source"], item["id"]
        counts[item["level"] - 1] += 1
    assert min(counts) >= 2, "Each level needs a distinct Free Pass replacement"
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", type=Path)
    args = parser.parse_args()
    if args.source:
        migrate(args.source)
    else:
        counts = validate(json.loads((ROOT / "Apple/Sources/GalleonaireCore/Resources/questions.json").read_text(encoding="utf-8")))
        print(f"Question bank valid: {sum(counts)} questions; level counts {counts}")
