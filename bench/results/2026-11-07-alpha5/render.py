#!/usr/bin/env python3
"""Render retained alpha.5 qualification; requires matplotlib 3.10.7."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--directory', type=Path, required=True)
out = parser.parse_args().directory
series = {name: json.loads((out / f'{name}.json').read_text()) for name in ('regression', 'validation')}
engines = {'goose': 'Alpha.5', 'baseline': 'Alpha.4', 'rust': 'Rust', 'go': 'Go', 'node': 'Node'}
titles = {'regression': 'Earlier regression/tuning corpus', 'validation': 'Fresh frozen alpha.5 corpus'}
lines = ['# Alpha.5 parser qualification — 2026-11-07', '',
    'Seven shuffled rounds on a shared Linux x86-64 host, CPU 2 and warm caches. Lower times are better. All losses and observed ranges are retained. Median differences do not establish statistical significance or a universal ranking.', '',
    'The fresh inputs were saved and SHA-256 recorded before parser experiments, then committed afterwards at `5d479fb`. SHA-256: `738c902a5452afcc78562a22b9df7ecc71d430293f3a55c2fbbe73c8cd4df538`. They contain 512 compiler paths disjoint from both earlier compiler selections and four new patterns. Fresh timings were first examined after candidate freeze and independent review. The earlier corpus is tuning/regression data.', '',
    f'Measured candidate: `{series["validation"]["prepared"]["source_head"]}`. Reference: `2022a04e1847490c9c76af91e1e5c01a3c6e3cc0` (alpha.4). Later evidence/release commits may follow; raw reports identify the actual source, tools, dependencies and binaries by hash.', '',
    'The parser now counts globstar components while validating/classifying them, removing a separate component pass from compilation and one-shot matching. It returns a negative count on failure and clears partial metadata. Public API, pattern storage, matching/fuel rules and collector code are unchanged. Reused matching and collection are controls, with mixed changes expected from host variation.', '',
    'Callgrind on the earlier compiler_3 one-shot workload attributed 34.23% of self instructions to pattern scanning. Allocation calls were not dominant as separate functions; this does not imply inlined allocation work is absent. A separate seven-round tuning probe found lower raw medians in 12/12 earlier matching groups. Neither profile nor tuning timings are part of the retained qualification samples.', '',
    '[Method and reproduction](../../README.md#alpha5-parser-experiment) · [Fresh inputs](../../validation-alpha5.json) · [Plot generator](render.py)', '',
    'Rust globset 0.4.21/glob 0.3.4, Go doublestar 4.10.4, Node picomatch 4.0.7/fast-glob 3.3.3. One-shot includes compilation; reused excludes it where supported (Go has no prepared API). Every engine receives 8192 one-shot, 65536 reused and 32 collection calls per round, with identical path order and weights within a mode. Node has explicit JIT warmup. Results/path sets are preflighted and source, dependency, binary, corpus and complete fixture maps are guarded.', '',
    'Own heavy correctness/build/profiling jobs finished before retained timings. Other host activity was uncontrolled. Matching excludes process startup/input IO; collection includes traversal IO on generated empty-file trees. Error/filesystem policies differ. No cold-storage, security-equivalence, whole-command or language-wide ranking follows.', '',
    '## Summary', '', '| Set | Samples | Lower vs alternatives | Lower than all three | Lower vs alpha.4 | Raw lower vs alpha.4 |', '| --- | ---: | ---: | ---: | ---: | ---: |']
scores = {}
for name, data in series.items():
    rows = data['summary']
    for row in rows:
        for engine in engines:
            assert len([s for s in data['samples'] if (s['mode'], s['workload'], s['engine']) == (row['mode'], row['workload'], engine)]) == 7
    raw = [r for r in rows if r['mode'] == 'oneshot']
    scores[name] = dict(samples=len(data['samples']), cells=len(rows), wins=sum(r['engines']['goose']['median'] < r['engines'][e]['median'] for r in rows for e in ('rust', 'go', 'node')), total=3 * len(rows), best=sum(r['engines']['goose']['median'] < min(r['engines'][e]['median'] for e in ('rust', 'go', 'node')) for r in rows), improved=sum(r['engines']['goose']['median'] < r['engines']['baseline']['median'] for r in rows), raw_improved=sum(r['engines']['goose']['median'] < r['engines']['baseline']['median'] for r in raw), raw_cells=len(raw), raw_reduction_percent=[100 * (1-r['engines']['goose']['median']/r['engines']['baseline']['median']) for r in raw])
    s = scores[name]
    lines.append(f'| {titles[name]} | {s["samples"]} | {s["wins"]}/{s["total"]} | {s["best"]}/{s["cells"]} | {s["improved"]}/{s["cells"]} | {s["raw_improved"]}/{s["raw_cells"]} |')
lines += ['', '## Fresh matching workloads', '', '| Workload | Pattern | Paths | Hits |', '| --- | --- | ---: | ---: |']
fresh = series['validation']
for source in fresh['sources']['sources']:
    for i, pattern in enumerate(source['patterns'], 1):
        name = f'{source["name"]}_{i}'
        values = fresh['workloads'][name]
        lines.append(f'| {name} | `{pattern}` | {values["rows"]} | {values["hits"]} |')
lines += ['', 'Fresh collection: wide has 80 directories, 320 files and 160 hits; deep has 8 branches, 26 nested levels each, 416 files and 208 hits. The earlier fixture names/geometry are unchanged.', '']
for name, data in series.items():
    lines += [f'## {titles[name]}', '', f'[Complete raw report]({name}.json). Every cell is median **[minimum, maximum]**. Matching: ns/call; collection: µs/collection.', '']
    for mode in ('oneshot', 'reused', 'collection'):
        lines += [f'### {mode}', '', '| Workload | Alpha.5 | Alpha.4 | Rust | Go | Node |', '| --- | ---: | ---: | ---: | ---: | ---: |']
        for row in data['summary']:
            walk = row['mode'] in ('walk', 'wide', 'deep')
            if (mode == 'collection' and not walk) or (mode != 'collection' and row['mode'] != mode):
                continue
            scale = 1000 if walk else 1
            cells = []
            for engine in engines:
                v = row['engines'][engine]
                cells.append(f'{v["median"]/scale:.1f} [{v["min"]/scale:.1f}, {v["max"]/scale:.1f}]')
            lines.append('| ' + row['workload'] + ' | ' + ' | '.join(cells) + ' |')
        lines.append('')
lines += ['## Correctness and scope', '', 'GCC/Clang interpreted, optimized/debug, ASan/UBSan, unknown-directory-type and filesystem-cap checks pass, alongside 7081 seeded differential cases through both matching APIs and eleven Python guard tests. Added cases cover escaped/class-contained stars and malformed syntax following a globstar. Independent standards and spec reviews found no actionable findings.', '', 'This is frozen in-project evidence, not blind third-party validation. Keep regression and fresh results together, including all slower outcomes. Reused matching and collection do not exercise the removed pass inside their timed loops. Honk already uses prepared patterns; these raw API improvements must not be projected onto its command latency.', '']
(out / 'README.md').write_text('\n'.join(lines))
(out / 'scores.json').write_text(json.dumps(scores, indent=2) + '\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, name in zip(axes, series):
    rows = [r for r in series[name]['summary'] if r['mode'] == 'oneshot']
    values = [r['engines']['baseline']['median']/r['engines']['goose']['median'] for r in rows]
    ax.barh([r['workload'].replace('_', ' ') for r in rows], values, color=['#287d59' if v > 1 else '#b47b24' for v in values])
    ax.axvline(1, color='#444', ls='--', lw=1)
    ax.invert_yaxis()
    ax.set_title(titles[name])
    ax.set_xlabel('Alpha.4 time / alpha.5 time (>1 favors alpha.5)')
    ax.set_xlim(0, max(1.2, max(values)*1.15))
    for i, v in enumerate(values):
        ax.text(v+.01, i, f'{v:.2f}×', va='center', fontsize=8)
fig.suptitle('One-shot pattern parsing + matching', fontsize=14)
fig.text(.5, .01, 'Seven shuffled rounds · shared host · warm caches · all ranges and controls retained in report', ha='center', fontsize=9)
fig.tight_layout(rect=[0, .04, 1, .95])
fig.savefig(out/'comparison.png', dpi=160)
fig.savefig(out/'comparison.svg')
plt.close(fig)
print(json.dumps(scores, indent=2))
