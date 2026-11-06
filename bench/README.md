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
