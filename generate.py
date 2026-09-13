"""Extract licensed author-published troubleshooting records. MIT licensed code.

Usage: python generate.py --xml-dir XML_DIR --index INDEX.json --out RAW_DIR
The input index is the Europe PMC core-search JSON snapshot. This program does
not download data, create a train/test split, or manufacture scientific labels.
"""
import argparse
import collections
import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

VERSION = '1.0.1'
DASH = r'[-\u2010-\u2015\u2212]'
SUBSTEP = r'(?:(?:\.|' + DASH + r'|\s?)[a-z](?:[ivx]+)?(?![a-z])(?:' + DASH + r'[a-z](?:[ivx]+)?(?![a-z]))*)?'
STEP_TOKEN = r'\d{1,3}' + SUBSTEP
REFERENCE = re.compile(r'\bsteps?\s*#?\s*(' + STEP_TOKEN + r'(?:(?:\s*(?:' + DASH + r'|/)\s*|\s+to\s+|\s*,\s*(?:(?:and|or)\s+)?|\s+(?:and|or|und)\s+|\s+for\s+[A-Za-z :_-]{1,60}\s+and\s+|\s*&\s*)' + STEP_TOKEN + r')*)(?!\w)', re.I)
BACK_REFERENCE = re.compile(r'\b(?:troubleshooting(?:\s*[-:–]?\s*problem)?|problems?)\s*#?\s*\d+(?:\s*(?:,|and|[-–])\s*\d+)*', re.I)

def plain(element):
    if element is None:
        return ''
    blocks = {'p', 'title', 'sec', 'list', 'list-item', 'label', 'table', 'tr', 'td', 'th',
              'caption', 'preformat', 'code', 'disp-quote', 'break', 'br', 'fig'}
    def render(node):
        value = node.text or ''
        for child in node:
            value += render(child) + (child.tail or '')
        if node.tag in blocks or (node.tag == 'xref' and node.get('ref-type') == 'bibr'):
            return ' ' + value + ' '
        return value
    text = ' '.join(render(element).split())
    # Preserve R object-slot expressions, which resemble email addresses.
    return re.sub(r'[\w.+-]+@(?!meta\.data\b|active\.ident\b)[\w.-]+\.[A-Za-z]{2,}', '[contact removed]', text)

def normalize(text):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', text).lower()))

def reference_numbers(text):
    result = set()
    for match in REFERENCE.finditer(text):
        span = match.group(1)
        for a, b in re.findall(r'(\d{1,3})' + SUBSTEP + r'\s*(?:' + DASH + r'|to)\s*(\d{1,3})', span, re.I):
            if int(a) > int(b) or int(b) - int(a) > 200:
                raise ValueError('Invalid step-reference range')
            result.update(range(int(a), int(b) + 1))
        result.update(map(int, re.findall(r'\d+', span)))
    return sorted(result)

def sanitize(text, query=False):
    """Remove answer pointers, not substantive words or scientific quantities.

    Internal method-to-method step references remain available. Troubleshooting
    back-pointers are removed from methods. All step pointers are removed from
    problem/remedy text. The original text remains in the raw source records.
    """
    text = unicodedata.normalize('NFKC', text)
    if query:
        text = REFERENCE.sub('', text)
    text = BACK_REFERENCE.sub('', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\b(?:see|refer to|related to)\s*(?=[).,;:]|$)', '', text, flags=re.I)
    text = re.sub(r'\(\s*\)', '', text)
    text = ''.join(c if c.isprintable() or c.isspace() else ' ' for c in text)
    return ' '.join(text.split()).strip()

def usable_cards(record):
    valid = {s['number'] for s in record['steps']}
    out, excluded = [], collections.Counter()
    for card in record['cards']:
        text = card['problem'] + ' ' + card['solution']
        try:
            targets = reference_numbers(text)
        except ValueError:
            excluded['invalid_reference_range'] += 1
            continue
        if not targets or not set(targets) <= valid:
            excluded['missing_or_outside_method_reference'] += 1
            continue
        if not card['solution'].strip() or re.search(r'before you begin|quantification and statistical analysis', text, re.I):
            excluded['outside_scope_or_missing_remedy'] += 1
            continue
        out.append({'key': card['key'], 'problem': sanitize(card['problem'], True),
                    'solution': sanitize(card['solution'], True), 'targets': targets})
    return out, dict(excluded)

