#!/usr/bin/env python3
"""Summarize malloc-family counts and logical temporary-record payloads."""
import html
import json
from pathlib import Path

out = Path(__file__).resolve().parent
heap = json.loads((out/'raw/heap.json').read_text())
records = json.loads((out/'raw/records.json').read_text())
summary = []
for group in ('compiler_3', 'honk_1', 'glob_4'):
    for mode in ('oneshot', 'reused'):
        h = sorted((r for r in heap if (r['group'], r['mode']) == (group, mode)), key=lambda r: r['calls'])
        r = sorted((r for r in records if (r['group'], r['mode']) == (group, mode)), key=lambda r: r['calls'])
        assert len(h) == len(r) == 2 and h[1]['calls'] == 2*h[0]['calls']
        assert r[0]['per_call'] == r[1]['per_call']
        assert r[0]['maximum_record_payload_per_call'] == r[1]['maximum_record_payload_per_call']
        for row in r:
            assert row['part_bytes'] == 17*row['parts'] and row['span_bytes'] == 16*row['spans']
        calls = h[1]['calls']-h[0]['calls']
        summary.append({'group': group, 'mode': mode, 'low_calls': h[0]['calls'], 'high_calls': h[1]['calls'], 'low_heap_blocks': h[0]['blocks'], 'high_heap_blocks': h[1]['blocks'], 'low_heap_bytes': h[0]['bytes'], 'high_heap_bytes': h[1]['bytes'], 'extra_heap_blocks_per_extra_call': (h[1]['blocks']-h[0]['blocks'])/calls, 'extra_heap_bytes_per_extra_call': (h[1]['bytes']-h[0]['bytes'])/calls, 'part_bytes_per_call': r[0]['per_call']['part_bytes'], 'span_bytes_per_call': r[0]['per_call']['span_bytes'], 'temporary_record_payload_per_call': r[0]['per_call']['part_bytes']+r[0]['per_call']['span_bytes'], 'maximum_record_payload_per_call': r[0]['maximum_record_payload_per_call']})
assert all(r['extra_heap_blocks_per_extra_call'] == r['extra_heap_bytes_per_extra_call'] == 0 for r in summary)
lines = ['# Matching allocation profile — 2026-11-07', '',
    'Finding: these raw and prepared matching workloads show no per-call malloc-family allocation growth. Doubling calls leaves the whole-process DHAT total at 12 blocks and 72648 allocated bytes in every case. Temporary metadata is written into Goose data stacks and rewound after each call. This profile does not justify an allocator API, persistent scratch buffer or runtime change; alpha.5 stays released.', '',
    'The three earlier real-path groups are `compiler_3` (768 paths, `src/**/*.[ch]`), `honk_1` (255 paths, `src/*.goose`) and `glob_4` (49 paths, `**/*.md`). Each mode runs 64 then 128 complete corpus cycles, preserving exact path weights. Reused mode compiles before its selected loop. The existing benchmark adapter prepares per input row; its retained-pattern setup footprint is outside the temporary-record counters. Honk already compiles once per invocation and shares that pattern.', '',
    '## Malloc-family allocations', '',
    'Valgrind DHAT 3.25.1 observes whole-process malloc-family allocations, including runtime startup and input IO. It does not count Goose data-stack `mmap` reservations, page commits or native stack frames. Stable malloc counts are not a measurement of total process memory or a guarantee for every input/program.', '',
    '| Workload | Mode | Calls, low → high | Blocks, low → high | Bytes, low → high | Additional blocks/call |',
    '| --- | --- | ---: | ---: | ---: | ---: |']
for r in summary:
    lines.append(f'| {r["group"]} | {r["mode"]} | {r["low_calls"]} → {r["high_calls"]} | {r["low_heap_blocks"]} → {r["high_heap_blocks"]} | {r["low_heap_bytes"]} → {r["high_heap_bytes"]} | {r["extra_heap_blocks_per_extra_call"]:.0f} |')
lines += ['', 'All raw DHAT JSON profiles and losslessly gzip-compressed logs are retained under [raw/](raw/); [heap totals](raw/heap.json). The allocation stacks identify runtime startup, libc thread-stack discovery and file IO; none scales with the selected loop count.', '',
    '## Temporary record payloads', '',
    'A separate private executable instruments generated C stores to pattern `Part` and path `Span` records. The pinned emitted layout is 17 bytes per Part and 16 per Span. Counters reset after preflight/compilation and before the selected matching loop. Exactly one Part-store and three Span-store sites are instrumented. The wrapper rejects a changed store-site count; the report checks the emitted payload sizes. Instrumented results still pass the normal matcher checksums; instrumented durations are discarded.', '',
    'These are logical record payload bytes appended during a call, not malloc calls, RSS, total memory bandwidth or full stack-frame sizes. The maximum sums record payloads appended within one call; headers, runtime bookkeeping, native locals and retained compiled patterns are excluded. Both iteration counts give exactly identical per-call averages.', '',
    '| Workload | Mode | Pattern bytes/call | Path-span bytes/call | Total bytes/call | Maximum record payload/call |',
    '| --- | --- | ---: | ---: | ---: | ---: |']
