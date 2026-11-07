# Rejected pattern byte-search experiments — 2026-11-07

Decision: keep alpha.5. All three attempts to replace long scalar literal-run scans with std `find_any` regressed earlier real-path workloads. Synthetic long literals improved, but those targeted gains did not justify the real-path cost or another release. No runtime patch is applied.

Each set uses seven shuffled rounds, two implementations and two matching modes, with 131072 calls per workload/round on CPU 2. Three real-path sets have 336 samples each; two synthetic sets have 364 each: 1736 total. Every median, observed range and loss is retained. Warm caches, shared host and uncontrolled other activity; median differences do not establish statistical significance. Own heavy builds/checks did not overlap these probes.

Baseline runtime: released alpha.5 (`02d7422d07469f1c483067a4d011698afbafbcc2`). Its measured binary was built from d6d6938, whose matcher/collector bytes are identical. [Identities](identity.json) record source/binary hashes and the earlier complete tool/dependency manifest. Candidate patches: [search16](search16.patch), [guarded16](guarded16.patch), [search64](search64.patch). No API, class/escape dialect or work-budget changes were attempted.

The earlier profile attributed 36.38% of self instructions to pattern scanning. The first candidate calls std byte search when at least 16 pattern bytes remain and retains scalar scanning otherwise. The second additionally avoids search setup when the current byte is already syntax. The third raises the threshold to 64 bytes. The pinned std implementation can vectorize generic byte sets on supporting x86 hosts; runtime search/setup and the added branch can still cost more than scanning short runs. The observed regressions do not isolate a single machine-code cause.

The earlier real corpus is explicitly tuning data, not unseen validation. Its patterns are 7–21 bytes; no real case enters the 64-byte search branch, so its regressions also demonstrate the cost of dispatch/code changes rather than search itself. The [synthetic corpus](long.tsv) was added during tuning after the first candidate, and cannot establish an independent gain. It has thirteen literal pattern widths (15 through 1024 bytes), eight paths each and equal hit/miss weights. Matching path bytes are identical across engines and modes. Reused matching excludes parsing and is a control.

The existing fresh alpha.6 corpus stays unmeasured. These candidates failed the regression screen, so no fresh timing, alternative-library campaign, release, catalog or workspace pin update was justified.

## All results

Each entry is median **[minimum, maximum]** ns/call. Change is candidate/baseline − 1: negative is faster. The guarded variant did not receive a synthetic run after regressing every real one-shot group.

### 16-byte threshold, earlier real paths

[Raw measurements and input/driver hashes](probe16.json).

#### oneshot

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| compiler_1 | 94.44 [92.50, 99.11] | 109.09 [104.97, 112.26] | +15.51% |
| compiler_2 | 122.02 [118.96, 126.08] | 148.02 [143.98, 148.18] | +21.31% |
| compiler_3 | 96.26 [94.65, 98.06] | 103.65 [99.51, 105.76] | +7.68% |
| compiler_4 | 96.80 [95.24, 100.77] | 98.89 [97.43, 100.87] | +2.16% |
| honk_1 | 87.48 [81.41, 91.95] | 87.36 [84.87, 90.45] | -0.13% |
| honk_2 | 110.56 [106.08, 115.55] | 115.91 [114.76, 118.58] | +4.84% |
| honk_3 | 114.18 [110.95, 117.60] | 122.11 [117.93, 124.79] | +6.95% |
| honk_4 | 112.43 [111.03, 116.94] | 117.27 [116.17, 120.33] | +4.31% |
| glob_1 | 68.29 [65.83, 71.67] | 66.71 [63.86, 68.61] | -2.31% |
| glob_2 | 85.23 [81.66, 88.74] | 92.50 [89.52, 95.55] | +8.53% |
| glob_3 | 85.77 [82.84, 90.28] | 89.53 [87.02, 93.57] | +4.38% |
| glob_4 | 70.86 [69.40, 75.03] | 71.52 [70.27, 74.87] | +0.93% |

#### reused

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| compiler_1 | 51.08 [49.70, 53.13] | 51.17 [50.17, 53.17] | +0.17% |
| compiler_2 | 85.45 [80.16, 86.95] | 82.91 [80.15, 86.59] | -2.96% |
| compiler_3 | 54.12 [52.59, 55.34] | 54.98 [53.22, 58.09] | +1.60% |
| compiler_4 | 53.07 [50.97, 55.25] | 52.11 [51.29, 55.61] | -1.80% |
| honk_1 | 55.78 [53.62, 57.25] | 55.51 [54.14, 57.06] | -0.47% |
| honk_2 | 57.30 [54.04, 63.30] | 57.43 [52.97, 62.25] | +0.24% |
| honk_3 | 59.29 [57.44, 63.78] | 61.05 [57.00, 63.63] | +2.97% |
| honk_4 | 71.68 [70.77, 74.73] | 71.02 [68.90, 73.78] | -0.92% |
| glob_1 | 40.27 [39.46, 42.40] | 40.07 [39.12, 41.38] | -0.51% |
| glob_2 | 51.49 [48.88, 53.62] | 51.36 [50.36, 52.20] | -0.27% |
| glob_3 | 39.69 [39.03, 40.49] | 41.11 [40.22, 42.65] | +3.58% |
| glob_4 | 49.44 [48.52, 52.34] | 50.23 [48.62, 52.81] | +1.59% |

