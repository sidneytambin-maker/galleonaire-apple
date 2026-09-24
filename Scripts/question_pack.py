"""Rebuild the reviewed bank from immutable provenance and explicit editorial changes."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from urllib.parse import urlparse

from migrate_questions import ROOT, validate

REFERENCE = ROOT / "Reference"
DESTINATION = ROOT / "Apple/Sources/GalleonaireCore/Resources/questions.json"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def editorial_rows(name):
    with (REFERENCE / name).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="|"))
    for row in rows:
        assert None not in row and all(row.values()), f"Incomplete editorial row: {row}"
        assert re.fullmatch(r"ga_(0[1-9]|1[0-5])_(0[1-9]|[1-4][0-9]|50)", row["id"]), row["id"]
    assert len({r["id"] for r in rows}) == len(rows), "Repeated editorial ID"
    return rows


def source_title(url):
    path = urlparse(url).path
    title = path.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").title()
    if "/writing-by-jk-rowling/" in path:
        return f"J. K. Rowling archive: {title}"
    if "wbstudiotour.co.uk" in url:
        return f"Warner Bros. Studio Tour: {title}"
    return f"Official Harry Potter: {title}"


def make_question(row, sources):
    qid = row["id"]
    level = int(qid[3:5])
    url = sources[row["source"]]
    assert urlparse(url).scheme == "https"
    assert urlparse(url).hostname in {"www.harrypotter.com", "www.wbstudiotour.co.uk"}
    correct = hashlib.sha256(qid.encode("ascii")).digest()[0] % 4
    answers = [row[f"wrong{i}"] for i in range(1, 4)]
    answers.insert(correct, row["correct"])
    return {
        "id": qid, "level": level, "difficulty": level,
        "category": row["category"], "text": row["question"],
        "answers": answers, "correctIndex": correct,
        "explanation": row["explanation"], "source": source_title(url),
        "sourceURL": url, "factKey": row["fact"],
    }



BOOKS = {
    "ps": ("first", "Harry Potter and the Philosopher's Stone"),
    "cs": ("second", "Harry Potter and the Chamber of Secrets"),
    "pa": ("third", "Harry Potter and the Prisoner of Azkaban"),
    "gf": ("fourth", "Harry Potter and the Goblet of Fire"),
    "op": ("fifth", "Harry Potter and the Order of the Phoenix"),
    "hbp": ("sixth", "Harry Potter and the Half-Blood Prince"),
    "dh": ("seventh", "Harry Potter and the Deathly Hallows"),
}


def make_novel_question(row):
    qid = row["id"]
    level = int(qid[3:5])
    ordinal, title = BOOKS[row["book"]]
    chapter = int(row["chapter"])
    assert 1 <= chapter <= 38
    url = row["sourceURL"]
    assert urlparse(url).scheme == "https"
    assert urlparse(url).hostname in {"www.hp-lexicon.org", "www.harrypotter.com"}
    position = hashlib.sha256(qid.encode("ascii")).digest()[0] % 4
    answers = [row[f"wrong{i}"] for i in range(1, 4)]
    answers.insert(position, row["correct"])
    return {
        "id": qid, "level": level, "difficulty": level,
        "category": row["category"], "text": row["question"],
        "answers": answers, "correctIndex": position,
        "explanation": row["explanation"],
        "source": f"The {ordinal} book, {title}, chapter {chapter}.",
        "sourceURL": url, "factKey": row["fact"],
    }


def validate_editorial(bank):
    assert validate(bank) == [50] * 15, "The released bank must contain 50 questions at every level"
    facts = [q["factKey"] for q in bank["questions"]]
    duplicates = [key for key, count in Counter(facts).items() if count > 1]
    assert not duplicates, f"Repeated underlying facts: {duplicates}"
    assert all(re.fullmatch(r"[a-z0-9]+(?:\.[a-z0-9]+)+", key) for key in facts)
    assert all(q["level"] == q["difficulty"] for q in bank["questions"])


def build_pack():
    original_path = REFERENCE / "original-questions.json"
    expected_hash = read_json(REFERENCE / "provenance.json")["sha256"]
    assert hashlib.sha256(original_path.read_bytes()).hexdigest() == expected_hash, "Original provenance changed"
    original = read_json(original_path)
    facts = read_json(REFERENCE / "legacy-question-facts.json")
    assert set(facts) == {str(i) for i in range(1, 16)} and all(len(v) == 20 for v in facts.values())
    questions = {}
    for item in original["questions"]:
        qid = item["id"]
        level = item["prize_level"]
        questions[qid] = {
            "id": qid, "level": level, "difficulty": item["difficulty"],
            "category": item["category"], "text": item["question_text"],
            "answers": [item[f"answer_{key}"] for key in "abcd"],
            "correctIndex": "ABCD".index(item["correct_answer"]),
            "explanation": item["explanation"], "source": item["source_note"],
            "factKey": facts[str(level)][int(qid[-2:]) - 1],
        }
    original_ids = set(questions)
    assert len(original_ids) == 300
    sources = read_json(REFERENCE / "question-sources.json")["sources"]
    for row in editorial_rows("question-replacements.csv"):
        assert row["id"] in original_ids, "A replacement must retain an original ID"
        questions[row["id"]] = make_question(row, sources)
    for qid, changes in read_json(REFERENCE / "question-clarifications.json").items():
        assert qid in original_ids and set(changes) <= {"text", "answers", "explanation", "source"}
        questions[qid].update(changes)
    additions = editorial_rows("question-additions.csv")
    expected_new = {f"ga_{level:02}_{number:02}" for level in range(1, 16) for number in range(21, 31)}
    assert {r["id"] for r in additions} == expected_new and len(additions) == 150
    for row in additions:
        assert row["id"] not in questions
        questions[row["id"]] = make_question(row, sources)
    assert set(questions) - original_ids == expected_new and original_ids <= set(questions)
    expansion = editorial_rows("question-additions-600.csv")
    expected_expansion = {f"ga_{level:02}_{number:02}" for level in range(1, 16) for number in range(31, 41)}
    assert {r["id"] for r in expansion} == expected_expansion and len(expansion) == 150
    for row in expansion:
        assert row["id"] not in questions
        questions[row["id"]] = make_question(row, sources)
    for qid, changes in read_json(REFERENCE / "question-context-clarifications.json").items():
        assert qid in questions and set(changes) <= {"text", "answers", "explanation", "source"}
        questions[qid].update(changes)
    previous_levels = {qid: q["level"] for qid, q in questions.items()}
    review = read_json(REFERENCE / "question-difficulty-review.json")
    assert review["status"] == "reviewed", "Difficulty review is not complete"
    assignments = {r["id"]: r for r in review["questions"]}
    assert set(assignments) == set(questions) and len(assignments) == 600
    for qid, row in assignments.items():
        assert row["previousLevel"] == questions[qid]["level"] and row["reason"]
        questions[qid].update(level=row["level"], difficulty=row["level"])
    for qid, edit in read_json(REFERENCE / "question-polish-750.json").items():
        assert qid in questions and edit["reason"]
        assert set(edit["changes"]) <= {"text", "answers", "explanation", "source", "sourceURL", "factKey"}
        questions[qid].update(edit["changes"])
    final_additions = editorial_rows("question-additions-750.csv")
    expected_final = {f"ga_{level:02}_{number:02}" for level in range(1, 16) for number in range(41, 51)}
    assert len(final_additions) == 150 and {r["id"] for r in final_additions} == expected_final
    for row in final_additions:
        assert row["id"] not in questions
        questions[row["id"]] = make_novel_question(row)
    bank = {"schemaVersion": 1, "contentRevision": 2, "previousLevels": previous_levels,
            "ladder": original["ladder"], "questions": [questions[k] for k in sorted(questions)]}
    validate_editorial(bank)
    return bank


def encoded(bank):
    return (json.dumps(bank, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def check_pack():
    bank = build_pack()
    assert DESTINATION.read_bytes() == encoded(bank), "Bundled questions are stale; rebuild the reviewed pack"
    return bank


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    bank = build_pack()
    if args.write:
        DESTINATION.write_bytes(encoded(bank))
    else:
        check_pack()
    print("Reviewed pack: 750 questions, 50 per level, 150 new additions, all previous IDs retained.")
