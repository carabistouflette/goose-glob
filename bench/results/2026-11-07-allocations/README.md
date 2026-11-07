# Matching allocation profile — 2026-11-07

Finding: these raw and prepared matching workloads show no per-call malloc-family allocation growth. Doubling calls leaves the whole-process DHAT total at 12 blocks and 72648 allocated bytes in every case. Temporary metadata is written into Goose data stacks and rewound after each call. This profile does not justify an allocator API, persistent scratch buffer or runtime change; alpha.5 stays released.

The three earlier real-path groups are `compiler_3` (768 paths, `src/**/*.[ch]`), `honk_1` (255 paths, `src/*.goose`) and `glob_4` (49 paths, `**/*.md`). Each mode runs 64 then 128 complete corpus cycles, preserving exact path weights. Reused mode compiles before its selected loop. The existing benchmark adapter prepares per input row; its retained-pattern setup footprint is outside the temporary-record counters. Honk already compiles once per invocation and shares that pattern.

## Malloc-family allocations

Valgrind DHAT 3.25.1 observes whole-process malloc-family allocations, including runtime startup and input IO. It does not count Goose data-stack `mmap` reservations, page commits or native stack frames. Stable malloc counts are not a measurement of total process memory or a guarantee for every input/program.

| Workload | Mode | Calls, low → high | Blocks, low → high | Bytes, low → high | Additional blocks/call |
| --- | --- | ---: | ---: | ---: | ---: |
| compiler_3 | oneshot | 49152 → 98304 | 12 → 12 | 72648 → 72648 | 0 |
| compiler_3 | reused | 49152 → 98304 | 12 → 12 | 72648 → 72648 | 0 |
| honk_1 | oneshot | 16320 → 32640 | 12 → 12 | 72648 → 72648 | 0 |
| honk_1 | reused | 16320 → 32640 | 12 → 12 | 72648 → 72648 | 0 |
| glob_4 | oneshot | 3136 → 6272 | 12 → 12 | 72648 → 72648 | 0 |
| glob_4 | reused | 3136 → 6272 | 12 → 12 | 72648 → 72648 | 0 |

All raw DHAT JSON profiles and losslessly gzip-compressed logs are retained under [raw/](raw/); [heap totals](raw/heap.json). The allocation stacks identify runtime startup, libc thread-stack discovery and file IO; none scales with the selected loop count.

## Temporary record payloads

A separate private executable instruments generated C stores to pattern `Part` and path `Span` records. The pinned emitted layout is 17 bytes per Part and 16 per Span. Counters reset after preflight/compilation and before the selected matching loop. Exactly one Part-store and three Span-store sites are instrumented. The wrapper rejects a changed store-site count; the report checks the emitted payload sizes. Instrumented results still pass the normal matcher checksums; instrumented durations are discarded.

These are logical record payload bytes appended during a call, not malloc calls, RSS, total memory bandwidth or full stack-frame sizes. The maximum sums record payloads appended within one call; headers, runtime bookkeeping, native locals and retained compiled patterns are excluded. Both iteration counts give exactly identical per-call averages.

| Workload | Mode | Pattern bytes/call | Path-span bytes/call | Total bytes/call | Maximum record payload/call |
| --- | --- | ---: | ---: | ---: | ---: |
| compiler_3 | oneshot | 51.00 | 48.98 | 99.98 | 147 |
| compiler_3 | reused | 0.00 | 7.58 | 7.58 | 64 |
| honk_1 | oneshot | 34.00 | 55.97 | 89.97 | 146 |
| honk_1 | reused | 0.00 | 17.76 | 17.76 | 64 |
| glob_4 | oneshot | 34.00 | 38.20 | 72.20 | 98 |
| glob_4 | reused | 0.00 | 38.20 | 38.20 | 64 |

[Complete counters](raw/records.json) · [C rewrite identity](rewrite.json) · [Run identities and limits](raw/run-identity.json) · [Source/compiler identities](identity.json).

Generated code initializes each temporary array at a data-stack top, appends packed records by pointer bump, then restores that top on function return. This explains why counting malloc alone misses temporary record work. The existing prepared prefix shortcut also avoids retaining spans on many long literal-prefix misses, reflected in the first two groups. Record counts establish payload volume and reuse; they do not establish how much CPU time those operations consume.

## Reproduction and checks

Linux x86-64/glibc, GCC `-O2`, pinned Goose `eadca409f68210893f366e60d0c2f0dc29a339be`. Baseline matcher/collector bytes match alpha.5 (`02d7422d07469f1c483067a4d011698afbafbcc2`). [Identity](identity.json) links the complete earlier baseline manifest and records helper/source hashes. All 12 DHAT profiles and 12 counter runs are retained. A first pilot run was exploratory and is excluded from these paired tables. Shared-host CPU affinity is CPU 2; these are count profiles, with no latency, memory-speedup or alternative-library ranking.

From the repository root, first build/save the unchanged `bench/matcher.goose` binary and generate corpus.tsv with `bench.independent.rows()`. Then:

```sh
python3 bench/results/2026-11-07-allocations/prepare.py --output .build/allocation-build
/absolute/pinned/goose build .build/allocation-build/matcher.goose \
  --cc "$PWD/.build/allocation-build/profile-cc.py" -O2 -o .build/allocation-build/instrumented
python3 bench/results/2026-11-07-allocations/run.py \
  --baseline /absolute/baseline --instrumented .build/allocation-build/instrumented \
  --corpus /absolute/corpus.tsv --output .build/allocation-profile
```

Preparation/profile directories must be new. The compiler wrapper writes a separate instrumented C copy and leaves library/compiler sources untouched. Binary and source-corpus hashes are checked throughout; each instrumented result checks exact call count and checksum. The driver records its hash and Valgrind version. Run `python3 render.py` to regenerate this report, summary and inline chart from the retained profiles. Runtime and supported API are unchanged; Python helpers and the real instrumented profiling run are validated before publication.
