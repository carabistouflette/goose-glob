# Competitive benchmarks

Run from the repository after `make setup`. Additional tools are Cargo/Rust,
Go 1.23+, Node/npm, and Linux CPU affinity support. Dependencies are exact-pinned
by Cargo.lock, go.mod/go.sum, and package-lock.json: Rust globset 0.4.21 and glob
0.3.4, Go doublestar 4.10.4, Node picomatch 4.0.7 and fast-glob 3.3.3.
They are benchmark-only dependencies and are not shipped with the library.

```sh
python3 bench/run.py --prepare-only
python3 bench/run.py --prepared --rounds 7 --iterations 100000 \
  --compile-iterations 2000 --walk-iterations 100 --cpu 2 --label comparison
```

Use `--goose /path/to/pinned/goose` and `--cc gcc` as needed. Choose an available
CPU, preferably the same core class across machines. The driver builds once,
records source/tool/binary hashes (including resolved Goose stdlib and goose-fs),
checks source snapshots across preparation and rejects changes to the recorded
runtime environment or complete fixture entry/type manifest before/after timing,
and runs engines sequentially in a seeded shuffled order. It does not reserve the
host or change its governor. Preparation never runs a timed benchmark. Generated
sources, fixtures, packages and executables stay under ignored build/cache paths.
Native Rust artifacts are selected from Cargo's reported executable for the
explicit host target. Go modules and npm/Cargo lockfiles are enforced.

## What is compared

Matching uses 576 shared ASCII pattern/path pairs: nine workloads, 64 rotating
rows each, with equal positive/negative outcomes. The corpus includes literals,
prefix/suffix, recursive suffix, ordinary wildcards, classes, a middle `**`,
multiple `**` and repeated-star retries. Some patterns/paths repeat intentionally;
this is a deterministic representative corpus, not a random internet workload.
All engines preflight every expected result and check the timed checksum.

- `oneshot`: parse/validate and match on every call. Rust builds and drops its
  normal compiled matcher per call; Node creates its normal matcher per call.
  Goose and Go use their direct matching APIs. Rust/Node run fewer iterations
  because compilation costs more; per-operation times retain the actual counts.
- `reused`: Goose `compile` and Rust/Node normal compilation happen before timing.
  Matching still validates Goose input paths and enforces work limits. Go has no
  prepared-pattern API here and uses `Match`. The initial alpha has no prepared API
  either; its baseline retains the original direct call. References with `compile`
  use their prepared API in this mode. Construction/owned
  pattern bytes are excluded only in this explicitly reused mode.
- `walk`: collect regular files matching `**/*.goose` from a generated warm-cache
  tree with 40 non-root directories and 256 empty regular files (128 matches).
  Goose uses `collect`, Rust `glob_with` plus regular-file filtering, Go
  `doublestar.Glob` with files-only/no-follow/error flags, and Node `fast-glob.sync`
  with files-only/no-follow. Creation and process startup are excluded. Every
  adapter first compares its complete normalized path set with a saved expected
  manifest; timed calls observe result counts and path lengths. Results own their
  returned path strings. Full collection, metadata, ordering and allocation work
  performed by each normal API stays inside timing.

Collection is a **clean trusted-tree throughput comparison**, not a proof of
identical security/error contracts. No hidden files, symlinks, non-ASCII names,
permission failures or binding resource limits occur in its timed tree. Goose
retains its additional root/path checks, limits, sorted per-directory traversal
and atomic result staging; alternatives make different checks and ordering choices.
No cold-storage, network filesystem, peak-memory or deadline claim is measured.

The matching dialect is the shared subset, with literal separators in globset,
case sensitivity and hidden matching enabled. Picomatch class negation is
normalized from `[!...]` to `[^...]` before timing. Patterns intentionally avoid
non-ASCII, braces, escapes, hidden paths, and trailing `/**` cases whose semantics
differ between engines. Those remain covered separately by Goose correctness
tests. All semantically mismatched fixtures fail preparation/run validation rather
than silently entering a performance ranking.

Timers are monotonic clocks inside each process. Node gets an explicit 20,000-call
matching JIT warmup per workload and 10 collection calls before timing; measured
GC/allocation remains included. Rust uses black_box; all engines consume runtime
fixture inputs and check complete batch outputs. Do not infer a universal ranking
from per-call parse costs or aggregate the pathological repeated-star case into a
single speed headline.

## Evidence

`--reference FULL_COMMIT` builds the original matcher and collector using the same
corpus and public APIs; the default is the initial alpha source. References providing `compile` use the current matching adapter, including
preparation outside reused-mode timing. The legacy adapter is used only for
references without that API. Reports include every sample, medians/ranges, source/tool
identities, modes, actual operation counts and the original reference revision.

The driver writes `.build/bench/LABEL.json`. Read the complete per-workload table,
including slower outcomes and ranges, before making claims. Shared-host scheduling,
thermal changes and governor behavior remain limitations despite CPU affinity.
Retained published reports belong in `results/`; do not overwrite historical raw
samples. Fresh measurements require matching source and harness hashes.

