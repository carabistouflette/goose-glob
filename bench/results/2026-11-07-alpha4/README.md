# Alpha.4 qualification — 2026-11-07

Seven shuffled rounds on a shared Linux x86-64 host, CPU 2 and warm caches. Lower times are better. Every slower result and observed range is retained; lower medians do not establish statistical significance or a universal ranking.

The fresh corpus and collection geometry were frozen at `d5b86d1` before optimization, with SHA-256 `0197483c7e8058d056dfff86ba5d0ea6616bdfbac4bb206a171b950fcf552afa`. Its timings were first examined after candidate freeze and independent review. The two earlier corpora are now explicitly tuning/regression data.

Measured candidate: `4c9e0f4090dbcbf9fb084eb5ce92a7ca291b11be`. Reference: `1c2cb05988a253c8f9c4922659dd4a669e0b80cf`, whose runtime is identical to alpha.3. Later documentation/release commits may follow; the raw source hashes identify the actual matcher, collector, harness, binaries and tools.

Changes: long paths use std byte searches; prepared literal-prefix misses validate without retaining unused spans; collection reuses validated spans and first tries a 4 KiB listing before retrying the original 1 MiB/4096-entry bounded adaptive path. Short-path scalar scanning and exact work/error contracts are preserved. Large directories may incur one additional partial listing.