### 16-byte threshold with first-byte guard, earlier real paths

[Raw measurements and input/driver hashes](guarded16.json).

#### oneshot

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| compiler_1 | 98.64 [95.89, 106.84] | 112.10 [108.93, 116.45] | +13.64% |
| compiler_2 | 126.17 [119.15, 133.06] | 140.61 [136.17, 147.67] | +11.44% |
| compiler_3 | 99.67 [95.61, 106.66] | 112.86 [108.86, 116.46] | +13.23% |
| compiler_4 | 100.49 [97.88, 103.62] | 111.41 [104.66, 115.55] | +10.86% |
| honk_1 | 88.36 [83.00, 91.48] | 95.79 [91.11, 101.32] | +8.41% |
| honk_2 | 117.70 [111.48, 125.87] | 122.02 [119.91, 126.67] | +3.67% |
| honk_3 | 117.65 [110.88, 124.37] | 128.97 [124.99, 133.05] | +9.62% |
| honk_4 | 115.86 [108.06, 127.71] | 126.88 [125.19, 133.77] | +9.51% |
| glob_1 | 69.04 [66.80, 76.36] | 72.82 [72.38, 76.97] | +5.48% |
| glob_2 | 86.61 [82.54, 91.18] | 102.88 [99.06, 105.27] | +18.78% |
| glob_3 | 90.31 [84.60, 95.68] | 94.64 [91.93, 100.79] | +4.79% |
| glob_4 | 73.81 [71.75, 85.69] | 81.92 [76.96, 83.65] | +10.98% |

#### reused

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| compiler_1 | 55.19 [51.17, 60.16] | 53.88 [49.70, 59.18] | -2.37% |
| compiler_2 | 85.95 [83.70, 88.52] | 87.27 [83.50, 91.03] | +1.54% |
| compiler_3 | 56.29 [51.62, 58.42] | 57.92 [53.61, 60.40] | +2.89% |
| compiler_4 | 54.66 [53.40, 57.29] | 54.05 [52.30, 58.32] | -1.12% |
| honk_1 | 57.49 [52.70, 59.61] | 56.94 [52.29, 59.48] | -0.95% |
| honk_2 | 58.26 [54.29, 64.47] | 57.49 [54.52, 60.51] | -1.31% |
| honk_3 | 62.11 [58.49, 64.34] | 59.43 [54.86, 66.33] | -4.32% |
| honk_4 | 71.38 [69.18, 77.42] | 72.50 [67.61, 74.70] | +1.56% |
| glob_1 | 41.23 [40.73, 42.55] | 41.60 [40.33, 44.24] | +0.91% |
| glob_2 | 53.58 [51.15, 56.47] | 52.10 [50.83, 53.24] | -2.77% |
| glob_3 | 40.77 [39.02, 43.14] | 41.17 [39.72, 42.31] | +0.98% |
| glob_4 | 52.41 [50.07, 58.03] | 50.85 [48.21, 52.28] | -2.98% |

### 64-byte threshold, earlier real paths

[Raw measurements and input/driver hashes](probe64.json).

#### oneshot

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| compiler_1 | 102.94 [96.84, 104.97] | 106.45 [99.51, 109.51] | +3.41% |
| compiler_2 | 129.90 [119.85, 131.20] | 134.17 [127.77, 138.19] | +3.29% |
| compiler_3 | 102.79 [99.07, 103.73] | 109.31 [106.69, 112.87] | +6.34% |
| compiler_4 | 103.82 [98.03, 104.66] | 107.33 [100.43, 108.56] | +3.38% |
| honk_1 | 87.85 [81.27, 90.78] | 89.23 [84.80, 95.71] | +1.58% |
| honk_2 | 116.49 [110.13, 123.88] | 121.01 [112.26, 125.32] | +3.87% |
| honk_3 | 120.13 [111.41, 122.39] | 123.19 [120.53, 125.09] | +2.55% |
| honk_4 | 118.80 [110.04, 122.32] | 126.14 [123.26, 129.12] | +6.18% |
| glob_1 | 70.44 [66.42, 73.53] | 69.47 [69.02, 74.06] | -1.38% |
| glob_2 | 87.25 [82.87, 96.77] | 99.61 [97.86, 101.94] | +14.17% |
| glob_3 | 88.80 [83.94, 94.86] | 95.52 [92.91, 96.70] | +7.58% |
| glob_4 | 75.24 [70.38, 79.19] | 77.68 [75.42, 79.00] | +3.24% |

