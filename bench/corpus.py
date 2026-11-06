# SPDX-License-Identifier: Apache-2.0
"""Fixed common ASCII dialect, with positive/negative cases in every workload."""
import fnmatch
from functools import lru_cache


def reference(pattern, path):
    ps, ns = pattern.split('/'), path.split('/')
    @lru_cache(None)
    def match(p, n):
        if p == len(ps): return n == len(ns)
        if ps[p] == '**': return match(p + 1, n) or (n < len(ns) and match(p, n + 1))
        return n < len(ns) and fnmatch.fnmatchcase(ns[n], ps[p]) and match(p + 1, n + 1)
    return match(0, 0)


def rows():
    for i in range(64):
        n = i // 4
        hit = i % 2 == 0
        cases = [
            ('literal', f'src/pkg{n}/main.goose', f'src/pkg{n}/' + ('main.goose' if hit else 'other.goose')),
            ('suffix', '*.goose', f'module_{i}.' + ('goose' if hit else 'txt')),
            ('recursive_suffix', '**/*.goose', f'src/pkg{n}/deep/module_{i}.' + ('goose' if hit else 'txt')),
            ('prefix', f'prefix{n}*', f'prefix{n}_module_{i}' if hit else f'other{n}_module_{i}'),
            ('wildcards', f'pkg{n}/*/test_?.goose', f'pkg{n}/src/test_' + ('a.goose' if hit else 'ab.goose')),
            ('classes', 'src/[a-z][0-9]/file_[!0-9].goose', 'src/' + ('a3/file_x.goose' if hit else 'a3/file_5.goose')),
            ('globstar_middle', f'src/**/pkg{n}/main.goose', f'src/a/b/c/pkg{n}/' + ('main.goose' if hit else 'other.goose')),
            ('multiple_globstars', '**/src/**/test/*.goose', f'root/p{n}/src/a/b/test/' + ('x.goose' if hit else 'x.txt')),
            ('star_retry', '*a*a*a*a*b', 'a' * (24 + n) + ('b' if hit else 'c')),
        ]
        for name, pattern, path in cases:
            yield name, pattern, path, int(reference(pattern, path))


def write(path):
    data = list(rows())
    names = list(dict.fromkeys(row[0] for row in data))
    path.write_text(''.join('\t'.join(map(str, row)) + '\n' for name in names for row in data if row[0] == name))
