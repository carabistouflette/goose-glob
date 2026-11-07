# goose-glob

Small, bounded path globbing for [Goose](https://github.com/aardappel/goose).
Match relative byte paths, or collect regular files beneath a directory using
[goose-fs](https://github.com/carabistouflette/goose-fs).

Experimental API. Tested on Linux x86-64/glibc with Goose
`eadca409f68210893f366e60d0c2f0dc29a339be`. The matcher uses only `std`;
filesystem collection requires 64-bit Linux and the pinned goose-fs dependency.
Other platforms are unvalidated. Apache-2.0.

## Try it

Requires Git, Make, CMake 3.27+, C/C++20 compilers, Python 3.11+ for tests,
and Linux headers with openat2 for directory collection.

```sh
git clone https://github.com/carabistouflette/goose-glob.git
cd goose-glob
make setup
.toolchain/goose/build/goose run examples/find.goose -- "$PWD"
make check test differential
```

The example finds `.goose` files, skips hidden entries and prunes `vendor` and
`.build` directories. It prints relative paths with control and non-ASCII bytes
escaped as `\xNN`. Results use breadth-first directory order, with each directory
sorted by unsigned filename bytes. They are not globally sorted.

## Match a path

In a program beside the checkout:

```goose
import glob from "./goose-glob";
import std;
fn main() {
    let matched, status = glob::matches("**/*.goose", "src/main.goose");
    assert(status.error == glob::Error.None && matched);
}
```

`matches(pattern, path, options = Options { .. })` returns `(bool, Status)`.
For repeated use, `compile(pattern)` returns an owned `Pattern` and `Status`;
pass that pattern to the same `matches` function. The compiled value owns its
bytes and can be reused without parsing the pattern again. A failed compilation
returns an empty pattern; matching it reports `InvalidPattern`. Treat pattern
fields as implementation details; do not mutate them.
A non-match is `false` with `Error.None`. Invalid syntax and exceeded limits are
errors, always returning `false`. `validate(pattern)` checks syntax independently.

`Options` has `hidden = false` and `work_limit = 1048576`.

## Collect files

Applications declare the filesystem package in their root source. Goose resolves
`import fs` inside the collector using that mapping. Keep the tested pin unless
you separately validate another revision:

```goose
import glob from "./goose-glob";
import fs from "github.com/carabistouflette/goose-fs@0d84729aed8d72463349cac7d9439d4039ccd6d3";
import glob.walk;
import std;
fn main() {
    var paths: u8[][>..] = [];
    let status = glob_walk::collect("/absolute/project", "**/*.goose",
        ["vendor", ".build"], glob_walk::Options { .. }, paths);
    assert(status.error == glob::Error.None);
}
```

`collect(root, pattern, excludes, options, out)` replaces `out` with owned relative
paths of regular files. Any error clears `out`; incomplete results never report
success. Arguments may borrow the previous output. Exclusions are ordinary globs
matched against each relative path with hidden matching enabled; an excluded
directory is pruned. For example, `vendor` excludes that root directory;
`**/vendor` excludes directories with that name at any depth. There is no gitignore
syntax or automatic `.gitignore` loading.

Collection never follows symlinks and skips symlinks, FIFOs, sockets, and devices.
The absolute root and all relative paths follow goose-fs's strict no-follow path
rules. No NUL, `.`/`..`, repeated or trailing separators are accepted (except root
`/`). Filesystem errors, including failures caused by concurrent changes, fail collection.
Entry types come from directory listings when available, otherwise no-follow
metadata. A file may disappear or change after either observation. This is not a
snapshot, sandbox, filesystem authorization check, or operation with a deadline.
A file can change type after inspection; re-open results with suitable no-follow
policy if you need to read them.

## Pattern rules

- Matching is anchored to the whole relative path and is case-sensitive on bytes.
- `/` separates components; `*` matches zero or more bytes within one component,
  and `?` matches exactly one byte, not one Unicode character.
- `**` must be an entire component and matches zero or more components.
  `**/*.goose` also matches `main.goose`; `a/**` matches `a` itself.
- Classes support `[abc]`, `[a-z]`, and negation `[!abc]` or `[^abc]`.
  A hyphen not used between two range endpoints is literal. Empty classes, reversed ranges and
  escapes inside classes are invalid. A closing `]` ends the class.
- Outside classes, `\` escapes the next byte. Use `\[` for a literal `[`.
  A trailing escape is invalid. Separators cannot be escaped.
- Empty, absolute, NUL-containing paths, empty components, and `.`/`..`
  components are invalid. Patterns follow the same rules.
- With `hidden = false`, a dot-leading component requires a literal leading dot
  in its pattern, such as `.*` or `\.*`; `[.]` does not opt in. `**` skips hidden
  components. The collector skips all hidden entries unless `hidden = true`,
  even when the inclusion pattern starts with a dot.
- Braces, tilde expansion and extglobs have no special meaning. This is a small
  explicit dialect, not a shell or Git wildmatch implementation.

## Limits and errors

Patterns: 1024 bytes. Paths: 4095 bytes. Either: at most 128 components.
Matcher work is bounded by a fuel counter for component transitions, greedy
matching steps and class scans; valid limits are 1–16777216. Validation and path
splitting are bounded separately by the input caps. Fuel is an implementation
limit, not a time unit or hard memory limit. Its accounting can change as matching
gets cheaper; do not depend on exact exhaustion thresholds across versions.

Collector options (default; accepted range):

- `hidden`: false.
- `max_depth`: 32; 1–64. Root entries have depth 1. Encountering a non-excluded
  directory at the maximum depth fails rather than silently truncating.
- `max_entries`: 10000; 0–65536. Counts every listed entry before filtering.
- `max_results`: 1000; 0–65536.
- `max_result_bytes`: 1048576; 0–16777216. Sum of returned path lengths.
- `work_limit`: 1048576; 1–16777216, shared across all inclusion/exclusion matches.

At most 64 exclusions. Each directory listing has goose-fs's independent cap of
4096 entries and 1 MiB of packed names, including entries later filtered out. Adaptive staging starts at 64 KiB; a larger
listing may be read again while retaining the same entry/byte caps.
Queued directory paths have a cumulative 16 MiB cap; queue records are also
bounded by `max_entries`. Results are staged before replacing output, so old
output, staging, backend buffers and queue storage can coexist.

`Status.error`: `None`, `InvalidPattern`, `InvalidPath`, `InvalidOptions`,
`LimitExceeded`, or `Filesystem`. `InvalidPath` is returned by the matcher;
root path validation failures in the collector are `Filesystem`.
`os_error` is an OS errno only when supplied by goose-fs, otherwise zero.
On a primary error, cleanup still runs; that primary error takes precedence.
Only `matches`, `validate`, `compile`, `Pattern`, `collect`, their options/status types and documented
constants are supported API. Other declarations are implementation details.

## Development

```sh
make check test differential CC=gcc
make sanitize SANITIZER_CC=gcc
make test differential CC=clang
make sanitize SANITIZER_CC=clang
```

Tests cover syntax and byte semantics, shared fuel exhaustion, exact result
bounds, hidden/excluded directories, binary filenames, symlinks, FIFOs, missing
paths, and oversized listings. An independent Python `fnmatch`/recursive model
checks 7081 seeded cases in both hidden modes and through both APIs for the shared dialect. Reproducible comparisons, their scope and raw results are described in [bench/README.md](bench/README.md).
See [contributing](CONTRIBUTING.md), [security](SECURITY.md),
[design](docs/DESIGN.md), and [dependency provenance](THIRD_PARTY.md).

## Measured performance

The [separate frozen corpus](bench/results/2026-11-07-independent/README.md)
uses 1,072 paths from three real Git trees, twelve patterns and two larger clean
collection trees. Across seven rounds, goose-glob has lower medians in 67/78
pairwise comparisons and is fastest in 15/26 workload/mode cells. Go wins ten
matching comparisons; Rust wins deep-tree collection. Full ranges and losses are
retained. Product code was unchanged after freezing this validation set.

In the original nine-workload Linux corpus, matching has lower medians than
all three pinned alternatives in every case: 9/9 direct-call and 9/9 prepared
workloads against Rust globset, Go doublestar and Node picomatch. Clean-tree
collection also has a lower median than the three collection adapters. Direct
Rust/Node calls include compilation; prepared mode excludes it for all supporting
APIs. These results are workload-specific and do not establish a universal speed
ranking. See [all medians, ranges, raw samples and limits](bench/results/2026-11-07/README.md)
and the [earlier alpha.2 report](bench/results/2026-11-06/README.md).