#### reused

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| compiler_1 | 57.10 [54.31, 58.17] | 56.76 [52.39, 59.26] | -0.60% |
| compiler_2 | 90.56 [87.26, 92.12] | 87.84 [82.51, 89.87] | -3.00% |
| compiler_3 | 58.80 [57.06, 60.14] | 57.04 [55.29, 59.96] | -3.00% |
| compiler_4 | 55.81 [54.44, 57.37] | 55.30 [53.03, 58.31] | -0.91% |
| honk_1 | 58.23 [55.14, 60.45] | 57.14 [54.90, 61.04] | -1.87% |
| honk_2 | 60.52 [57.34, 62.92] | 58.36 [56.64, 61.38] | -3.58% |
| honk_3 | 64.06 [59.26, 65.53] | 61.56 [59.45, 64.34] | -3.91% |
| honk_4 | 76.72 [73.12, 77.59] | 76.26 [69.91, 79.32] | -0.60% |
| glob_1 | 42.94 [41.93, 44.28] | 41.93 [40.16, 44.15] | -2.35% |
| glob_2 | 54.79 [53.35, 56.54] | 53.72 [52.91, 55.86] | -1.94% |
| glob_3 | 42.87 [40.67, 44.32] | 43.23 [42.22, 43.71] | +0.86% |
| glob_4 | 54.63 [52.91, 56.15] | 53.58 [49.60, 54.70] | -1.93% |

### 16-byte threshold, synthetic literal patterns

[Raw measurements and input/driver hashes](long16.json).

#### oneshot

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| literal_15 | 35.68 [34.96, 38.82] | 38.07 [36.69, 39.45] | +6.70% |
| literal_16 | 38.00 [36.62, 39.54] | 29.75 [28.18, 30.35] | -21.70% |
| literal_17 | 39.34 [38.55, 40.90] | 31.99 [31.46, 32.69] | -18.69% |
| literal_31 | 57.59 [56.78, 63.96] | 36.86 [35.84, 38.45] | -36.00% |
| literal_32 | 56.64 [55.49, 58.15] | 32.31 [31.33, 33.86] | -42.96% |
| literal_33 | 59.44 [56.17, 60.23] | 34.05 [31.93, 34.25] | -42.71% |
| literal_63 | 116.55 [111.91, 118.77] | 36.69 [36.19, 39.39] | -68.52% |
| literal_64 | 117.44 [113.64, 120.73] | 40.84 [39.17, 42.35] | -65.22% |
| literal_65 | 98.22 [94.59, 101.61] | 40.78 [39.58, 41.32] | -58.48% |
| literal_127 | 177.39 [172.58, 179.98] | 43.77 [43.34, 46.53] | -75.33% |
| literal_255 | 296.30 [287.57, 303.54] | 68.79 [66.67, 70.57] | -76.78% |
| literal_511 | 538.75 [534.70, 546.27] | 108.27 [107.41, 111.33] | -79.90% |
| literal_1024 | 1007.32 [991.55, 1019.97] | 233.48 [229.23, 239.55] | -76.82% |

#### reused

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| literal_15 | 18.83 [18.33, 19.77] | 18.81 [18.23, 19.55] | -0.10% |
| literal_16 | 18.97 [18.54, 20.47] | 18.94 [18.76, 19.98] | -0.17% |
| literal_17 | 20.67 [19.75, 21.20] | 19.95 [19.55, 20.94] | -3.50% |
| literal_31 | 24.43 [24.21, 26.34] | 24.01 [23.89, 25.56] | -1.70% |
| literal_32 | 21.11 [20.13, 21.39] | 19.92 [19.26, 21.09] | -5.66% |
| literal_33 | 21.34 [20.53, 21.99] | 21.60 [20.66, 22.29] | +1.21% |
| literal_63 | 23.32 [22.70, 26.33] | 22.27 [21.56, 23.69] | -4.50% |
| literal_64 | 25.39 [23.53, 26.54] | 24.22 [23.56, 25.34] | -4.60% |
| literal_65 | 25.04 [23.92, 27.04] | 24.55 [22.79, 25.58] | -1.94% |
| literal_127 | 28.55 [27.05, 29.00] | 27.17 [26.23, 28.22] | -4.81% |
| literal_255 | 37.73 [36.72, 39.38] | 37.72 [36.67, 39.40] | -0.03% |
| literal_511 | 45.97 [44.80, 46.92] | 45.84 [44.74, 47.82] | -0.28% |
| literal_1024 | 96.78 [94.55, 104.56] | 94.82 [88.45, 101.41] | -2.03% |

