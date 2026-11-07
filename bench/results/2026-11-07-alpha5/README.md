# Alpha.5 parser qualification — 2026-11-07

Seven shuffled rounds on a shared Linux x86-64 host, CPU 2 and warm caches. Lower times are better. All losses and observed ranges are retained. Median differences do not establish statistical significance or a universal ranking.

The fresh inputs were saved and SHA-256 recorded before parser experiments, then committed afterwards at `5d479fb`. SHA-256: `738c902a5452afcc78562a22b9df7ecc71d430293f3a55c2fbbe73c8cd4df538`. They contain 512 compiler paths disjoint from both earlier compiler selections and four new patterns. Fresh timings were first examined after candidate freeze and independent review. The earlier corpus is tuning/regression data.

Measured candidate: `d6d6938baea52b47becbf0f32c50a474c2820fea`. Reference: `2022a04e1847490c9c76af91e1e5c01a3c6e3cc0` (alpha.4). Later evidence/release commits may follow; raw reports identify the actual source, tools, dependencies and binaries by hash.

The parser now counts globstar components while validating/classifying them, removing a separate component pass from compilation and one-shot matching. It returns a negative count on failure and clears partial metadata. Public API, pattern storage, matching/fuel rules and collector code are unchanged. Reused matching and collection are controls, with mixed changes expected from host variation.

Callgrind on the earlier compiler_3 one-shot workload attributed 34.23% of self instructions to pattern scanning. Allocation calls were not dominant as separate functions; this does not imply inlined allocation work is absent. A separate seven-round tuning probe found lower raw medians in 12/12 earlier matching groups. Neither profile nor tuning timings are part of the retained qualification samples.

