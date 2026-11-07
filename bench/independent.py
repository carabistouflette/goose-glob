#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Measure a named frozen corpus with guarded adapters and explicit provenance."""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import time

import corpus
import run

FROZEN = Path(__file__).with_name('independent-corpus.json')


def rows(frozen=FROZEN):
    result = []
    for source in json.loads(frozen.read_text())['sources']:
        for index, pattern in enumerate(source['patterns']):
            for path in source['paths']:
                result.append((f"{source['name']}_{index + 1}", pattern, path,
                               int(corpus.reference(pattern, path))))
    return result


def checksum(outcomes, count):
    cycles, tail = divmod(count, len(outcomes))
    return cycles * sum(outcomes) + sum(outcomes[:tail])


def make_tree(directory, shape, configuration=None):
    tree = directory/'tree'
    tree.mkdir(parents=True)
    expected = []
    defaults = {'wide': {'groups': 192, 'extensions': ['goose', 'txt', 'goose', 'txt', 'goose', 'txt', 'txt', 'txt']},
                'deep': {'branches': 12, 'levels': 24, 'extensions': ['goose', 'txt']}}
    geometry = (configuration or defaults)[shape]
    if shape == 'wide':
        names = (f'package{p}/module{i}.{ext}' for p in range(geometry['groups'])
                 for i, ext in enumerate(geometry['extensions']))
    else:
        names = (f"branch{p}/" + '/'.join(f'd{d}' for d in range(depth + 1)) + f'/file{i if configuration else ""}.{ext}'
                 for p in range(geometry['branches']) for depth in range(geometry['levels'])
                 for i, ext in enumerate(geometry['extensions']))
    for name in names:
        path = tree/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        if name.endswith('.goose'):
            expected.append(name)
    manifest = directory/'walk-expected.txt'
    manifest.write_text(''.join(p + '\n' for p in sorted(expected)))
    return {'entries': run.fixture_entries(tree), 'expected_sha256': run.digest(manifest),
            'checksum': len(expected) * 1000003 + sum(map(len, expected)),
            'matches': len(expected)}