[Method and reproduction](../../README.md#alpha4-candidate-qualification) · [Fresh frozen inputs](../../validation-alpha4.json) · [Plot generator](render.py) · [Interactive chart](comparison.html)

Rust globset 0.4.21/glob 0.3.4, Go doublestar 4.10.4, Node picomatch 4.0.7/fast-glob 3.3.3. One-shot includes pattern compilation; reused mode excludes compilation where supported (Go has no prepared API). All results/path sets are preflighted; source, dependency, binary, corpus and complete fixture maps are checked. Node uses explicit JIT warmup. Error and filesystem policies differ.

Own heavy correctness/build/profiling jobs finished before retained timings. Other host activity was uncontrolled. Matcher timers exclude process startup/input IO; collection includes traversal IO. Generated collection trees contain empty regular files. No cold-storage, security-equivalence or language-wide ranking follows.

## Summary

| Set | Samples | Lower medians vs alternatives | Lower than all three alternatives | Lower medians vs alpha.3 |
| --- | ---: | ---: | ---: | ---: |
| Legacy tuning corpus | 665 | 57/57 | 19/19 | 6/19 |
| Earlier corpus, now regression/tuning | 910 | 68/78 | 16/26 | 16/26 |
| Fresh frozen alpha.4 validation | 910 | 68/78 | 16/26 | 18/26 |

## Fresh matching workloads

Real tracked path names only; these projects are not built or executed. Natural hit ratios, including all-negative groups, remain. All engines see identical path order and call counts within each mode.

| Workload | Pattern | Paths | Hits |
| --- | --- | ---: | ---: |
| compiler_extra_1 | `samples/**/m*.goose` | 768 | 0 |
| compiler_extra_2 | `test/**/t[ab]*.goose` | 768 | 1 |
| compiler_extra_3 | `src/**/a*.[ch]` | 768 | 0 |
| compiler_extra_4 | `**/README.*` | 768 | 2 |
| fs_1 | `native/*.[ch]` | 251 | 4 |
| fs_2 | `tests/**/f*.goose` | 251 | 1 |
| fs_3 | `examples/*_*.goose` | 251 | 0 |
| fs_4 | `docs/**/[a-z]*.md` | 251 | 2 |
| crypto_1 | `tests/[a-z]*.goose` | 79 | 3 |
| crypto_2 | `native/**/s*.[ch]` | 79 | 0 |
| crypto_3 | `examples/**/h*.goose` | 79 | 1 |
| crypto_4 | `**/*_*.*` | 79 | 1 |

Fresh collection geometry: wide has 112 directories, 1008 files and 336 matches; deep has 10 branches, 28 nested levels each, 840 files and 560 matches. The earlier regression fixture names/geometry are unchanged.

## Legacy tuning corpus

[Complete raw report](legacy.json). Every cell shows median **[minimum, maximum]**. Matching units are ns/call; collection units are µs/collection.

Legacy calls per round: 65536 for Goose/Go one-shot and all reused engines; Rust/Node one-shot 2048; 64 collections. All matching groups have 64 rows and counts are exact full cycles, so path weights agree.

### oneshot

| Workload | Alpha.4 | Alpha.3 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| literal | 67.1 [64.1, 70.1] | 65.5 [63.1, 67.7] | 23333.5 [22844.0, 27210.5] | 142.9 [134.3, 188.3] | 10465.5 [7123.3, 13020.0] |
| suffix | 42.6 [40.4, 47.6] | 42.3 [40.1, 43.4] | 21460.5 [20582.6, 22604.7] | 157.1 [151.4, 204.5] | 3646.5 [1783.9, 6445.4] |
| recursive_suffix | 90.3 [86.4, 92.8] | 90.8 [83.1, 93.8] | 31704.2 [30437.9, 34871.5] | 348.7 [331.2, 454.9] | 3913.1 [3552.2, 5906.5] |
| prefix | 37.1 [34.9, 40.2] | 37.5 [35.4, 38.5] | 21586.9 [20511.8, 26967.9] | 66.9 [62.4, 92.5] | 33481.9 [32343.5, 37056.9] |
| wildcards | 127.6 [121.8, 132.3] | 122.2 [116.1, 124.9] | 33232.0 [31876.4, 42805.0] | 180.0 [171.6, 248.6] | 15546.6 [9714.5, 40672.5] |
| classes | 155.6 [150.2, 162.5] | 153.1 [145.8, 163.6] | 33737.6 [32112.9, 44853.9] | 194.7 [186.2, 256.2] | 16158.3 [10115.9, 38757.5] |
| globstar_middle | 120.4 [119.2, 148.7] | 125.2 [120.3, 130.1] | 35902.7 [34718.0, 49066.4] | 220.5 [208.9, 262.0] | 31303.7 [11297.7, 33335.8] |
| multiple_globstars | 182.9 [173.2, 215.5] | 181.1 [174.5, 205.9] | 47955.9 [46107.6, 61751.9] | 245.0 [233.9, 270.2] | 23236.6 [12711.9, 38675.8] |
| star_retry | 67.4 [63.6, 82.4] | 69.5 [63.8, 79.8] | 33232.2 [31217.7, 40151.2] | 366.7 [353.9, 413.1] | 286993.9 [270426.0, 340307.9] |

### reused

| Workload | Alpha.4 | Alpha.3 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| literal | 24.5 [24.3, 26.4] | 23.9 [22.9, 29.7] | 129.0 [123.7, 132.9] | 143.6 [142.5, 146.8] | 375.2 [329.3, 434.4] |
| suffix | 33.7 [32.5, 36.2] | 32.9 [30.9, 41.1] | 124.3 [119.7, 125.7] | 158.2 [153.2, 163.2] | 470.3 [450.5, 489.6] |
| recursive_suffix | 62.3 [60.0, 69.2] | 61.2 [59.5, 78.8] | 158.3 [148.8, 162.6] | 344.9 [335.6, 347.0] | 420.8 [376.6, 522.3] |
| prefix | 25.2 [23.3, 29.0] | 23.2 [21.1, 29.4] | 108.6 [103.8, 113.5] | 64.6 [62.6, 67.0] | 294.4 [230.7, 332.2] |
| wildcards | 83.6 [79.3, 97.2] | 82.9 [80.0, 102.6] | 175.3 [165.3, 184.3] | 175.6 [170.3, 180.0] | 332.8 [270.3, 518.7] |
| classes | 105.7 [98.1, 128.6] | 102.9 [101.2, 137.4] | 167.5 [158.3, 179.0] | 194.5 [189.2, 201.8] | 280.5 [96.9, 490.9] |
| globstar_middle | 74.5 [70.2, 94.2] | 74.8 [71.4, 94.0] | 215.7 [210.3, 227.1] | 219.6 [210.9, 223.2] | 366.6 [173.5, 411.8] |
| multiple_globstars | 113.2 [109.2, 141.9] | 110.4 [109.7, 138.7] | 216.4 [210.3, 226.8] | 239.7 [232.9, 249.3] | 212.3 [198.2, 327.4] |
| star_retry | 40.0 [38.6, 51.1] | 39.6 [38.2, 46.7] | 154.5 [150.4, 159.0] | 371.8 [353.1, 378.0] | 276609.2 [269682.0, 279073.3] |

### collection

| Workload | Alpha.4 | Alpha.3 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| walk | 489.5 [458.7, 644.6] | 585.0 [575.7, 687.0] | 779.2 [739.0, 959.2] | 866.4 [846.9, 947.0] | 1502.9 [1460.0, 1809.0] |

## Earlier corpus, now regression/tuning

[Complete raw report](regression.json). Every cell shows median **[minimum, maximum]**. Matching units are ns/call; collection units are µs/collection.

Calls per round for every engine: 8192 one-shot, 65536 reused, 32 collections; identical path sequence and weights within each mode.

### oneshot

| Workload | Alpha.4 | Alpha.3 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| compiler_1 | 111.6 [103.8, 135.1] | 131.7 [122.9, 179.4] | 27962.3 [25964.1, 35192.1] | 62.7 [57.7, 69.1] | 9395.3 [8537.7, 11987.9] |
| compiler_2 | 133.3 [124.8, 166.9] | 153.1 [145.9, 210.7] | 34363.6 [33200.1, 48062.7] | 189.9 [175.8, 202.2] | 17218.2 [16227.2, 17539.9] |
| compiler_3 | 107.8 [100.2, 132.8] | 121.5 [118.6, 174.7] | 27309.1 [25680.4, 32580.2] | 53.6 [49.6, 58.3] | 15807.8 [10274.4, 21362.5] |
| compiler_4 | 108.2 [100.6, 134.0] | 124.6 [120.5, 176.2] | 25554.1 [24917.6, 33897.7] | 57.8 [53.3, 58.8] | 15241.9 [13717.5, 28924.6] |
| honk_1 | 104.0 [88.2, 122.0] | 95.2 [91.9, 130.5] | 20480.1 [19903.9, 21701.0] | 57.8 [56.1, 60.4] | 13350.6 [9185.3, 13648.4] |
| honk_2 | 124.9 [117.1, 159.1] | 115.6 [112.1, 161.2] | 27692.5 [27342.1, 28667.5] | 72.3 [68.0, 78.7] | 18001.5 [13242.2, 24582.2] |
| honk_3 | 126.9 [118.0, 154.7] | 118.1 [115.1, 174.2] | 29535.4 [29189.5, 32863.0] | 103.1 [97.3, 109.9] | 23162.4 [12324.0, 28988.1] |
| honk_4 | 128.2 [118.9, 159.5] | 120.5 [115.8, 156.7] | 29307.1 [28929.8, 30647.0] | 145.1 [136.9, 147.4] | 18814.4 [17742.1, 22390.1] |
| glob_1 | 69.6 [67.6, 90.3] | 68.9 [61.4, 83.2] | 20888.0 [20319.7, 24478.0] | 79.8 [75.9, 81.1] | 14131.9 [9036.5, 18785.3] |
| glob_2 | 92.9 [83.5, 117.7] | 89.9 [81.7, 109.6] | 29641.9 [28481.1, 38841.0] | 113.9 [106.5, 116.6] | 18127.4 [14637.2, 23999.4] |
| glob_3 | 99.8 [91.0, 134.0] | 91.9 [87.1, 126.8] | 28321.0 [27426.0, 36549.3] | 75.9 [74.8, 82.2] | 28987.2 [17602.5, 32845.3] |
| glob_4 | 76.8 [72.9, 95.3] | 80.4 [73.0, 92.5] | 27807.5 [26701.9, 33311.1] | 297.4 [295.0, 309.6] | 4577.7 [4362.5, 6661.4] |

### reused

| Workload | Alpha.4 | Alpha.3 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| compiler_1 | 53.7 [51.0, 72.9] | 89.2 [79.2, 110.1] | 93.2 [90.0, 110.2] | 60.6 [56.7, 75.9] | 475.1 [413.4, 478.9] |
| compiler_2 | 85.2 [80.9, 110.2] | 97.5 [89.7, 128.5] | 277.6 [261.2, 333.7] | 172.8 [164.6, 219.0] | 584.9 [533.3, 656.9] |
| compiler_3 | 55.9 [52.9, 71.2] | 82.4 [78.2, 108.3] | 87.4 [84.5, 115.8] | 47.2 [46.4, 63.9] | 248.6 [241.3, 337.4] |
| compiler_4 | 53.9 [50.9, 70.7] | 88.1 [80.1, 113.4] | 91.8 [85.2, 107.0] | 51.5 [51.1, 70.3] | 286.0 [197.7, 549.6] |
| honk_1 | 54.1 [52.5, 71.8] | 63.4 [54.8, 78.7] | 88.9 [83.6, 101.4] | 55.2 [53.7, 73.7] | 170.2 [80.5, 468.5] |
| honk_2 | 56.6 [53.8, 74.3] | 64.6 [61.2, 87.2] | 91.5 [88.5, 107.0] | 70.2 [68.1, 92.9] | 254.8 [197.9, 593.3] |
| honk_3 | 59.9 [57.2, 79.1] | 69.3 [64.4, 95.8] | 111.6 [107.1, 148.8] | 98.0 [96.6, 128.3] | 296.3 [154.7, 565.0] |
| honk_4 | 73.9 [68.5, 86.5] | 67.9 [65.4, 94.2] | 182.0 [174.1, 231.4] | 136.9 [136.4, 184.3] | 303.3 [135.8, 405.5] |
| glob_1 | 40.2 [38.1, 47.5] | 40.8 [38.5, 55.8] | 79.0 [75.2, 100.5] | 76.4 [74.0, 100.4] | 233.7 [100.8, 333.5] |
| glob_2 | 51.3 [49.0, 57.1] | 49.5 [46.8, 67.6] | 125.1 [117.6, 164.7] | 109.0 [106.4, 142.8] | 160.8 [151.2, 183.8] |
| glob_3 | 38.7 [37.6, 46.8] | 41.2 [39.1, 56.6] | 66.6 [64.6, 92.8] | 76.7 [72.1, 99.9] | 108.5 [102.0, 144.9] |
| glob_4 | 51.6 [47.6, 54.1] | 49.6 [47.3, 65.6] | 129.9 [123.1, 177.2] | 293.4 [282.8, 364.9] | 462.8 [316.3, 480.5] |

### collection

| Workload | Alpha.4 | Alpha.3 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| wide | 2067.6 [2003.4, 2423.0] | 2508.1 [2482.3, 2594.1] | 3772.8 [3665.3, 4911.0] | 4283.9 [4150.7, 4539.3] | 5480.9 [5155.7, 6624.1] |
| deep | 3517.7 [3279.1, 3861.8] | 4110.8 [3986.9, 4431.8] | 3478.2 [3414.3, 3570.9] | 5933.0 [5610.9, 6339.1] | 6965.4 [6899.8, 8203.9] |

## Fresh frozen alpha.4 validation

[Complete raw report](validation.json). Every cell shows median **[minimum, maximum]**. Matching units are ns/call; collection units are µs/collection.

Calls per round for every engine: 8192 one-shot, 65536 reused, 32 collections; identical path sequence and weights within each mode.

### oneshot

| Workload | Alpha.4 | Alpha.3 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| compiler_extra_1 | 112.5 [108.6, 148.7] | 131.7 [122.3, 166.1] | 27498.5 [27178.7, 38155.8] | 71.4 [66.5, 73.1] | 10332.4 [9213.5, 16930.1] |
| compiler_extra_2 | 144.1 [133.8, 180.7] | 158.4 [150.3, 193.9] | 34899.5 [33250.1, 40375.5] | 187.4 [181.1, 197.2] | 17506.7 [16882.0, 24812.1] |
| compiler_extra_3 | 113.6 [103.1, 139.6] | 132.9 [121.2, 172.3] | 27962.3 [27010.9, 28764.0] | 62.3 [58.9, 70.7] | 14711.7 [9929.7, 18392.3] |
| compiler_extra_4 | 101.9 [95.2, 128.0] | 116.6 [111.8, 149.5] | 27253.3 [26132.8, 27993.8] | 155.8 [145.1, 162.3] | 15083.4 [9798.7, 23136.4] |
| fs_1 | 97.0 [89.2, 119.1] | 98.7 [90.9, 125.4] | 21773.6 [21073.0, 29062.6] | 51.3 [47.4, 52.3] | 18046.7 [13988.5, 24360.6] |
| fs_2 | 125.9 [115.3, 165.9] | 128.0 [119.0, 167.5] | 28303.4 [27994.2, 37084.0] | 95.2 [89.8, 97.2] | 21017.3 [9168.9, 23351.3] |
| fs_3 | 105.6 [97.6, 128.7] | 101.6 [94.4, 127.4] | 24329.5 [23416.4, 30223.2] | 64.5 [59.0, 67.6] | 16089.6 [11952.3, 20354.8] |
| fs_4 | 120.7 [110.2, 149.7] | 120.0 [113.9, 146.8] | 26685.3 [26161.8, 35593.0] | 73.5 [68.1, 76.3] | 17337.3 [12745.1, 21850.7] |
| crypto_1 | 95.9 [82.2, 113.1] | 87.4 [79.2, 108.6] | 22748.9 [22119.5, 26920.1] | 92.2 [88.2, 107.2] | 17367.4 [12149.9, 22905.5] |
| crypto_2 | 104.9 [96.8, 137.2] | 101.9 [96.0, 127.2] | 28832.2 [28210.7, 30364.9] | 60.8 [56.4, 79.8] | 29230.6 [22788.2, 30497.2] |
| crypto_3 | 106.5 [103.1, 136.3] | 104.8 [101.2, 139.9] | 30594.1 [30080.3, 35974.8] | 146.9 [138.5, 157.2] | 21147.5 [14226.1, 24730.5] |
| crypto_4 | 103.4 [100.8, 134.4] | 113.5 [99.9, 136.8] | 31413.1 [30836.6, 38889.9] | 426.2 [397.3, 446.0] | 20368.2 [14782.1, 26095.0] |

### reused

| Workload | Alpha.4 | Alpha.3 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| compiler_extra_1 | 55.9 [52.4, 72.4] | 80.7 [76.9, 98.9] | 103.7 [93.7, 120.7] | 69.2 [66.2, 88.7] | 385.4 [365.2, 463.3] |
| compiler_extra_2 | 90.4 [81.4, 109.3] | 93.5 [90.2, 106.8] | 282.2 [279.6, 360.9] | 164.8 [162.6, 210.6] | 612.3 [525.7, 704.8] |
| compiler_extra_3 | 59.4 [56.2, 73.2] | 80.0 [78.1, 97.3] | 92.6 [86.7, 96.1] | 54.7 [52.5, 66.7] | 471.6 [362.8, 1115.4] |
| compiler_extra_4 | 77.8 [72.6, 94.5] | 88.7 [82.3, 104.4] | 214.7 [210.0, 226.7] | 133.0 [130.8, 170.6] | 552.8 [457.6, 673.9] |
| fs_1 | 55.7 [53.0, 69.4] | 58.0 [55.4, 69.4] | 81.9 [78.7, 90.8] | 49.2 [45.9, 62.0] | 408.7 [187.3, 892.4] |
| fs_2 | 58.3 [52.2, 73.6] | 68.9 [63.4, 72.6] | 99.3 [96.8, 106.2] | 87.6 [83.4, 113.7] | 251.7 [200.7, 633.8] |
| fs_3 | 50.7 [49.4, 66.8] | 54.3 [51.2, 62.6] | 77.5 [76.3, 83.3] | 62.7 [59.1, 81.6] | 233.1 [190.6, 371.6] |
| fs_4 | 57.0 [51.5, 69.8] | 62.8 [59.7, 74.1] | 86.1 [83.6, 88.8] | 70.2 [66.6, 93.1] | 320.1 [231.3, 652.7] |
| crypto_1 | 50.9 [45.6, 62.5] | 46.7 [44.5, 58.6] | 78.0 [76.7, 80.5] | 94.6 [90.2, 119.8] | 210.0 [135.7, 362.4] |
| crypto_2 | 45.7 [43.7, 57.8] | 52.4 [46.5, 56.6] | 74.1 [70.8, 78.3] | 62.5 [59.2, 82.2] | 161.6 [96.0, 264.5] |
| crypto_3 | 56.0 [55.6, 72.9] | 54.1 [49.6, 65.9] | 147.1 [139.7, 153.8] | 144.4 [139.5, 175.7] | 153.7 [131.8, 169.5] |
| crypto_4 | 71.4 [70.5, 91.3] | 70.7 [66.6, 81.1] | 148.8 [140.0, 150.5] | 405.6 [389.8, 434.3] | 210.7 [198.4, 254.9] |

### collection

| Workload | Alpha.4 | Alpha.3 | Rust | Go | Node |
| --- | ---: | ---: | ---: | ---: | ---: |
| wide | 1224.0 [1194.6, 1516.9] | 1536.2 [1473.6, 1794.9] | 2325.1 [2242.4, 2774.1] | 2731.4 [2593.7, 3487.4] | 3742.9 [3508.3, 4330.0] |
| deep | 3640.7 [3428.6, 3879.8] | 4252.3 [3944.3, 5437.6] | 4665.4 [4589.4, 5509.5] | 6309.0 [6039.7, 7662.0] | 7647.0 [7592.6, 9787.7] |

## Correctness and scope

GCC/Clang normal, optimized/debug and ASan/UBSan checks pass. The seeded model covers 7081 cases; 12160 alpha.3 comparisons cover exact hidden, fuel and invalid-path outcomes through both matching APIs. Listing tests cover exact 4 KiB, one byte above, large listings, original caps, unknown entry types and output clearing. Eleven Python guard tests pass. Independent spec review found no issues; the sole standards finding was stale staging documentation, corrected before measurement.

This validation set is frozen in-project evidence, not blind third-party validation. Keep all three sets together: improvements in selected long-path and collection cases do not imply every short-path case improves. Honk command measurements belong to their separately identified combined-build report; matcher ratios must not be projected onto whole-command latency.
