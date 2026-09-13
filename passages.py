"""Deterministic passage extraction and original-parent association. MIT."""
import hashlib
import re

VERSION = '2.0.0'
SLOTS = 256

def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z][a-z]|[A-Z]{2}\b)', text) if s.strip()]

def compile_article(record, source):
    cid = 'case_' + hashlib.sha256(('protocol-case-v1|' + record['article_id']).encode()).hexdigest()[:24]
    cards = sorted(source.usable_cards(record)[0], key=lambda c: hashlib.sha256((cid+'|'+c['key']).encode()).hexdigest())
    problems, mapping = [], {}
    for c in cards:
        text = c['problem']
        if text not in mapping:
            mapping[text] = len(problems)
            problems.append({'problem_id': len(problems), 'text': text})
    unique = {}
    for c in cards:
        for j, text in enumerate(sentences(c['solution'])):
            item = unique.setdefault(text, {'text': text, 'owners': set(), 'keys': []})
            item['owners'].add(mapping[c['problem']])
            item['keys'].append(c['key']+'_'+str(j))
    # The earliest hash among duplicate occurrences is a stable identity; sorting
    # on text would also be legal but is avoided to keep lexical order absent.
    ordered = sorted(unique.values(), key=lambda f:min(hashlib.sha256((cid+'|fragment|'+k).encode()).hexdigest() for k in f['keys']))
    if not 2 <= len(problems) <= 32 or not 1 <= len(ordered) <= SLOTS:
        raise ValueError('Article outside passage-routing contract')
    fragments = [{'fragment_id': i, 'text': f['text']} for i, f in enumerate(ordered)]
    labels = [sorted(f['owners']) for f in ordered]
    return cid, problems, fragments, labels

def text_key(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
