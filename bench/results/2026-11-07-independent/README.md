# Separate frozen corpus — 2026-11-07

Seven shuffled rounds, 728 raw samples, CPU 2 on a shared Linux x86-64 host. Goose has a lower median in **67/78** pairwise comparisons and is fastest in **15/26** workload/mode cells. All slower results remain below. These are median observations, not significance or universal speed claims.

Measured source: `b8990786b20a4c1c93e3c55bb78aeb70201d3440`. Library runtime remains exactly alpha.3 (`379515420be040bc603f0ea87b4e823d2e4e5c3a`); this change adds measurement code/data and documentation, with no matcher or collector changes. The independent corpus was frozen before these measurements and was not used to retune the implementation.

Frozen corpus SHA-256: `16149d4681f40bafba175975cc8e6acf5a752ff769924d9a8e1acb5dda4cb043`.

[Raw samples, manifests and tool/binary/source hashes](raw.json) · [Method and reproduction](../../README.md#separate-frozen-validation-set) · [Frozen paths and source revisions](../../independent-corpus.json)

Rust globset 0.4.21/glob 0.3.4; Go doublestar 4.10.4; Node picomatch 4.0.7/fast-glob 3.3.3. Same locked adapters as the original corpus. One-shot Rust/Node includes compilation; reused mode excludes compilation where supported (Go has no prepared API). Goose additionally validates paths and enforces work limits; error/security policies differ.

Each round uses 8,192 one-shot calls, 65,536 reused calls and 32 collections per tree for every engine. Every engine sees identical path order and weights within each mode. Every matching result and complete collection path set passes preflight. Node keeps explicit JIT warmup. Corpus, inputs and complete empty-file fixture maps are checked throughout. Our heavy validation/build tasks finished before timing; other host activity, including desktop processes and concurrent compilers from other work, was uncontrolled.

## Frozen matching workloads

| Name | Pattern | Paths | Hits |
| --- | --- | ---: | ---: |
| compiler_1 | `stdlib/**/*.goose` | 768 | 4 |
| compiler_2 | `test/**/t[0-9]*.goose` | 768 | 0 |
| compiler_3 | `src/**/*.[ch]` | 768 | 6 |
| compiler_4 | `docs/**/a*.md` | 768 | 1 |
| honk_1 | `src/*.goose` | 255 | 14 |
| honk_2 | `tests/**/t*.goose` | 255 | 2 |
| honk_3 | `vendor/**/test*.goose` | 255 | 0 |
| honk_4 | `bench/**/main.*` | 255 | 1 |
| glob_1 | `tests/*.goose` | 49 | 3 |
| glob_2 | `bench/**/main.*` | 49 | 3 |
| glob_3 | `.github/**/[a-z]*.yml` | 49 | 1 |
| glob_4 | `**/*.md` | 49 | 9 |

## Parse and match each call

Median **[minimum, maximum]** ns/call; lower is better. Seven rounds per engine/case.

| Workload | Goose | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: |
| compiler_1 | 131.1 [124.8, 140.5] | 26737.9 [26468.2, 27288.5] | 63.4 [54.3, 68.1] | 9334.1 [8938.0, 9834.5] |
| compiler_2 | 156.0 [146.8, 172.8] | 34921.5 [34463.1, 35208.1] | 188.0 [180.6, 194.8] | 17779.1 [16317.4, 26317.3] |
| compiler_3 | 123.7 [120.7, 138.3] | 27280.1 [26817.5, 27562.0] | 53.7 [50.4, 55.7] | 16693.9 [14116.8, 23037.8] |
| compiler_4 | 130.0 [121.4, 150.2] | 26144.6 [25691.0, 26975.9] | 56.5 [55.0, 64.2] | 13697.0 [6472.1, 17182.2] |
| honk_1 | 101.0 [98.7, 104.8] | 20786.4 [20534.2, 24284.2] | 59.0 [57.5, 64.3] | 13277.8 [12982.7, 14911.4] |
| honk_2 | 124.4 [115.9, 136.8] | 28720.9 [28554.6, 29048.6] | 73.0 [72.5, 75.3] | 25212.8 [21401.5, 26131.0] |
| honk_3 | 126.4 [119.6, 137.7] | 30552.7 [29869.0, 31248.5] | 104.5 [101.7, 106.0] | 16271.1 [10427.7, 19758.0] |
| honk_4 | 123.6 [122.2, 135.7] | 30444.5 [29771.9, 31852.4] | 147.5 [141.8, 149.9] | 18763.8 [11717.5, 20465.8] |
| glob_1 | 70.9 [65.5, 75.6] | 21448.6 [20991.1, 21602.2] | 79.0 [77.3, 82.3] | 11887.7 [10576.6, 15296.4] |
| glob_2 | 89.4 [85.8, 98.6] | 29708.0 [29417.4, 30384.8] | 113.8 [107.0, 115.4] | 18498.7 [14277.3, 24056.6] |
| glob_3 | 95.5 [90.6, 99.5] | 29287.1 [29000.9, 29713.1] | 77.2 [70.1, 82.9] | 20671.7 [14154.3, 29193.1] |
| glob_4 | 78.0 [67.9, 84.0] | 27963.9 [27763.0, 28782.9] | 295.4 [278.2, 299.1] | 4711.1 [4127.3, 6608.1] |

## Reuse patterns

Median **[minimum, maximum]** ns/call; lower is better. Seven rounds per engine/case.

| Workload | Goose | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: |
| compiler_1 | 83.2 [80.1, 88.0] | 95.4 [94.1, 98.9] | 63.2 [60.5, 66.7] | 453.0 [368.8, 469.8] |
| compiler_2 | 96.5 [92.4, 102.9] | 281.5 [278.6, 283.4] | 175.8 [169.1, 182.1] | 574.8 [543.9, 866.4] |
| compiler_3 | 80.8 [79.1, 82.6] | 91.6 [86.6, 92.0] | 49.0 [46.8, 52.4] | 291.6 [220.5, 422.6] |
| compiler_4 | 85.0 [81.6, 86.9] | 93.5 [85.8, 100.2] | 55.3 [54.5, 60.3] | 252.5 [190.9, 363.3] |
| honk_1 | 57.1 [54.7, 60.0] | 89.5 [87.8, 97.9] | 57.6 [53.9, 61.7] | 167.9 [96.0, 291.9] |
| honk_2 | 64.7 [60.4, 66.8] | 90.1 [88.6, 93.0] | 73.6 [71.3, 78.8] | 265.7 [212.8, 378.4] |
| honk_3 | 66.4 [63.3, 74.7] | 113.0 [109.6, 127.9] | 103.8 [102.2, 104.6] | 272.7 [237.0, 335.2] |
| honk_4 | 68.6 [65.2, 73.2] | 185.4 [180.5, 186.4] | 143.4 [141.3, 146.2] | 336.7 [247.6, 400.4] |
| glob_1 | 41.6 [38.6, 42.8] | 81.3 [78.1, 82.3] | 79.2 [76.6, 80.3] | 263.6 [189.1, 321.7] |
| glob_2 | 48.4 [47.7, 50.2] | 125.7 [118.7, 129.4] | 111.9 [106.6, 113.8] | 162.9 [158.1, 169.1] |
| glob_3 | 41.5 [39.2, 47.4] | 70.8 [68.7, 72.0] | 75.6 [72.2, 79.1] | 107.0 [104.7, 121.6] |
| glob_4 | 48.6 [47.6, 54.0] | 129.9 [128.0, 132.2] | 294.7 [288.5, 300.1] | 427.3 [263.1, 449.5] |

## Larger collection trees

Median **[minimum, maximum]** µs/collection; lower is better. Seven rounds per engine/case.

| Workload | Goose | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: |
| wide | 2578.2 [2546.0, 2599.5] | 3903.8 [3793.2, 4356.9] | 4393.0 [4258.9, 4497.2] | 5436.1 [5028.2, 5717.2] |
| deep | 4137.8 [4014.7, 4164.3] | 3654.3 [3573.0, 3958.2] | 6067.8 [5882.3, 6164.4] | 6976.8 [6897.7, 7163.2] |

Wide: 192 directories, 1,536 empty files, 576 matching files. Deep: 12 branches with 24 nested levels each, 576 empty files, 288 matches. Clean generated trees and warm OS caches; no real-storage/cold-cache or memory ranking follows. The real-repository inputs above benchmark names only, without checking out or executing those repositories.

The new path distributions expose losses, particularly against Go, that the original nine-workload tuning corpus did not. Keep this evidence alongside the original report; alpha.3 does not beat all alternatives on all workloads.
