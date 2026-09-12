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
        self.assertEqual(len(self.bank["questions"]), 450)
        self.assertEqual(Counter(q["level"] for q in self.bank["questions"]), {i: 30 for i in range(1, 16)})
        original = pack.read_json(pack.REFERENCE / "original-questions.json")
        self.assertTrue({q["id"] for q in original["questions"]} <= {q["id"] for q in self.bank["questions"]})

    def test_exactly_ten_new_questions_at_every_level(self):
        rows = pack.editorial_rows("question-additions.csv")
        self.assertEqual(len(rows), 150)
        self.assertEqual(Counter(int(r["id"][3:5]) for r in rows), {i: 10 for i in range(1, 16)})

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
        rows = pack.editorial_rows("question-additions.csv") + pack.editorial_rows("question-replacements.csv")
        questions = {q["id"]: q for q in self.bank["questions"]}
        sources = pack.read_json(pack.REFERENCE / "question-sources.json")["sources"]
        for row in rows:
            question = questions[row["id"]]
            self.assertEqual(question["sourceURL"], sources[row["source"]])
            self.assertEqual(question["answers"][question["correctIndex"]], row["correct"])
            self.assertEqual(question["factKey"], row["fact"])

    def test_source_derived_question_wording_stays_brief(self):
        words = Counter()
        rows = pack.editorial_rows("question-additions.csv") + pack.editorial_rows("question-replacements.csv")
        for row in rows:
            words[row["source"]] += sum(len(row[field].split()) for field in ["question", "correct", "explanation"])
        for source, count in words.items():
            self.assertLessEqual(count, 200, f"Source {source}: {count} derived words")

    def test_correct_answers_do_not_always_occupy_one_button(self):
        added = [q for q in self.bank["questions"] if int(q["id"][-2:]) >= 21]
        counts = Counter(q["correctIndex"] for q in added)
        self.assertEqual(set(counts), {0, 1, 2, 3})
        self.assertTrue(all(20 <= count <= 60 for count in counts.values()))

    def test_canonical_and_ambiguous_question_regressions(self):
        questions = {q["id"]: q for q in self.bank["questions"]}
        self.assertNotIn("Protean", questions["ga_07_09"]["text"])
        self.assertNotIn("Slytherin's ring", questions["ga_13_17"]["answers"])
        self.assertIn("orders Kreacher", questions["ga_12_03"]["text"])
        self.assertIn("book", questions["ga_07_08"]["text"])
        self.assertIn("films", questions["ga_07_10"]["text"])
        self.assertNotIn("Selkies from the Black Lake", questions["ga_05_17"]["answers"])
        self.assertIn("revisit stored memories", questions["ga_04_01"]["text"])
        self.assertEqual(questions["ga_12_13"]["answers"][questions["ga_12_13"]["correctIndex"]], "Gemino and Flagrante")
        self.assertEqual(len({q["factKey"] for q in self.bank["questions"]}), 450)


if __name__ == "__main__":
    unittest.main()