def extract_article(path):
    root = ET.parse(path).getroot()
    license_element = root.find('.//license')
    license_text = plain(license_element)
    license_values = list(license_element.attrib.values()) if license_element is not None else []
    if 'creativecommons.org/licenses/by/4.0' not in license_text and not any('creativecommons.org/licenses/by/4.0' in v for v in license_values):
        return None, 'license_not_cc_by_4'
    sections = root.findall('./body/sec')
    method = next((s for s in sections if 'step-by-step method' in plain(s.find('title')).lower()), None)
    trouble = next((s for s in sections if plain(s.find('title')).lower() == 'troubleshooting'), None)
    if method is None or trouble is None:
        return None, 'missing_section'
    parents = {child: parent for parent in method.iter() for child in parent}
    steps = {}
    for item in method.findall('.//list-item'):
        label = plain(item.find('label'))
        if not re.fullmatch(r'\d+\.', label):
            continue
        number = int(label[:-1])
        if number in steps or not 0 <= number <= 255:
            return None, 'ambiguous_step_number'
        node, heading = item, ''
        while node in parents:
            node = parents[node]
            if node.tag == 'sec':
                heading = plain(node.find('title'))
                break
        body = plain(item)[len(label):].strip()
        steps[number] = {'number': number, 'text': heading + ' | ' + body}
    if not 10 <= len(steps) <= 150:
        return None, 'step_count'
    cards, pending = [], None
    for section in trouble.findall('./sec'):
        title = plain(section.find('title'))
        if re.fullmatch(r'Problem\s*\d+', title, re.I):
            if pending is not None:
                cards.append(pending)
            pending = {'key': title, 'problem': plain(section)[len(title):].strip(), 'solution': ''}
        elif 'potential solution' in title.lower() and pending is not None:
            pending['solution'] += ' ' + plain(section)[len(title):].strip()
    if pending is not None:
        cards.append(pending)
    record = {'article_id': path.stem,
              'title': plain(root.find('./front/article-meta/title-group/article-title')),
              'steps': list(steps.values()), 'cards': cards,
              'xml_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    usable, _ = usable_cards(record)
    if len(usable) < 2:
        return None, 'card_count'
    if len(usable) > 32:
        return None, 'more_than_32_cards'
    return record, 'included'

def generate(xml_dir, index_path, output):
    xml_dir, output = Path(xml_dir), Path(output)
    meta = json.loads(Path(index_path).read_text(encoding='utf-8'))['resultList']['result']
    sources = []
    for row in meta:
        if not row.get('pmcid'):
            continue
        authors = sorted({' '.join((a.get('firstName', '') + ' ' + a.get('lastName', '')).split())
                          for a in row.get('authorList', {}).get('author', [])
                          if a.get('firstName') and a.get('lastName')})
        sources.append({'article_id': row['pmcid'], 'title': row.get('title', ''),
                        'authors': authors, 'doi': row.get('doi', ''),
                        'source_url': 'https://pmc.ncbi.nlm.nih.gov/articles/' + row['pmcid'] + '/'})
    source_ids = [r['article_id'] for r in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError('Duplicate source article identifiers')
    records, exclusions = [], {}
    for ident in sorted(source_ids):
        path = xml_dir / (ident + '.xml')
        if not path.is_file():
            exclusions[ident] = 'download_unavailable'
            continue
        record, reason = extract_article(path)
        if record is None:
            exclusions[ident] = reason
        else:
            records.append(record)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'records.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in records), encoding='utf-8', newline='\n')
    (output / 'source_index.json').write_text(json.dumps(sorted(sources, key=lambda r: r['article_id']), ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    report = {'version': VERSION, 'indexed_articles': len(sources), 'included_articles': len(records),
              'excluded': exclusions, 'article_license': 'CC BY 4.0',
              'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (output / 'source_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml-dir', required=True)
    parser.add_argument('--index', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    report = generate(args.xml_dir, args.index, args.out)
    print(json.dumps({k: v for k, v in report.items() if k != 'excluded'}, indent=2))