for r in summary:
    lines.append(f'| {r["group"]} | {r["mode"]} | {r["part_bytes_per_call"]:.2f} | {r["span_bytes_per_call"]:.2f} | {r["temporary_record_payload_per_call"]:.2f} | {r["maximum_record_payload_per_call"]} |')
lines += ['', '[Complete counters](raw/records.json) · [C rewrite identity](rewrite.json) · [Run identities and limits](raw/run-identity.json) · [Source/compiler identities](identity.json).', '',
    'Generated code initializes each temporary array at a data-stack top, appends packed records by pointer bump, then restores that top on function return. This explains why counting malloc alone misses temporary record work. The existing prepared prefix shortcut also avoids retaining spans on many long literal-prefix misses, reflected in the first two groups. Record counts establish payload volume and reuse; they do not establish how much CPU time those operations consume.', '',
    '## Reproduction and checks', '',
    'Linux x86-64/glibc, GCC `-O2`, pinned Goose `eadca409f68210893f366e60d0c2f0dc29a339be`. Baseline matcher/collector bytes match alpha.5 (`02d7422d07469f1c483067a4d011698afbafbcc2`). [Identity](identity.json) links the complete earlier baseline manifest and records helper/source hashes. All 12 DHAT profiles and 12 counter runs are retained. A first pilot run was exploratory and is excluded from these paired tables. Shared-host CPU affinity is CPU 2; these are count profiles, with no latency, memory-speedup or alternative-library ranking.', '',
    'From the repository root, first build/save the unchanged `bench/matcher.goose` binary and generate corpus.tsv with `bench.independent.rows()`. Then:', '',
    '```sh',
    'python3 bench/results/2026-11-07-allocations/prepare.py --output .build/allocation-build',
    '/absolute/pinned/goose build .build/allocation-build/matcher.goose \\',
    '  --cc "$PWD/.build/allocation-build/profile-cc.py" -O2 -o .build/allocation-build/instrumented',
    'python3 bench/results/2026-11-07-allocations/run.py \\',
    '  --baseline /absolute/baseline --instrumented .build/allocation-build/instrumented \\',
    '  --corpus /absolute/corpus.tsv --output .build/allocation-profile',
    '```', '',
    'Preparation/profile directories must be new. The compiler wrapper writes a separate instrumented C copy and leaves library/compiler sources untouched. Binary and source-corpus hashes are checked throughout; each instrumented result checks exact call count and checksum. The driver records its hash and Valgrind version. Run `python3 render.py` to regenerate this report, summary and inline chart from the retained profiles. Runtime and supported API are unchanged; Python helpers and the real instrumented profiling run are validated before publication.', '']
(out/'README.md').write_text('\n'.join(lines))
(out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
chart = ['<!doctype html><html><head><style>body{margin:0;font-family:var(--font-sans);color:var(--foreground)}h3{font-size:17px;margin:0 0 8px}p{font-size:13px;color:var(--muted-foreground)}.group{margin:16px 0}.label{font-size:13px;font-weight:600}.row{display:grid;grid-template-columns:75px 1fr 65px;gap:10px;align-items:center;margin:7px 0;font-size:13px}.track{height:20px;background:var(--secondary);border-radius:4px}.bar{height:100%;border-radius:4px}.number{text-align:right}</style></head><body><h3>Temporary record payload appended per matcher call</h3><p>Average logical bytes · same averages at both iteration counts</p>']
for group in ('compiler_3', 'honk_1', 'glob_4'):
    chart.append(f'<div class="group"><div class="label">{html.escape(group)}</div>')
    for r in (r for r in summary if r['group'] == group):
        v = r['temporary_record_payload_per_call']
        color = '--chart-1' if r['mode'] == 'oneshot' else '--chart-2'
        label = 'One-shot' if r['mode'] == 'oneshot' else 'Prepared'
        chart.append(f'<div class="row"><span>{label}</span><div class="track"><div class="bar" style="width:{v/105*100:.2f}%;background:var({color})"></div></div><span class="number">{v:.2f} B</span></div>')
    chart.append('</div>')
chart.append('<p>Doubling calls added zero malloc-family allocations in all six workload/mode pairs. Data-stack records are reused. These counts exclude mapped pages, stack headers, retained patterns and RSS; they make no latency claim.</p></body></html>')
(out/'comparison.html').write_text(''.join(chart))
print(json.dumps(summary, indent=2))
