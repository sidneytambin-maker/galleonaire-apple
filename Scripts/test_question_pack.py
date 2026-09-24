import copy
import hashlib
import unittest
from collections import Counter

import question_pack as pack


class QuestionPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = pack.build_pack()

    def test_exact_counts_and_stable_original_ids(self):
        self.assertEqual(len(self.bank["questions"]), 750)
        self.assertEqual(Counter(q["level"] for q in self.bank["questions"]), {i: 50 for i in range(1, 16)})
        original = pack.read_json(pack.REFERENCE / "original-questions.json")
        self.assertTrue({q["id"] for q in original["questions"]} <= {q["id"] for q in self.bank["questions"]})

    def test_exactly_ten_new_questions_at_every_level(self):
        rows = pack.editorial_rows("question-additions-750.csv")
        self.assertEqual(len(rows), 150)
        self.assertEqual(Counter(int(r["id"][3:5]) for r in rows), {i: 10 for i in range(1, 16)})

    def test_dobby_and_adaptation_context_is_explicit(self):
        questions = {q["id"]: q for q in self.bank["questions"]}
        dobby = questions["ga_05_07"]
        self.assertIn("fourth book, Harry Potter and the Goblet of Fire", dobby["text"])
        for phrase in ["Dobby", "Neville", "2005"]:
            self.assertIn(phrase, dobby["explanation"])
        for qid, title in [("ga_07_13", "Harry Potter and the Order of the Phoenix"), ("ga_14_09", "Harry Potter and the Deathly Hallows"), ("ga_15_02", "Harry Potter and the Deathly Hallows")]:
            self.assertIn(title, questions[qid]["text"])
            self.assertNotIn("in the book?", questions[qid]["text"])

    def test_year_ranges_are_written_for_speech(self):
        import re
        for q in self.bank["questions"]:
            for text in [q["text"], q["explanation"], q["source"], *q["answers"]]:
                self.assertIsNone(re.search(r"\d{4}\s*[/–—-]\s*\d{4}", text), q["id"])
        question = next(q for q in self.bank["questions"] if q["id"] == "ga_02_10")
        self.assertIn("from 2001 until 2011", question["text"])

    def test_expansion_has_exact_book_context_and_unique_facts(self):
        questions = {q["id"]: q for q in self.bank["questions"]}
        for row in pack.editorial_rows("question-additions-750.csv"):
            q = questions[row["id"]]
            ordinal, title = pack.BOOKS[row["book"]]
            self.assertIn(f"{ordinal} book, {title}", q["text"])
            self.assertIn(f"{ordinal} book, {title}", q["explanation"])
            self.assertEqual(q["answers"][q["correctIndex"]], row["correct"])
            self.assertEqual(q["sourceURL"], row["sourceURL"])

    def test_existing_facts_keep_ids_and_have_migration_provenance(self):
        previous = self.bank["previousLevels"]
        self.assertEqual(len(previous), 600)
        for qid, level in previous.items():
            self.assertEqual(int(qid[3:5]), level)
        decisions = pack.read_json(pack.REFERENCE / "question-difficulty-review.json")["questions"]
        self.assertEqual(Counter(r["level"] for r in decisions), {i: 40 for i in range(1, 16)})
        questions = {q["id"]: q for q in self.bank["questions"]}
        for decision in decisions:
            self.assertEqual(questions[decision["id"]]["level"], decision["level"])
        # Familiar plot facts must not reappear in the two expert pools.
        for qid in ["ga_14_09", "ga_14_16", "ga_14_20", "ga_15_01", "ga_15_04", "ga_15_16", "ga_15_40"]:
            self.assertLess(questions[qid]["level"], 14)

    def test_spoken_choices_do_not_depend_on_homophone_spellings(self):
        question = next(q for q in self.bank["questions"] if q["id"] == "ga_15_38")
        self.assertEqual(question["factKey"], "trelawney.surname.song")
        self.assertNotIn("Sibyl", question["answers"])
        for q in self.bank["questions"]:
            self.assertTrue(q["text"].endswith("?"), q["id"])
            self.assertEqual(len(q["answers"]), 4)

    def test_original_reference_hash_is_unchanged(self):
        original = pack.REFERENCE / "original-questions.json"
        expected = pack.read_json(pack.REFERENCE / "provenance.json")["sha256"]
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), expected)

    def test_bundled_bank_is_reproducible(self):
        self.assertEqual(pack.DESTINATION.read_bytes(), pack.encoded(self.bank))
        self.assertEqual(pack.encoded(pack.build_pack()), pack.encoded(self.bank))

    def test_rephrased_duplicate_fact_is_rejected(self):
        altered = copy.deepcopy(self.bank)
        altered["questions"][1]["factKey"] = altered["questions"][0]["factKey"]
        with self.assertRaisesRegex(AssertionError, "Repeated underlying facts"):
            pack.validate_editorial(altered)

    def test_every_addition_and_replacement_has_a_traceable_source(self):
        rows = pack.editorial_rows("question-additions.csv") + pack.editorial_rows("question-additions-600.csv") + pack.editorial_rows("question-replacements.csv")
        questions = {q["id"]: q for q in self.bank["questions"]}
        sources = pack.read_json(pack.REFERENCE / "question-sources.json")["sources"]
        for row in rows:
            question = questions[row["id"]]
            changes = pack.read_json(pack.REFERENCE / "question-polish-750.json").get(row["id"], {}).get("changes", {})
            self.assertEqual(question["sourceURL"], changes.get("sourceURL", sources[row["source"]]))
            expected_answer = changes.get("answers", question["answers"])[question["correctIndex"]]
            if "answers" not in changes:
                expected_answer = row["correct"]
            self.assertEqual(question["answers"][question["correctIndex"]], expected_answer)
            self.assertEqual(question["factKey"], changes.get("factKey", row["fact"]))

    def test_source_derived_question_wording_stays_brief(self):
        words = Counter()
        rows = pack.editorial_rows("question-additions.csv") + pack.editorial_rows("question-additions-600.csv") + pack.editorial_rows("question-replacements.csv")
        for row in rows:
            words[row["source"]] += sum(len(row[field].split()) for field in ["question", "correct", "explanation"])
        for source, count in words.items():
            self.assertLessEqual(count, 200, f"Source {source}: {count} derived words")

    def test_correct_answers_do_not_always_occupy_one_button(self):
        added = [q for q in self.bank["questions"] if int(q["id"][-2:]) >= 21]
        counts = Counter(q["correctIndex"] for q in added)
        self.assertEqual(set(counts), {0, 1, 2, 3})
        self.assertTrue(all(85 <= count <= 145 for count in counts.values()))

    def test_canonical_and_ambiguous_question_regressions(self):
        questions = {q["id"]: q for q in self.bank["questions"]}
        self.assertNotIn("Protean", questions["ga_07_09"]["text"])
        self.assertNotIn("Slytherin's ring", questions["ga_13_17"]["answers"])
        self.assertIn("orders Kreacher", questions["ga_12_03"]["text"])
        self.assertIn("book", questions["ga_07_08"]["text"])
        self.assertIn("film Harry Potter and the Order of the Phoenix (2007)", questions["ga_07_10"]["text"])
        self.assertNotIn("Selkies from the Black Lake", questions["ga_05_17"]["answers"])
        self.assertIn("revisit stored memories", questions["ga_04_01"]["text"])
        self.assertEqual(questions["ga_12_13"]["answers"][questions["ga_12_13"]["correctIndex"]], "Gemino and Flagrante")
        self.assertEqual(len({q["factKey"] for q in self.bank["questions"]}), 750)


if __name__ == "__main__":
    unittest.main()