def verify_fixtures(output, frozen_hash, corpus_hash, fixtures, frozen=FROZEN):
    if run.digest(frozen) != frozen_hash or run.digest(output/'corpus.tsv') != corpus_hash:
        raise SystemExit('Independent corpus changed')
    for shape, fixture in fixtures.items():
        directory = output/shape
        if (run.fixture_entries(directory/'tree') != fixture['entries'] or
                run.digest(directory/'walk-expected.txt') != fixture['expected_sha256']):
            raise SystemExit(f'Independent {shape} fixture changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rounds', type=int, default=7)
    parser.add_argument('--iterations', type=int, default=65536)
    parser.add_argument('--compile-iterations', type=int, default=8192)
    parser.add_argument('--walk-iterations', type=int, default=32)
    parser.add_argument('--cpu', type=int, default=2)
    parser.add_argument('--label', default='independent')
    parser.add_argument('--corpus', type=Path, default=FROZEN)
    parser.add_argument('--baseline', action='store_true', help='include the prepared reference implementation')
    args = parser.parse_args()
    if min(args.rounds, args.iterations, args.compile_iterations, args.walk_iterations) < 1:
        parser.error('positive counts required')
    if args.cpu not in os.sched_getaffinity(0):
        parser.error('CPU unavailable')
    manifest = json.loads((run.OUT/'prepared.json').read_text())
    run.verify(manifest)
    output = run.OUT/args.label
    output.mkdir()  # Never silently overwrite an earlier experiment.
    frozen = args.corpus.resolve()
    frozen_hash = run.digest(frozen)
    definition = json.loads(frozen.read_text())
    cases = rows(frozen)
    (output/'corpus.tsv').write_text(''.join('\t'.join(map(str, row)) + '\n' for row in cases))
    outcomes = defaultdict(list)
    for name, _, _, expected in cases:
        outcomes[name].append(expected)
    fixtures = {shape: make_tree(output/shape, shape, definition.get('collections')) for shape in ('wide', 'deep')}
    corpus_hash = run.digest(output/'corpus.tsv')
    os.sched_setaffinity(0, {args.cpu})
    engines = ('goose', 'baseline', 'rust', 'go', 'node') if args.baseline else ('goose', 'rust', 'go', 'node')
    tasks = [(engine, mode) for engine in engines for mode in ('oneshot', 'reused', 'wide', 'deep')]
    samples = []
    report = {'recorded_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'args': {**vars(args), 'corpus': str(frozen)}, 'prepared': manifest, 'frozen_sha256': frozen_hash,
              'corpus_sha256': corpus_hash, 'sources': definition,
              'workloads': {name: {'rows': len(values), 'hits': sum(values)} for name, values in outcomes.items()},
              'fixtures': fixtures, 'samples': samples,
              'limits': 'Shared host, warm cache, ASCII dialect, synthetic empty-file collection trees. '
                        'Matcher timers exclude process startup/input IO; collection timers include traversal IO. '
                        'Corpus and implementation identities are retained. Old corpora may be tuning data; '
                        'fresh validation must be frozen before optimization and measured after candidate freeze. '
                        'This is not blind third-party validation or a universal ranking.'}
    checkpoint = output/'raw.partial.json'
    rng = random.Random(20261107)
    for round_index in range(args.rounds):
        order = tasks.copy()
        rng.shuffle(order)
        for engine, mode in order:
            run.verify(manifest)
            verify_fixtures(output, frozen_hash, corpus_hash, fixtures, frozen)
            walking = mode in fixtures
            count = args.walk_iterations if walking else (
                args.compile_iterations if mode == 'oneshot' else args.iterations)
            command = manifest['commands'][engine]
            fixture = output/'corpus.tsv'
            if walking:
                fixture = output/mode/'tree'
                if engine in ('goose', 'baseline'):
                    command = [str(run.OUT/f'{engine}-walk')]
            start = time.monotonic_ns()
            proc = subprocess.run([*command, str(fixture), str(count), 'walk' if walking else mode],
                                  capture_output=True, text=True, timeout=180)
            elapsed = time.monotonic_ns() - start
            if proc.returncode:
                (output/'failure.txt').write_text(proc.stdout + proc.stderr)
                raise SystemExit(f'{engine} {mode} failed: {proc.stderr}')
            seen = set()
            for line in proc.stdout.splitlines():
                name, ns, n, total = line.split('\t')
                ns, n, total = int(ns), int(n), int(total)
                valid = {'walk'} if walking else outcomes.keys()
                if name in seen or name not in valid:
                    raise SystemExit(f'Unexpected workload: {engine} {mode} {name}')
                seen.add(name)
                expected = count * fixtures[mode]['checksum'] if walking else checksum(outcomes[name], count)
                if n != count or total != expected or ns <= 0:
                    raise SystemExit(f'Bad checksum/count: {engine} {mode} {name}')
                samples.append({'round': round_index, 'engine': engine, 'mode': mode,
                                'workload': mode if walking else name, 'elapsed_ns': ns,
                                'operations': n, 'checksum': total, 'ns_per_op': ns/n,
                                'process_elapsed_ns': elapsed})
            if len(seen) != (1 if walking else len(outcomes)):
                raise SystemExit('Missing workloads')
            checkpoint.write_text(json.dumps(report, indent=2) + '\n')
            print(f'{round_index + 1}/{args.rounds} {engine} {mode}', flush=True)
    run.verify(manifest)
    verify_fixtures(output, frozen_hash, corpus_hash, fixtures, frozen)
    summary = []
    for mode in ('oneshot', 'reused', 'wide', 'deep'):
        for workload in ([mode] if mode in fixtures else outcomes):
            values = {}
            for engine in engines:
                times = [s['ns_per_op'] for s in samples if (s['mode'], s['workload'], s['engine']) ==
                         (mode, workload, engine)]
                values[engine] = {'median': statistics.median(times), 'min': min(times), 'max': max(times)}
            summary.append({'mode': mode, 'workload': workload, 'engines': values})
    report['summary'] = summary
    (output/'raw.json').write_text(json.dumps(report, indent=2) + '\n')
    checkpoint.unlink()
    print(output/'raw.json')


if __name__ == '__main__':
    main()
