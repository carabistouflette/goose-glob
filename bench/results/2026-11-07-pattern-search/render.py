#!/usr/bin/env python3
"""Summarize all pattern-search tuning results; standard library only."""
import html
import json
from pathlib import Path
import statistics

out = Path(__file__).resolve().parent
sets = {
    'probe16': '16-byte threshold, earlier real paths',
    'guarded16': '16-byte threshold with first-byte guard, earlier real paths',
    'probe64': '64-byte threshold, earlier real paths',
    'long16': '16-byte threshold, synthetic literal patterns',
    'long64': '64-byte threshold, synthetic literal patterns',
}
lines = ['# Rejected pattern byte-search experiments — 2026-11-07', '',
    'Decision: keep alpha.5. All three attempts to replace long scalar literal-run scans with std `find_any` regressed earlier real-path workloads. Synthetic long literals improved, but those targeted gains did not justify the real-path cost or another release. No runtime patch is applied.', '',
    'Each set uses seven shuffled rounds, two implementations and two matching modes, with 131072 calls per workload/round on CPU 2. Three real-path sets have 336 samples each; two synthetic sets have 364 each: 1736 total. Every median, observed range and loss is retained. Warm caches, shared host and uncontrolled other activity; median differences do not establish statistical significance. Own heavy builds/checks did not overlap these probes.', '',
    'Baseline runtime: released alpha.5 (`02d7422d07469f1c483067a4d011698afbafbcc2`). Its measured binary was built from d6d6938, whose matcher/collector bytes are identical. [Identities](identity.json) record source/binary hashes and the earlier complete tool/dependency manifest. Candidate patches: [search16](search16.patch), [guarded16](guarded16.patch), [search64](search64.patch). No API, class/escape dialect or work-budget changes were attempted.', '',
    'The earlier profile attributed 36.38% of self instructions to pattern scanning. The first candidate calls std byte search when at least 16 pattern bytes remain and retains scalar scanning otherwise. The second additionally avoids search setup when the current byte is already syntax. The third raises the threshold to 64 bytes. The pinned std implementation can vectorize generic byte sets on supporting x86 hosts; runtime search/setup and the added branch can still cost more than scanning short runs. The observed regressions do not isolate a single machine-code cause.', '',
    'The earlier real corpus is explicitly tuning data, not unseen validation. Its patterns are 7–21 bytes; no real case enters the 64-byte search branch, so its regressions also demonstrate the cost of dispatch/code changes rather than search itself. The [synthetic corpus](long.tsv) was added during tuning after the first candidate, and cannot establish an independent gain. It has thirteen literal pattern widths (15 through 1024 bytes), eight paths each and equal hit/miss weights. Matching path bytes are identical across engines and modes. Reused matching excludes parsing and is a control.', '',
    'The existing fresh alpha.6 corpus stays unmeasured. These candidates failed the regression screen, so no fresh timing, alternative-library campaign, release, catalog or workspace pin update was justified.', '',
    '## All results', '',
    'Each entry is median **[minimum, maximum]** ns/call. Change is candidate/baseline − 1: negative is faster. The guarded variant did not receive a synthetic run after regressing every real one-shot group.', '']
summary = {}
real_changes = {}
for name, title in sets.items():
    data = json.loads((out/f'{name}.json').read_text())
    samples = data['samples']
    assert len(samples) == (364 if name.startswith('long') else 336)
    summary[name] = {'samples': len(samples)}
    lines += [f'### {title}', '', f'[Raw measurements and input/driver hashes]({name}.json).', '']
    for mode in ('oneshot', 'reused'):
        changes = []
        lines += [f'#### {mode}', '', '| Workload | Alpha.5 | Candidate | Change |', '| --- | ---: | ---: | ---: |']
        for workload in dict.fromkeys(s['name'] for s in samples):
            groups = {e: [s['ns_per_op'] for s in samples if (s['name'], s['mode'], s['engine']) == (workload, mode, e)] for e in ('before', 'candidate')}
            assert all(len(v) == 7 for v in groups.values())
            delta = 100*(statistics.median(groups['candidate'])/statistics.median(groups['before'])-1)
            changes.append(delta)
            cells = [f'{statistics.median(v):.2f} [{min(v):.2f}, {max(v):.2f}]' for v in groups.values()]
            lines.append(f'| {workload} | {cells[0]} | {cells[1]} | {delta:+.2f}% |')
            if mode == 'oneshot' and not name.startswith('long'):
                real_changes.setdefault(workload, {})[name] = delta
        summary[name][mode] = {'lower_medians': sum(v < 0 for v in changes), 'cells': len(changes), 'minimum_change_percent': min(changes), 'maximum_change_percent': max(changes)}
        lines.append('')
