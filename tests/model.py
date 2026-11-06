#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Compare against Python fnmatch plus a component-level recursive oracle."""
import fnmatch
from functools import lru_cache
import itertools
import random
import subprocess
import sys


def reference(pattern, path):
    patterns, names = pattern.split("/"), path.split("/")

    @lru_cache(None)
    def match(p, n):
        if p == len(patterns):
            return n == len(names)
        if patterns[p] == "**":
            return match(p + 1, n) or (n < len(names) and match(p, n + 1))
        return n < len(names) and fnmatch.fnmatchcase(names[n].encode(), patterns[p].encode()) and match(p + 1, n + 1)

    return match(0, 0)


rng = random.Random(20261106)
patterns = ["*", "?", "a", "b", "a*", "*b", "a?", "[ab]", "[!a]", "[a-c]", "**"]
names = ["a", "b", "c", "aa", "ab", "ba", ".a", "é"]
cases = list(itertools.product(patterns, names))
for _ in range(2000):
    cases.append(("/".join(rng.choices(patterns, k=rng.randint(1, 5))),
                  "/".join(rng.choices(names, k=rng.randint(1, 5)))))
for pattern, path in cases:
    result = subprocess.run([sys.argv[1], pattern, path], check=True, capture_output=True, timeout=5)
    expected = "1" if reference(pattern, path) else "0"
    assert result.stdout.decode().strip() == expected, (pattern, path, expected, result.stdout)
print(f"{len(cases)} differential cases passed (seed 20261106)")
