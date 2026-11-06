# Design

The matcher and collector have separate imports so text-only users need no
filesystem dependency. The matcher uses a greedy single-star scan within each
component and two boolean rows for `**` transitions between components. There is
no recursive matching or compiled-pattern object. Pattern validation runs before
matching. Bounded inputs and a fuel counter limit adversarial work.

The collector uses goose-fs Root operations instead of adding native I/O. A queue
holds byte spans and depths; paths live in a bounded byte arena. Breadth-first
processing avoids recursive frames and holding one directory descriptor per
level. Each listing is sorted, inspected without following symlinks, filtered,
and either queued or matched. Failures discard the staged output.

The concrete consumer is the included `examples/find.goose` command, which finds
Goose sources while pruning build/vendor directories. Build tools and test
runners can reuse the same match/collect seam. Honk is a potential future adopter;
no production integration or adoption claim is made.

Keep the first version small: no pattern cache, gitignore parser, callbacks,
parallel traversal, symlink-following mode, or custom filesystem abstraction.
