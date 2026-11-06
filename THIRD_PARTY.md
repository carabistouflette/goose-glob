# Dependencies and provenance

Original library sources are Apache-2.0, copyright 2026 goose-glob contributors.
The setup and sanitizer compiler scripts were adapted from carabistouflette's
Apache-2.0 goose-text/goose-fs projects.

The optional collector uses goose-fs at
[`0d84729aed8d72463349cac7d9439d4039ccd6d3`](https://github.com/carabistouflette/goose-fs/tree/0d84729aed8d72463349cac7d9439d4039ccd6d3),
Apache-2.0, copyright 2026 goose-fs contributors. It is fetched by the Goose
compiler; no library code is copied here. Applications supply this package mapping
in their root source. See goose-fs's license, native dependencies and limits.

The development compiler is aardappel/goose at the full commit in GOOSE_REVISION,
Apache-2.0. Its source and third-party notices remain in the separately fetched
`.toolchain/goose` checkout. Runtime code included by compiled applications retains
its upstream license; this library does not replace those notices.

The Python differential oracle uses Python's standard library only.

Benchmark-only adapters use globset 0.4.21 (MIT/Unlicense), glob 0.3.4
(MIT/Apache-2.0), doublestar 4.10.4 (MIT), picomatch 4.0.7 (MIT), and
fast-glob 3.3.3 (MIT), plus their lockfile-recorded transitive dependencies.
No third-party implementation is copied into the source or linked into the
published library. See the packages' license files when redistributing benchmark
binaries or installed package trees.