Primary API references: [globset](https://docs.rs/globset/0.4.21/globset/),
[glob](https://docs.rs/glob/0.3.4/glob/),
[doublestar](https://pkg.go.dev/github.com/bmatcuk/doublestar/v4@v4.10.4),
[picomatch](https://github.com/micromatch/picomatch/tree/4.0.7), and
[fast-glob](https://github.com/mrmlnc/fast-glob/tree/3.3.3).

## Separate frozen validation set

`independent-corpus.json` freezes 1,072 tracked paths from exact compiler, Honk
and goose-glob Git trees and twelve patterns before measurement. Each source
records its full revision and SHA-256 of `git ls-tree -rz --name-only REV`.
Eligible paths are printable ASCII, at most 4095 bytes and 128 components;
the first 768 ranked by SHA-256 of the path are retained, or all paths in smaller
trees. Outcomes are computed with the independent Python component oracle from
`corpus.py`. Natural hit ratios, including entirely negative workloads, remain.
The frozen paths suffice to rerun without checking out or building those projects.
This is a separate in-project validation set, not blind external validation.
The original alpha.3 experiment made no implementation changes in response to
these measurements. Alpha.4 treats this set as regression/tuning data and uses
the fresh validation set described below.

```sh
python3 bench/run.py --goose /absolute/pinned/goose --prepare-only
python3 bench/independent.py --rounds 7 --cpu 2 --label independent
```

The second command reuses the exact prepared adapters, locked dependencies and
before/after source, tool, dependency and binary checks. It adds a frozen corpus
hash and complete fixture manifests. It checks every result before timing and
validates dynamic checksums for each natural hit ratio and iteration count.
Every engine uses the same path sequence and call count within a mode: 8192
one-shot calls and 65536 reused calls by default. This preserves identical path
weights even when a count ends partway through a corpus cycle. Node keeps the same explicit JIT warmup as the retained harness.

Collection uses the normal APIs and `**/*.goose`, with complete sorted path-set
preflight, on separate clean empty-file trees: wide (192 directories, 1536 files,
576 hits) and deep (12 branches, 24 nested levels each, 576 files, 288 hits).
The fixture maps and expected manifests are checked before every task and after
the last task. These are warm-cache generated trees, not real storage benchmarks.
The command writes raw samples and medians/ranges to `.build/bench/LABEL/raw.json`;
existing experiment directories are never overwritten. Shared-host timing has no
CI threshold and cannot establish a universal language or library ranking.

## Alpha.4 candidate qualification

The earlier independent corpus is now regression/tuning data. The fresh
[`validation-alpha4.json`](validation-alpha4.json) was committed at `d5b86d1`
before optimization, with SHA-256
`0197483c7e8058d056dfff86ba5d0ea6616bdfbac4bb206a171b950fcf552afa`.
It selects additional compiler paths disjoint from the earlier selection, plus
pinned goose-fs and goose-crypto paths, and twelve patterns. Collection geometry
is also frozen: wide (112 directories, 1008 files, 336 matches) and deep
(10 branches, 28 nested levels each, 840 files, 560 matches). Duplicate extensions
use distinct indexed names in these fresh trees. Historical default tree names
and geometry stay unchanged and are protected by a manifest regression.

Freeze the candidate before examining this set's timing results. Record changes
needed for correctness or harness issues; never silently retune against it while
calling it unseen validation. Preparation and heavy correctness/profiling jobs
finish before retained timings. Use sequential shuffled rounds on one CPU and
report uncontrolled host activity and all slower results.

```sh
python3 bench/run.py --goose /absolute/pinned/goose \
  --reference 1c2cb05988a253c8f9c4922659dd4a669e0b80cf --prepare-only
python3 bench/independent.py --baseline --label alpha4-regression
python3 bench/independent.py --baseline --corpus bench/validation-alpha4.json \
  --label alpha4-validation
```

`--baseline` includes the prepared reference binary from that exact alpha.3
runtime snapshot. All engines receive identical call counts and path order
within each mode: 8192 one-shot, 65536 reused, and 32 collection calls by default.
The raw report includes the selected corpus, its full hash, exact fixture maps,
expected paths, tools, binaries and dependencies. Median/min/max and checksums
are retained for every engine and round. Compiler/library policies still differ;
this is a workload comparison rather than a universal language ranking.

## Alpha.5 parser experiment

`validation-alpha5.json` was saved and its SHA-256
`738c902a5452afcc78562a22b9df7ecc71d430293f3a55c2fbbe73c8cd4df538`
recorded before the parser experiment; it was committed afterwards. It selects
512 additional compiler paths disjoint from both earlier selections and four
new patterns. Its timing is first examined after candidate freeze/review.
Prepare with reference `2022a04e1847490c9c76af91e1e5c01a3c6e3cc0`, then run
`bench/independent.py --baseline --corpus bench/validation-alpha5.json --label alpha5-validation`.
The earlier independent corpus is regression/tuning data. All counts, guards and
shared-host limits from the alpha.4 method apply.

Retained [alpha.5 qualification](results/2026-11-07-alpha5/README.md) includes
both sets and all losses. Reproduce after preparing the exact reference:

```sh
python3 bench/run.py --goose /absolute/pinned/goose \
  --reference 2022a04e1847490c9c76af91e1e5c01a3c6e3cc0 --prepare-only
python3 bench/independent.py --baseline --rounds 7 --cpu 2 --label alpha5-regression
python3 bench/independent.py --baseline --rounds 7 --cpu 2 \
  --corpus bench/validation-alpha5.json --label alpha5-validation
```