[Method and reproduction](../../README.md#alpha5-parser-experiment) · [Fresh inputs](../../validation-alpha5.json) · [Plot generator](render.py)

Rust globset 0.4.21/glob 0.3.4, Go doublestar 4.10.4, Node picomatch 4.0.7/fast-glob 3.3.3. One-shot includes compilation; reused excludes it where supported (Go has no prepared API). Every engine receives 8192 one-shot, 65536 reused and 32 collection calls per round, with identical path order and weights within a mode. Node has explicit JIT warmup. Results/path sets are preflighted and source, dependency, binary, corpus and complete fixture maps are guarded.

Own heavy correctness/build/profiling jobs finished before retained timings. Other host activity was uncontrolled. Matching excludes process startup/input IO; collection includes traversal IO on generated empty-file trees. Error/filesystem policies differ. No cold-storage, security-equivalence, whole-command or language-wide ranking follows.

## Summary

| Set | Samples | Lower vs alternatives | Lower than all three | Lower vs alpha.4 | Raw lower vs alpha.4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Earlier regression/tuning corpus | 910 | 69/78 | 17/26 | 16/26 | 11/12 |
| Fresh frozen alpha.5 corpus | 350 | 26/30 | 6/10 | 3/10 | 3/4 |

## Fresh matching workloads

| Workload | Pattern | Paths | Hits |
| --- | --- | ---: | ---: |
| compiler_remaining_1 | `test/**/p*.goose` | 512 | 9 |
| compiler_remaining_2 | `stdlib/**/s*.goose` | 512 | 0 |
| compiler_remaining_3 | `src/**/[a-f]*.cpp` | 512 | 0 |
| compiler_remaining_4 | `samples/**/*_*.goose` | 512 | 5 |

Fresh collection: wide has 80 directories, 320 files and 160 hits; deep has 8 branches, 26 nested levels each, 416 files and 208 hits. The earlier fixture names/geometry are unchanged.

## Earlier regression/tuning corpus

[Complete raw report](regression.json). Every cell is median **[minimum, maximum]**. Matching: ns/call; collection: µs/collection.

### oneshot

| Workload | Alpha.5 | Alpha.4 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| compiler_1 | 100.6 [96.5, 103.5] | 108.0 [103.0, 114.6] | 24627.9 [24436.9, 26757.0] | 61.1 [52.3, 70.0] | 9100.1 [8430.6, 9986.2] |
| compiler_2 | 121.0 [113.6, 130.0] | 134.1 [123.8, 140.7] | 32561.6 [32055.6, 34438.0] | 189.5 [169.0, 211.3] | 17627.7 [16343.8, 26016.9] |
| compiler_3 | 96.4 [89.6, 102.9] | 105.3 [98.9, 111.0] | 25150.7 [24782.8, 26299.6] | 53.6 [45.9, 63.3] | 14833.9 [13985.6, 21929.2] |
| compiler_4 | 96.8 [90.3, 108.5] | 105.9 [100.3, 107.5] | 24084.2 [23137.7, 25270.6] | 58.4 [54.8, 72.0] | 14096.8 [11367.9, 23347.3] |
| honk_1 | 90.9 [84.7, 95.0] | 90.6 [87.8, 99.7] | 19757.4 [18940.7, 20557.6] | 57.9 [53.2, 67.0] | 14289.8 [8905.3, 17742.5] |
| honk_2 | 113.9 [106.2, 124.0] | 128.1 [114.5, 134.9] | 26712.7 [25770.5, 27681.8] | 72.4 [67.0, 87.9] | 22005.8 [15131.1, 24470.7] |
| honk_3 | 113.7 [105.9, 134.2] | 119.7 [117.6, 137.3] | 28176.4 [27487.4, 29858.5] | 105.4 [96.6, 122.6] | 22292.9 [14880.6, 26148.5] |
| honk_4 | 117.2 [109.7, 125.1] | 122.7 [115.2, 139.5] | 29109.1 [27014.7, 30315.1] | 146.7 [132.0, 160.6] | 19172.7 [14217.0, 22307.3] |
| glob_1 | 68.4 [65.2, 71.3] | 72.4 [67.7, 75.6] | 20650.9 [19331.4, 21344.7] | 79.4 [69.9, 87.7] | 13491.4 [11243.6, 20620.0] |
| glob_2 | 86.3 [77.9, 89.6] | 92.8 [88.0, 97.8] | 28134.5 [27226.2, 29136.5] | 110.3 [101.2, 128.6] | 18822.7 [14815.9, 25582.0] |
| glob_3 | 84.6 [76.9, 87.9] | 99.4 [97.0, 107.0] | 27694.2 [27041.8, 29144.4] | 79.3 [72.3, 86.4] | 26069.7 [19606.0, 30088.3] |
| glob_4 | 72.4 [67.3, 80.6] | 76.3 [72.8, 81.3] | 26720.0 [25674.5, 27923.9] | 296.0 [253.2, 330.4] | 4200.1 [3646.2, 6217.7] |

### reused

| Workload | Alpha.5 | Alpha.4 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| compiler_1 | 54.0 [48.0, 58.9] | 53.3 [51.4, 56.4] | 92.9 [89.9, 110.0] | 56.1 [54.2, 61.8] | 432.7 [380.1, 458.0] |
| compiler_2 | 86.1 [74.5, 93.5] | 84.3 [82.0, 91.1] | 276.3 [265.3, 324.0] | 163.6 [160.4, 174.5] | 558.0 [526.8, 594.8] |
| compiler_3 | 57.1 [48.2, 60.4] | 55.5 [52.9, 56.9] | 88.9 [83.8, 106.8] | 46.9 [43.9, 47.8] | 291.6 [251.7, 389.2] |
| compiler_4 | 53.3 [48.7, 56.3] | 53.0 [51.1, 56.4] | 88.6 [85.5, 109.7] | 51.2 [50.9, 51.8] | 223.1 [182.4, 306.2] |
| honk_1 | 54.2 [47.8, 59.3] | 56.1 [52.8, 60.4] | 86.0 [82.6, 92.7] | 55.5 [50.7, 58.2] | 154.8 [87.8, 395.4] |
| honk_2 | 60.8 [50.3, 67.6] | 57.9 [53.8, 63.5] | 88.2 [86.2, 93.1] | 68.3 [67.7, 73.6] | 207.4 [152.7, 337.9] |
| honk_3 | 61.8 [54.5, 67.8] | 60.2 [57.5, 63.0] | 107.3 [105.3, 116.7] | 96.5 [90.5, 102.2] | 249.8 [215.1, 436.8] |
| honk_4 | 75.6 [61.4, 80.6] | 70.4 [67.5, 74.8] | 177.9 [173.9, 188.0] | 134.8 [131.5, 141.5] | 305.1 [178.7, 559.1] |
| glob_1 | 40.4 [36.0, 44.4] | 38.9 [36.1, 45.5] | 76.5 [71.8, 81.0] | 75.2 [72.2, 81.1] | 199.3 [95.9, 337.7] |
| glob_2 | 51.2 [45.3, 54.6] | 50.0 [49.2, 53.1] | 115.9 [110.2, 124.5] | 105.5 [99.2, 107.7] | 156.2 [111.5, 162.6] |
| glob_3 | 39.6 [36.8, 42.0] | 40.1 [37.3, 41.5] | 66.6 [63.1, 70.1] | 73.3 [67.4, 79.6] | 108.1 [101.8, 118.2] |
| glob_4 | 49.9 [48.3, 52.8] | 50.0 [47.7, 55.1] | 125.9 [121.4, 135.1] | 276.4 [264.2, 292.5] | 410.3 [243.5, 447.8] |

### collection

| Workload | Alpha.5 | Alpha.4 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| wide | 1959.0 [1932.6, 2132.1] | 1999.9 [1951.2, 2173.2] | 3745.1 [3505.3, 3993.3] | 4070.7 [3975.0, 4483.9] | 5148.1 [5027.8, 5539.4] |
| deep | 3236.8 [3135.6, 3354.4] | 3396.7 [3218.5, 3469.3] | 3433.1 [3288.8, 3672.5] | 5714.3 [5383.4, 6143.9] | 6688.4 [6331.6, 7095.1] |

## Fresh frozen alpha.5 corpus

[Complete raw report](validation.json). Every cell is median **[minimum, maximum]**. Matching: ns/call; collection: µs/collection.

### oneshot

| Workload | Alpha.5 | Alpha.4 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| compiler_remaining_1 | 125.1 [119.4, 133.3] | 130.2 [124.6, 146.9] | 30664.8 [29512.4, 33923.1] | 172.8 [153.7, 189.1] | 18185.4 [13482.1, 19314.2] |
| compiler_remaining_2 | 100.2 [94.5, 101.7] | 100.1 [97.9, 115.5] | 26601.5 [24520.9, 30121.1] | 66.7 [58.2, 69.6] | 18110.8 [12233.5, 20984.3] |
| compiler_remaining_3 | 102.8 [95.1, 103.8] | 105.0 [100.6, 116.7] | 27011.6 [25335.1, 28936.6] | 68.6 [63.6, 90.0] | 25142.2 [14156.8, 26207.0] |
| compiler_remaining_4 | 105.1 [99.1, 114.2] | 107.1 [102.1, 115.9] | 31793.0 [29942.6, 32923.7] | 80.1 [76.9, 90.7] | 25724.6 [16189.7, 31695.4] |

### reused

| Workload | Alpha.5 | Alpha.4 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| compiler_remaining_1 | 85.9 [82.3, 90.0] | 84.3 [79.3, 91.6] | 218.2 [215.9, 240.5] | 169.7 [163.7, 178.4] | 553.6 [505.5, 578.6] |
| compiler_remaining_2 | 51.0 [48.2, 56.1] | 49.8 [48.2, 52.6] | 85.5 [80.8, 90.7] | 63.9 [58.5, 72.9] | 271.7 [215.6, 318.5] |
| compiler_remaining_3 | 51.2 [49.7, 55.4] | 50.6 [46.6, 54.8] | 86.9 [81.7, 91.6] | 60.5 [59.0, 65.0] | 336.6 [207.3, 444.1] |
| compiler_remaining_4 | 51.1 [46.8, 55.1] | 50.6 [45.5, 54.2] | 86.8 [85.0, 91.8] | 77.1 [72.2, 78.2] | 303.0 [160.0, 381.4] |

### collection

| Workload | Alpha.5 | Alpha.4 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| wide | 813.2 [742.4, 826.1] | 802.5 [723.5, 861.5] | 1182.6 [1078.5, 1219.5] | 1524.0 [1444.3, 1558.6] | 1437.7 [1380.8, 1561.9] |
| deep | 2531.8 [2251.0, 2657.7] | 2525.0 [2301.0, 2654.6] | 2516.0 [2394.2, 2640.0] | 4160.8 [3926.6, 4483.7] | 4302.5 [4175.6, 5083.5] |

## Correctness and scope

GCC/Clang interpreted, optimized/debug, ASan/UBSan, unknown-directory-type and filesystem-cap checks pass, alongside 7081 seeded differential cases through both matching APIs and eleven Python guard tests. Added cases cover escaped/class-contained stars and malformed syntax following a globstar. Independent standards and spec reviews found no actionable findings.

This is frozen in-project evidence, not blind third-party validation. Keep regression and fresh results together, including all slower outcomes. Reused matching and collection do not exercise the removed pass inside their timed loops. Honk already uses prepared patterns; these raw API improvements must not be projected onto its command latency.
