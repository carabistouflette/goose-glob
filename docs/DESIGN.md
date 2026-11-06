# Design

The matcher and collector have separate imports so text-only users need no
filesystem dependency. The matcher classifies ordinary literal/prefix/suffix
components and uses
bounded slice comparisons for them. Other components use a greedy single-star
scan. A single `**` matches the fixed components from both ends; multiple `**`
components use a greedy scan with one retry point. There is no recursive matching
or dynamic-programming matrix. `compile` owns validated component metadata for
callers matching many paths; the raw API parses only once per call. Both paths
validate candidate paths and enforce bounded work.

The collector uses goose-fs Root operations instead of adding native I/O. A queue
holds byte spans and depths; paths live in a bounded byte arena. Breadth-first
processing avoids recursive frames and holding one directory descriptor per
level. Each scan holds its directory Root while inspecting entries, avoiding
reopening ancestor paths for every metadata call. Patterns and exclusions are
prepared once per collection. Each listing is sorted and filtered. Known listing types avoid redundant metadata;
unknown types use no-follow metadata on the held directory. Directory opens still
refuse symlinks. Entries are classified
and either queued or matched. Failures discard the staged output.

The concrete consumer is the included `examples/find.goose` command, which finds
Goose sources while pruning build/vendor directories. Build tools and test
runners can reuse the same match/collect seam. Honk is a potential future adopter;
no production integration or adoption claim is made.

Keep the first version small: no global pattern cache, gitignore parser, callbacks,
parallel traversal, symlink-following mode, or custom filesystem abstraction.
