# Design

The matcher and collector have separate imports so text-only users need no
filesystem dependency. The matcher classifies ordinary literal/prefix/suffix
components and uses bounded slice comparisons for them. Literal-only components
with several stars search nonoverlapping literal chunks, with the first-byte search window
restricted by fuel and subsequent prefix comparisons charged individually. Classes are decoded once while
matching; more general components retain a greedy single-star scan. Pattern
validation and classification share one scan, skipping ordinary literal runs.
A validated literal pattern equal to its candidate establishes candidate validity;
mismatches still validate the entire candidate. Single-component matching avoids
temporary path-span storage. Small dispatch helpers inline into their callers. A single `**` matches the fixed components from both ends; multiple `**`
components use a greedy scan with one retry point. There is no recursive matching
or dynamic-programming matrix. `compile` owns validated component metadata for
callers matching many paths; the raw API parses only once per call. Both paths
validate candidate paths and enforce bounded work. Paths below 32 bytes retain
the scalar splitter; longer paths check NUL once and use std's single-byte slash
search. Prepared matching can reject a literal first-component miss without
retaining spans, after validating the complete candidate. That shortcut applies
only when the first comparison cannot exhaust fuel; low budgets keep the normal
matching path and its exact error order.

The collector uses goose-fs Root operations instead of adding native I/O. A queue
holds byte spans and depths; paths live in a bounded byte arena. Breadth-first
processing avoids recursive frames and holding one directory descriptor per
level. Each scan holds its directory Root while inspecting entries, avoiding
reopening ancestor paths for every metadata call. Patterns and exclusions are
prepared once per collection. A 4 KiB first listing avoids initializing 64 KiB
for each small directory.
On a listing limit it retries through goose-fs's adaptive staging with the
original 1 MiB/4096-entry caps. Larger directories may incur one extra partial
listing; filesystem observations are still not a snapshot. Each candidate's
validated spans are reused by the inclusion and exclusion matchers. Each listing
is sorted and filtered. Known listing types avoid redundant metadata;
unknown types use no-follow metadata on the held directory. Directory opens still
refuse symlinks. Entries are classified
and either queued or matched. Failures discard the staged output.

The concrete consumer is the included `examples/find.goose` command, which finds
Goose sources while pruning build/vendor directories. Build tools and test
runners can reuse the same match/collect seam.
[Honk](https://github.com/carabistouflette/honk/pull/15) uses the prepared matcher
for test/benchmark target selection. It retains its own stricter traversal;
the optional collector is not vendored by Honk.

Keep the first version small: no global pattern cache, gitignore parser, callbacks,
parallel traversal, symlink-following mode, or custom filesystem abstraction.
