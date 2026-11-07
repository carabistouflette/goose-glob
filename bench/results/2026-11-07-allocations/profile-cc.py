#!/usr/bin/env python3
"""Instrument typed record stores emitted by the pinned Goose compiler."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parent
args = sys.argv[1:]
rewritten = 0
for index, arg in enumerate(args):
    if not arg.endswith('.c') or not Path(arg).is_file():
        continue
    source = Path(arg).read_text()
    if 'glob_scan_pattern_' not in source:
        continue
    counts = {'Part': 0, 'Span': 0}

    def instrument(match):
        kind = 'Part' if '_Part_' in match[2] else 'Span'
        counts[kind] += 1
        counter = 'parts' if kind == 'Part' else 'spans'
        size = 'part' if kind == 'Part' else 'span'
        return (match[0] + f'\n{match[1]}profile_{counter}++; '
                f'profile_{size}_bytes += sizeof({match[2]}); '
                f'profile_current += sizeof({match[2]});')

    patched = re.sub(r'^(\s*)\*\((glob_(?:Part|Span)_g\d+) \*\)(.+?) = (.+);$',
                     instrument, source, flags=re.M)
    assert counts == {'Part': 1, 'Span': 3}, counts
    path = root/'instrumented.c'
    path.write_text(patched)
    args[index] = str(path)
    rewritten += 1
    identity = {'original_c_sha256': hashlib.sha256(source.encode()).hexdigest(),
                'instrumented_c_sha256': hashlib.sha256(patched.encode()).hexdigest(),
                'store_sites': counts}
    (root/'rewrite.json').write_text(json.dumps(identity, indent=2)+'\n')
if rewritten:
    args = ['-include', str(root/'counters.h'), *args]
sys.exit(subprocess.call(['gcc', *args]))
