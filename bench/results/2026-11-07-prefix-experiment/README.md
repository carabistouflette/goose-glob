# Rejected shared-prefix experiment — 2026-11-07

Decision: keep alpha.5 runtime unchanged. Moving the prepared literal-prefix rejection into the shared raw/prepared dispatch helped selected long-path misses but regressed several other workloads in two tuning probes. This does not justify a new release. No claim of statistical significance follows from these shared-host observations.

Each probe has seven shuffled rounds, two implementations, two modes and twelve earlier workloads: 336 samples per probe, 672 total. Every group receives 131072 calls per round, in identical path order. Both binaries assert expected results, statuses and checksums. Warm caches, CPU 2, uncontrolled host activity. Own heavy validation/build jobs finished before the repeat. The repeat driver checks binary/corpus hashes before each task and after the final task; the initial exploratory probe used the same counts/order seed but did not guard every task.

The baseline binary was built from `d6d6938baea52b47becbf0f32c50a474c2820fea`, whose matcher and collector bytes are identical to released alpha.5 (`02d7422d07469f1c483067a4d011698afbafbcc2`). The [prepared manifest](baseline-prepared.json) records its tools, binaries and dependencies. [Identity](identity.json) includes baseline/candidate matcher and binary hashes. The rejected candidate is exactly [this patch](rejected.patch), which is not applied to the released source.

Callgrind for 131072 one-shot compiler_3 calls on the baseline recorded 123939090 instructions. Pattern scanning accounted for 36.38% self instructions, byte search 18.98%, component scanning 13.36%, splitting 7.44%, and matching parts 6.24%. This motivated testing span-free prefix rejection for raw calls, reusing an existing prepared optimization. A source move can alter generated code and add dispatch work; these measurements do not isolate the cause of each regression.

Fresh [alpha.6 inputs](../../validation-alpha6.json) were committed at `702f0a8` before the experiment; SHA-256 `f62e05cfb1be5a4b5806837597ed495dd785851dbad8544d09cd61d5253e38f2`. Their 512 compiler paths are disjoint from all three earlier compiler selections. They have not been timed. Since the candidate failed the tuning screen, no fresh qualification or cross-library/collection campaign was run. The file name reserves inputs for a future candidate; no alpha.6 release exists.

## All tuning results

Each value is median **[minimum, maximum]** ns/call across seven rounds. Change is candidate/baseline − 1; positive means slower. Names refer to the earlier independent corpus, now tuning data.

### Initial probe

[Raw samples](initial.json).

#### oneshot

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| compiler_1 | 101.29 [97.78, 116.48] | 92.23 [88.64, 94.75] | -8.95% |
| compiler_2 | 126.60 [120.13, 137.66] | 134.31 [127.64, 157.51] | +6.09% |
| compiler_3 | 98.92 [93.51, 106.41] | 94.91 [93.38, 116.11] | -4.05% |
| compiler_4 | 101.66 [94.26, 106.67] | 94.96 [91.19, 114.91] | -6.60% |
| honk_1 | 86.08 [80.46, 88.60] | 85.00 [84.71, 102.70] | -1.25% |
| honk_2 | 115.27 [107.53, 118.69] | 108.96 [107.28, 120.68] | -5.48% |
| honk_3 | 114.86 [111.67, 118.71] | 118.13 [114.04, 136.13] | +2.84% |
| honk_4 | 112.82 [108.69, 119.47] | 119.95 [116.48, 139.57] | +6.32% |
| glob_1 | 67.54 [65.90, 70.81] | 72.13 [69.18, 81.33] | +6.80% |
| glob_2 | 86.36 [82.48, 91.12] | 91.31 [90.36, 109.59] | +5.72% |
| glob_3 | 86.91 [83.27, 88.27] | 89.81 [88.31, 109.98] | +3.34% |
| glob_4 | 72.70 [68.80, 73.85] | 73.58 [73.26, 87.49] | +1.21% |

#### reused

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| compiler_1 | 54.94 [53.69, 56.04] | 57.35 [52.74, 62.03] | +4.40% |
| compiler_2 | 85.05 [82.28, 94.26] | 89.07 [85.98, 105.38] | +4.73% |
| compiler_3 | 57.12 [53.61, 59.12] | 58.61 [56.90, 69.41] | +2.61% |
| compiler_4 | 53.58 [52.04, 56.85] | 56.59 [55.43, 61.99] | +5.61% |
| honk_1 | 55.65 [53.10, 59.84] | 57.99 [54.06, 62.22] | +4.20% |
| honk_2 | 59.46 [55.11, 63.53] | 59.55 [54.15, 65.80] | +0.15% |
| honk_3 | 60.98 [58.38, 63.94] | 61.33 [59.39, 69.48] | +0.57% |
| honk_4 | 75.92 [72.80, 80.16] | 73.51 [69.67, 77.77] | -3.17% |
| glob_1 | 41.39 [40.43, 43.31] | 42.34 [39.87, 43.79] | +2.29% |
| glob_2 | 53.71 [50.69, 57.56] | 54.06 [52.48, 55.52] | +0.66% |
| glob_3 | 42.10 [39.99, 42.79] | 42.37 [41.26, 43.79] | +0.64% |
| glob_4 | 52.77 [49.69, 56.51] | 53.71 [51.23, 54.01] | +1.79% |

