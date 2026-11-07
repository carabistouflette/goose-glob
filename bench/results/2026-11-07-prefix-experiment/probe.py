#!/usr/bin/env python3
"""Exploratory paired matcher probe; no cross-library ranking."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--before', type=Path, required=True)
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--corpus', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--rounds', type=int, default=7)
p.add_argument('--iterations', type=int, default=131072)
p.add_argument('--cpu', type=int, default=2)
a = p.parse_args()
if min(a.rounds, a.iterations) <= 0:
    p.error('positive counts required')
if a.output.exists():
    p.error('output already exists')
inputs = {'before': a.before.resolve(), 'candidate': a.candidate.resolve(), 'corpus': a.corpus.resolve()}
def hashes():
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in inputs.items()}
frozen = hashes()
os.sched_setaffinity(0, {a.cpu})
rng = random.Random(2026110706)
samples = []
expected = {}
for round_index in range(a.rounds):
    tasks = [(e, m) for e in ('before', 'candidate') for m in ('oneshot', 'reused')]
    rng.shuffle(tasks)
    for engine, mode in tasks:
        assert hashes() == frozen, 'input changed'
        proc = subprocess.run([str(inputs[engine]), str(inputs['corpus']), str(a.iterations), mode], capture_output=True, text=True, check=True, timeout=180)
        seen = set()
        for line in proc.stdout.splitlines():
            name, ns, count, checksum = line.split('\t')
            ns, count, checksum = int(ns), int(count), int(checksum)
            assert name not in seen and count == a.iterations and ns > 0
            seen.add(name)
            assert expected.setdefault(name, checksum) == checksum
            samples.append({'round': round_index, 'engine': engine, 'mode': mode, 'name': name, 'ns_per_op': ns/count, 'checksum': checksum})
        assert seen == set(expected), 'missing workloads'
assert hashes() == frozen
report = {'args': {k: str(v) if isinstance(v, Path) else v for k, v in vars(a).items()}, 'sha256': frozen, 'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'samples': samples}
with a.output.open('x') as f:
    json.dump(report, f, indent=2)
    f.write('\n')
print(f'{len(samples)} samples saved to {a.output}')