### 64-byte threshold, synthetic literal patterns

[Raw measurements and input/driver hashes](long64.json).

#### oneshot

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| literal_15 | 37.11 [36.23, 39.93] | 39.31 [36.30, 44.87] | +5.95% |
| literal_16 | 39.10 [38.12, 41.71] | 41.05 [38.91, 48.36] | +5.01% |
| literal_17 | 41.03 [40.03, 44.02] | 43.39 [42.24, 48.72] | +5.76% |
| literal_31 | 62.61 [56.66, 64.06] | 62.18 [59.53, 69.07] | -0.69% |
| literal_32 | 59.97 [55.92, 60.80] | 59.45 [56.80, 63.49] | -0.87% |
| literal_33 | 59.82 [57.08, 64.73] | 63.91 [58.93, 65.17] | +6.83% |
| literal_63 | 120.57 [113.41, 125.64] | 122.29 [112.56, 127.13] | +1.43% |
| literal_64 | 122.45 [118.71, 126.48] | 42.38 [39.53, 43.90] | -65.39% |
| literal_65 | 101.17 [96.14, 115.51] | 41.59 [39.66, 43.54] | -58.89% |
| literal_127 | 183.28 [173.67, 188.79] | 46.60 [44.27, 49.97] | -74.58% |
| literal_255 | 301.01 [289.28, 321.08] | 70.97 [66.52, 75.40] | -76.42% |
| literal_511 | 561.16 [539.29, 582.76] | 110.64 [105.57, 116.43] | -80.28% |
| literal_1024 | 1048.42 [1023.19, 1077.71] | 233.29 [226.47, 252.36] | -77.75% |

#### reused

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| literal_15 | 19.13 [18.31, 20.79] | 19.61 [18.44, 20.58] | +2.54% |
| literal_16 | 19.85 [18.52, 21.48] | 19.87 [18.66, 21.06] | +0.10% |
| literal_17 | 20.41 [19.73, 21.98] | 21.36 [20.03, 22.44] | +4.65% |
| literal_31 | 26.02 [24.13, 27.76] | 25.95 [24.01, 27.62] | -0.27% |
| literal_32 | 20.92 [19.57, 22.53] | 20.84 [19.98, 22.88] | -0.34% |
| literal_33 | 22.05 [20.27, 23.77] | 21.99 [20.43, 23.75] | -0.28% |
| literal_63 | 23.10 [22.00, 24.69] | 23.08 [21.74, 28.52] | -0.07% |
| literal_64 | 25.93 [24.29, 26.57] | 25.47 [24.90, 27.41] | -1.79% |
| literal_65 | 25.66 [24.12, 29.02] | 25.75 [23.86, 27.32] | +0.34% |
| literal_127 | 27.38 [26.42, 31.03] | 29.04 [26.75, 31.04] | +6.06% |
| literal_255 | 40.04 [37.13, 41.57] | 40.06 [37.54, 42.79] | +0.05% |
| literal_511 | 48.02 [45.14, 49.55] | 48.96 [45.73, 50.91] | +1.95% |
| literal_1024 | 100.19 [96.35, 103.84] | 97.68 [85.57, 109.78] | -2.50% |

## Validation and reproduction

Every timing task preflights results/statuses and asserts expected checksums inside the matcher executable. The paired Python driver guards both binary hashes and the corpus hash before every task and after the last task. These are exploratory timing screens, not full correctness qualification of the rejected candidates.

Final `glob.goose` and `walk.goose` bytes remain identical to alpha.5. New tests exercise long literal, escaped-star, wildcard and class patterns plus malformed escapes, classes, NUL and dot components at widths 15/16/17, 31/32/33, 63/64/65 and 127 through syntax checks and the public matching APIs. GCC normal/debug, ASan/UBSan, 7081 seeded differential cases and eleven Python guard tests qualify the retained baseline and new tests; hosted GCC/Clang CI is required before merge.

Build `bench/matcher.goose` at alpha.5 with the pinned Goose compiler and GCC `-O2`, save a baseline binary, apply one retained patch and build a candidate. Generate the earlier TSV with `bench.independent.rows()`, or use retained `long.tsv`. Run the [paired probe](../2026-11-07-prefix-experiment/probe.py) with `--before`, `--candidate`, `--corpus` and a new `--output`; defaults reproduce these counts and CPU. Each raw file records the driver hash. It refuses to overwrite an experiment. Run heavy builds/checks before timings. `python3 render.py` regenerates this report, its summary and the inline chart. The initial build hit a `/tmp` quota; measured binaries were built successfully with a private `TMPDIR` in the library build directory.
