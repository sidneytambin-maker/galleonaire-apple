"""Compile reviewed exam records without rewriting the original Classic bank.

The similarity report is an editorial aid, never a claim of semantic proof.
Release validation requires a reviewed resolution for every flagged new pair.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'Reference'
RES = ROOT / 'Apple/Sources/GalleonaireCore/Resources'
SUBJECTS = dict(zip('CSPTBEHOQF', ['characters', 'spells', 'potions', 'transformations', 'creatures',
    'education', 'history', 'objects', 'competitions', 'films']))

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def additions():
    sources = read(REF / 'exam-sources.json')
    rows = []
    for path in sorted(REF.glob('exam-additions*.csv')):
        with path.open(encoding='utf-8', newline='') as f:
            for row in csv.DictReader(f, delimiter='|'):
                assert None not in row and all(row.values()), (path, row)
                rows.append(row)
    result = []
    for row in rows:
        key = row['source']
        if key.startswith('jkr.'):
            slug = key[4:]
            source = ['J. K. Rowling: ' + slug.replace('-', ' ').title(),
                      'https://www.harrypotter.com/writing-by-jk-rowling/' + slug]
        elif key.startswith('hp.'):
            slug = key[3:]
            source = ['HarryPotter.com: ' + slug.replace('-', ' ').title(),
                      'https://www.harrypotter.com/features/' + slug]
        elif key.startswith(('lex.', 'thing.')):
            kind, slug = key.split('.', 1)
            source = ['Harry Potter Lexicon: ' + slug.replace('-', ' ').title() + ' (with book references)',
                      'https://www.hp-lexicon.org/' + ('magic' if kind == 'lex' else 'thing') + '/' + slug + '/']
        elif key.startswith('plant.'):
            slug = key[6:]
            source = ['Official Harry Potter Encyclopedia: ' + slug.replace('-', ' ').title(),
                      'https://www.harrypotter.com/fact-file/plants-and-potions/' + slug]
        elif key.startswith('book.'):
            match = re.fullmatch(r'book\.(ps|cs|pa|gf|op|hbp|dh)(\d+)', key)
            assert match, key
            book, chapter = match.groups()
            names = dict(ps="Philosopher's Stone", cs='Chamber of Secrets', pa='Prisoner of Azkaban',
                gf='Goblet of Fire', op='Order of the Phoenix', hbp='Half-Blood Prince', dh='Deathly Hallows')
            source = [f'J. K. Rowling: Harry Potter and the {names[book]}, chapter {chapter}; reference check: Harry Potter Lexicon',
                      f'https://www.hp-lexicon.org/source/the-harry-potter-novels/{book}/{book}{chapter}/']
        else:
            source = sources[key]
        answers = [row['correct'], row['wrong1'], row['wrong2'], row['wrong3']]
        rotation = int(hashlib.sha256(row['id'].encode()).hexdigest()[:8], 16) % 4
        answers = answers[rotation:] + answers[:rotation]
        q = dict(id=row['id'], level=int(row['level']), difficulty=int(row['level']), category=row['subject'],
                 text=row['question'], answers=answers, correctIndex=answers.index(row['correct']),
                 explanation=row['explanation'], source=source[0], sourceURL=source[1], factKey=row['fact'])
        result.append(dict(question=q, subject=row['subject'], difficulty='expert', conflictKeys=[row['fact']]))
    return result

def normalize(text):
    text = re.sub(r'In the \w+ book, Harry Potter and the [^,]+,', '', text, flags=re.I)
    return ' '.join(re.findall(r'[a-z0-9]+', text.lower()))

def similarity(originals, added):
    all_questions = originals + [i['question'] for i in added]
    stop = set('the a an of in on to and which what who how does did is was were for with according rowling harry potter book film'.split())
    stems = [normalize(q['text']) for q in all_questions]
    tokens = [set(s.split()) - stop for s in stems]
    flags = []
    for right in range(len(originals), len(all_questions)):
        for left in range(right):
            a, b = all_questions[left], all_questions[right]
            intersection = tokens[left] & tokens[right]
            union = tokens[left] | tokens[right]
            similarity = len(intersection) / max(1, len(union))
            answer_a = normalize(a['answers'][a['correctIndex']])
            answer_b = normalize(b['answers'][b['correctIndex']])
            reasons = []
            if a.get('factKey') == b['factKey']: reasons.append('same fact key')
            if similarity >= .48 or (len(intersection) >= 3 and SequenceMatcher(None, stems[left], stems[right]).ratio() >= .76):
                reasons.append('similar wording or concepts')
            if answer_a == answer_b and len(intersection) >= 2:
                reasons.append('same answer and related stem')
            if len(intersection) >= 2 and any(len(ans.split()) >= 2 and ans in stem for ans, stem in
                [(answer_a, stems[right]), (answer_b, stems[left])]):
                reasons.append('possible answer disclosure')
            if reasons:
                flags.append(dict(pair='|'.join(sorted([a['id'], b['id']])), reasons=reasons,
                    first=a['text'] + ' → ' + a['answers'][a['correctIndex']],
                    second=b['text'] + ' → ' + b['answers'][b['correctIndex']]))
    return flags

def compile_bank(require_complete=True, check=False):
    originals = read(RES / 'questions.json')['questions']
    corrections = read(REF / 'classic-source-corrections.json')
    assert set(corrections).issubset({q['id'] for q in originals})
    assert all(set(patch).issubset({'text', 'explanation', 'source', 'sourceURL'}) for patch in corrections.values())
    corrected = [{**q, **corrections[q['id']]} for q in originals if q['id'] in corrections]
    originals = [{**q, **corrections.get(q['id'], {})} for q in originals]
    classifications = read(REF / 'exam-classifications.json')
    assert len(originals) == len(classifications) == 1000
    assert {q['id'] for q in originals} == {c['questionID'] for c in classifications}
    by_id = {q['id']: q for q in originals}
    added = additions()
    items = [dict(question=by_id[c['questionID']], subject=c['subject'], difficulty=c['difficulty'],
                  conflictKeys=c.get('conflictKeys', [by_id[c['questionID']]['factKey']]))
             for c in classifications if c['eligible']]
    items += added
    all_q = originals + [i['question'] for i in added]
    assert len({q['id'] for q in all_q}) == len(all_q), 'Duplicate ID'
    assert len({normalize(q['text']) for q in all_q}) == len(all_q), 'Duplicate question'
    assert len({q['factKey'] for q in all_q}) == len(all_q), 'Duplicate fact key'
    for q in all_q:
        assert len(q['answers']) == len(set(map(normalize, q['answers']))) == 4, q['id']
        assert 0 <= q['correctIndex'] < 4 and q['explanation'] and q['source'], q['id']
        if q['id'].startswith('ex_'): assert q['sourceURL'].startswith('https://'), q['id']
    coverage = []
    for subject in SUBJECTS.values():
        counts = Counter(i['difficulty'] for i in items if i['subject'] == subject)
        coverage.append(dict(subject=subject, original=sum(c['subject'] == subject for c in classifications),
            added=sum(i['subject'] == subject for i in added), intermediate=counts['intermediate'], expert=counts['expert']))
        if require_complete:
            assert counts['intermediate'] >= 20 and counts['expert'] >= 50, coverage[-1]
        for difficulty in ['intermediate', 'expert']:
            keys = [k for i in items if i['subject'] == subject and i['difficulty'] == difficulty for k in i['conflictKeys']]
            assert len(keys) == len(set(keys)), (subject, difficulty, 'conflicts')
    flags = similarity(originals, added)
    if not check: write(REF / 'exam-similarity-candidates.json', flags)
    decisions_path = REF / 'exam-similarity-review.json'
    decisions = read(decisions_path) if decisions_path.exists() else {}
    if require_complete:
        unresolved = [f['pair'] for f in flags if not decisions.get(f['pair'], '').strip()]
        assert not unresolved, f'Unresolved editorial comparisons: {unresolved}'
    bank = dict(schemaVersion=1, classifications=classifications, items=items, classicCorrections=corrected)
    if require_complete:
        if check:
            assert read(RES / 'exam-bank.json') == bank, 'Generated exam bank is stale'
            assert read(REF / 'exam-coverage.json') == coverage, 'Coverage table is stale'
        else:
            write(RES / 'exam-bank.json', bank)
    if not check: write(REF / 'exam-coverage.json', coverage)
    # Every pool is pairwise compatible, so every possible full-size subset is safe.
    # Exercise deterministic selection and answer permutations for all twenty papers too.
    import random
    for subject in SUBJECTS.values():
        for difficulty, size in [('intermediate', 20), ('expert', 50)]:
            pool = [i for i in items if i['subject'] == subject and i['difficulty'] == difficulty]
            if len(pool) < size: continue
            rng = random.Random(6706)
            paper = rng.sample(pool, size)
            assert len({i['question']['id'] for i in paper}) == size
            assert len({k for i in paper for k in i['conflictKeys']}) == sum(len(i['conflictKeys']) for i in paper)
            for item in paper:
                order = rng.sample(range(4), 4)
                assert sorted(order) == list(range(4)) and order.count(item['question']['correctIndex']) == 1
    print(json.dumps(coverage, indent=2))
    print(f'{len(added)} additions; {len(flags)} editorial comparisons')
    return bank

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--draft', action='store_true', help='Report unfinished coverage; never write a shipping bank')
    parser.add_argument('--check', action='store_true', help='Validate without rewriting generated resources')
    args = parser.parse_args()
    compile_bank(require_complete=not args.draft, check=args.check)