lines += ['## Validation and reproduction', '',
    'Every timing task preflights results/statuses and asserts expected checksums inside the matcher executable. The paired Python driver guards both binary hashes and the corpus hash before every task and after the last task. These are exploratory timing screens, not full correctness qualification of the rejected candidates.', '',
    'Final `glob.goose` and `walk.goose` bytes remain identical to alpha.5. New tests exercise long literal, escaped-star, wildcard and class patterns plus malformed escapes, classes, NUL and dot components at widths 15/16/17, 31/32/33, 63/64/65 and 127 through syntax checks and the public matching APIs. GCC normal/debug, ASan/UBSan, 7081 seeded differential cases and eleven Python guard tests qualify the retained baseline and new tests; hosted GCC/Clang CI is required before merge.', '',
    'Build `bench/matcher.goose` at alpha.5 with the pinned Goose compiler and GCC `-O2`, save a baseline binary, apply one retained patch and build a candidate. Generate the earlier TSV with `bench.independent.rows()`, or use retained `long.tsv`. Run the [paired probe](../2026-11-07-prefix-experiment/probe.py) with `--before`, `--candidate`, `--corpus` and a new `--output`; defaults reproduce these counts and CPU. Each raw file records the driver hash. It refuses to overwrite an experiment. Run heavy builds/checks before timings. `python3 render.py` regenerates this report, its summary and the inline chart. The initial build hit a `/tmp` quota; measured binaries were built successfully with a private `TMPDIR` in the library build directory.', '']
(out/'README.md').write_text('\n'.join(lines))
(out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
chart = ['<!doctype html><html><head><style>body{margin:0;font-family:var(--font-sans);color:var(--foreground)}h3{font-size:17px;margin:0 0 8px}p{font-size:13px;color:var(--muted-foreground)}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:6px 3px;text-align:right;border-bottom:1px solid var(--border)}th:first-child,td:first-child{text-align:left}.metric{position:relative}.zero{position:absolute;left:20%;top:4px;bottom:4px;border-left:1px solid var(--border)}.bar{position:absolute;top:5px;bottom:5px;opacity:.23}.value{position:relative}</style></head><body><h3>Parser byte-search experiments: real-path one-shot matching</h3><p>Median latency change versus alpha.5 · negative is faster</p><table><tr><th>Workload</th><th>16 bytes</th><th>16 + guard</th><th>64 bytes</th></tr>']
for workload, values in real_changes.items():
    cells = ''
    for name in ('probe16', 'guarded16', 'probe64'):
        v = values[name]
        position = f'left:{20+min(v,0)*3:.2f}%'
        color = '--success' if v < 0 else '--warning'
        cells += f'<td class="metric"><span class="zero"></span><span class="bar" style="{position};width:{abs(v)*3:.2f}%;background:var({color})"></span><span class="value">{v:+.2f}%</span></td>'
    chart.append(f'<tr><td>{html.escape(workload)}</td>{cells}</tr>')
chart.append('</table><p>All variants rejected. Synthetic long literals improved, but real workloads regressed. All 1,736 samples and ranges are retained; fresh inputs remain unmeasured.</p></body></html>')
(out/'comparison.html').write_text(''.join(chart))
print(json.dumps(summary, indent=2))
