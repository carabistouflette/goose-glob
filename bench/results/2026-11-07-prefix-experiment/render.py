#!/usr/bin/env python3
"""Summarize every retained tuning cell; standard library only."""
import html
import json
from pathlib import Path
import statistics

out = Path(__file__).resolve().parent
runs = {'initial': json.loads((out/'initial.json').read_text()), 'repeat': json.loads((out/'repeat.json').read_text())['samples']}
lines = ['# Rejected shared-prefix experiment — 2026-11-07', '',
    'Decision: keep alpha.5 runtime unchanged. Moving the prepared literal-prefix rejection into the shared raw/prepared dispatch helped selected long-path misses but regressed several other workloads in two tuning probes. This does not justify a new release. No claim of statistical significance follows from these shared-host observations.', '',
    'Each probe has seven shuffled rounds, two implementations, two modes and twelve earlier workloads: 336 samples per probe, 672 total. Every group receives 131072 calls per round, in identical path order. Both binaries assert expected results, statuses and checksums. Warm caches, CPU 2, uncontrolled host activity. Own heavy validation/build jobs finished before the repeat. The repeat driver checks binary/corpus hashes before each task and after the final task; the initial exploratory probe used the same counts/order seed but did not guard every task.', '',
    'The baseline binary was built from `d6d6938baea52b47becbf0f32c50a474c2820fea`, whose matcher and collector bytes are identical to released alpha.5 (`02d7422d07469f1c483067a4d011698afbafbcc2`). The [prepared manifest](baseline-prepared.json) records its tools, binaries and dependencies. [Identity](identity.json) includes baseline/candidate matcher and binary hashes. The rejected candidate is exactly [this patch](rejected.patch), which is not applied to the released source.', '',
    'Callgrind for 131072 one-shot compiler_3 calls on the baseline recorded 123939090 instructions. Pattern scanning accounted for 36.38% self instructions, byte search 18.98%, component scanning 13.36%, splitting 7.44%, and matching parts 6.24%. This motivated testing span-free prefix rejection for raw calls, reusing an existing prepared optimization. A source move can alter generated code and add dispatch work; these measurements do not isolate the cause of each regression.', '',
    'Fresh [alpha.6 inputs](../../validation-alpha6.json) were committed at `702f0a8` before the experiment; SHA-256 `f62e05cfb1be5a4b5806837597ed495dd785851dbad8544d09cd61d5253e38f2`. Their 512 compiler paths are disjoint from all three earlier compiler selections. They have not been timed. Since the candidate failed the tuning screen, no fresh qualification or cross-library/collection campaign was run. The file name reserves inputs for a future candidate; no alpha.6 release exists.', '',
    '## All tuning results', '',
    'Each value is median **[minimum, maximum]** ns/call across seven rounds. Change is candidate/baseline − 1; positive means slower. Names refer to the earlier independent corpus, now tuning data.', '']
summary = {}
chart = ['<!doctype html><html><head><style>body{margin:0;color:var(--foreground);font-family:var(--font-sans)}h3{font-size:17px;margin:0 0 8px}p{font-size:13px;color:var(--muted-foreground)}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:6px 4px;text-align:right;border-bottom:1px solid var(--border)}th:first-child,td:first-child{text-align:left}.gain{color:var(--success)}.loss{color:var(--warning)}.metric{position:relative;min-width:110px}.bar{position:absolute;top:5px;bottom:5px;opacity:.22}.zero{position:absolute;left:50%;top:4px;bottom:4px;border-left:1px solid var(--border)}.value{position:relative}</style></head><body><h3>Shared-prefix candidate: repeat tuning probe</h3><p>Median latency change versus alpha.5 · negative is faster</p><table><tr><th>Workload</th><th>One-shot</th><th>Reused</th></tr>']
repeat_changes = {}
for label, samples in runs.items():
    assert len(samples) == 336
    names = list(dict.fromkeys(s['name'] for s in samples))
    candidate = 'shared' if label == 'initial' else 'candidate'
    lines += [f'### {label.capitalize()} probe', '', f'[Raw samples]({label}.json).', '']
    summary[label] = {}
    for mode in ('oneshot', 'reused'):
        lines += [f'#### {mode}', '', '| Workload | Alpha.5 | Candidate | Change |', '| --- | ---: | ---: | ---: |']
        changes = []
        for name in names:
            groups = {e: [s['ns_per_op'] for s in samples if (s['name'], s['engine'], s['mode']) == (name, e, mode)] for e in ('before', candidate)}
            assert all(len(v) == 7 for v in groups.values())
            change = 100 * (statistics.median(groups[candidate])/statistics.median(groups['before']) - 1)
            changes.append(change)
            cells = [f'{statistics.median(v):.2f} [{min(v):.2f}, {max(v):.2f}]' for v in groups.values()]
            lines.append(f'| {name} | {cells[0]} | {cells[1]} | {change:+.2f}% |')
            if label == 'repeat':
                repeat_changes.setdefault(name, {})[mode] = change
        lines.append('')
        summary[label][mode] = {'lower_medians': sum(v < 0 for v in changes), 'cells': len(changes), 'minimum_change_percent': min(changes), 'maximum_change_percent': max(changes)}
lines += ['## Validation and reproduction', '',
    'The rejected patch passes GCC/Clang normal, optimized/debug and ASan/UBSan checks, 7081 differential cases and eleven Python guard tests. Added fuel-boundary cases cover long valid prefix misses at budgets 3 and 4, including a literal prefix lacking a following separator. After reverting the runtime patch, the final interpreter matcher suite also passes. The new tests remain; released matcher/collector source bytes stay unchanged.', '',
    'To repeat: build `bench/matcher.goose` at alpha.5 using the pinned Goose compiler and GCC `-O2`, save that baseline binary, apply `rejected.patch`, then build the candidate. Generate corpus.tsv from `bench.independent.rows()` (tab-separated workload, pattern, path, expected). Run the retained `probe.py` with `--before`, `--candidate`, `--corpus` and a new `--output`; defaults are seven rounds, 131072 iterations and CPU 2. It refuses to overwrite an experiment. Run heavy builds/checks before measuring. Use `python3 render.py` to regenerate this report and the inline chart. This tuning driver does not replace the maintained full alternative-library qualification harness.', '']
for name, values in repeat_changes.items():
    cells = ''
    for mode in ('oneshot', 'reused'):
        v = values[mode]
        color = '--success' if v < 0 else '--warning'
        side = 'right' if v < 0 else 'left'
        cells += f'<td class="metric"><span class="zero"></span><span class="bar" style="{side}:50%;width:{abs(v)*5:.2f}%;background:var({color})"></span><span class="value">{v:+.2f}%</span></td>'
    chart.append(f'<tr><td>{html.escape(name)}</td>{cells}</tr>')
chart.append('</table><p>Six of twelve one-shot medians improve; six regress. Candidate rejected. Alpha.5 remains released. All 672 samples and ranges are retained; fresh inputs remain unmeasured.</p></body></html>')
(out/'README.md').write_text('\n'.join(lines))
(out/'comparison.html').write_text(''.join(chart))
(out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2))