### Repeat probe

[Raw samples](repeat.json).

#### oneshot

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| compiler_1 | 93.18 [92.01, 99.42] | 84.89 [84.53, 90.17] | -8.90% |
| compiler_2 | 119.07 [117.08, 125.01] | 123.44 [121.27, 131.58] | +3.67% |
| compiler_3 | 94.35 [93.78, 97.52] | 90.46 [87.48, 93.11] | -4.12% |
| compiler_4 | 95.83 [94.15, 99.96] | 88.62 [87.44, 90.64] | -7.52% |
| honk_1 | 84.17 [80.01, 89.04] | 80.09 [78.37, 87.89] | -4.84% |
| honk_2 | 110.61 [107.47, 115.47] | 103.61 [99.09, 105.84] | -6.33% |
| honk_3 | 110.55 [103.29, 115.31] | 109.94 [107.51, 120.01] | -0.56% |
| honk_4 | 109.46 [105.24, 118.12] | 112.09 [108.63, 116.55] | +2.41% |
| glob_1 | 65.36 [63.06, 67.86] | 66.59 [63.53, 69.22] | +1.88% |
| glob_2 | 81.29 [78.09, 86.10] | 86.02 [84.69, 90.77] | +5.82% |
| glob_3 | 83.77 [81.79, 89.08] | 86.21 [83.48, 90.72] | +2.92% |
| glob_4 | 68.68 [67.41, 69.36] | 69.37 [67.31, 73.74] | +1.01% |

#### reused

| Workload | Alpha.5 | Candidate | Change |
| --- | ---: | ---: | ---: |
| compiler_1 | 49.59 [48.81, 52.00] | 49.23 [48.87, 51.96] | -0.73% |
| compiler_2 | 82.30 [80.07, 83.53] | 81.47 [80.70, 85.37] | -1.01% |
| compiler_3 | 52.52 [52.05, 56.05] | 53.27 [52.26, 54.49] | +1.42% |
| compiler_4 | 51.14 [50.51, 51.52] | 51.58 [51.27, 53.44] | +0.85% |
| honk_1 | 53.10 [52.01, 56.12] | 52.00 [51.01, 56.45] | -2.07% |
| honk_2 | 57.90 [52.49, 59.00] | 55.86 [54.89, 58.48] | -3.53% |
| honk_3 | 57.18 [54.84, 58.21] | 58.96 [57.41, 62.91] | +3.11% |
| honk_4 | 69.92 [67.57, 72.95] | 69.34 [64.87, 72.15] | -0.83% |
| glob_1 | 39.06 [38.64, 39.39] | 39.36 [38.62, 40.37] | +0.77% |
| glob_2 | 49.46 [48.48, 49.91] | 49.13 [46.85, 54.69] | -0.66% |
| glob_3 | 38.97 [37.77, 39.93] | 39.12 [36.91, 40.57] | +0.40% |
| glob_4 | 49.29 [47.80, 52.03] | 49.71 [47.51, 52.27] | +0.86% |

## Validation and reproduction

The rejected patch passes GCC/Clang normal, optimized/debug and ASan/UBSan checks, 7081 differential cases and eleven Python guard tests. Added fuel-boundary cases cover long valid prefix misses at budgets 3 and 4, including a literal prefix lacking a following separator. After reverting the runtime patch, the final interpreter matcher suite also passes. The new tests remain; released matcher/collector source bytes stay unchanged.

To repeat: build `bench/matcher.goose` at alpha.5 using the pinned Goose compiler and GCC `-O2`, save that baseline binary, apply `rejected.patch`, then build the candidate. Generate corpus.tsv from `bench.independent.rows()` (tab-separated workload, pattern, path, expected). Run the retained `probe.py` with `--before`, `--candidate`, `--corpus` and a new `--output`; defaults are seven rounds, 131072 iterations and CPU 2. It refuses to overwrite an experiment. Run heavy builds/checks before measuring. Use `python3 render.py` to regenerate this report and the inline chart. This tuning driver does not replace the maintained full alternative-library qualification harness.
