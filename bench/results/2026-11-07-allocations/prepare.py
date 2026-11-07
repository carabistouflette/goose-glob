#!/usr/bin/env python3
"""Create a private counter-instrumented matcher without editing the library."""
import argparse
from pathlib import Path
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True)  # Refuse to overwrite an earlier preparation.
root = Path(__file__).resolve().parents[3]
source = (root/'bench/matcher.goose').read_text()
source = source.replace('import glob from "..";', f'import glob from "{root}";')
source = source.replace('struct Row {', 'extern fn allocation_reset() = "allocation_reset";\nextern fn allocation_begin() = "allocation_begin";\nextern fn allocation_end() = "allocation_end";\nextern fn allocation_report(calls: i64) = "allocation_report";\nstruct Row {')
source = source.replace('    let start = clock_ns();', '    allocation_reset();\n    let start = clock_ns();')
source = source.replace('        let matched, status = selected(mode, row, refs, i % rows.len);', '        allocation_begin();\n        let matched, status = selected(mode, row, refs, i % rows.len);\n        allocation_end();')
source = source.replace('    assert(checksum == expected);', '    assert(checksum == expected);\n    allocation_report(iterations);')
for symbol, count in (('allocation_reset();', 1), ('allocation_begin();', 1), ('allocation_end();', 1), ('allocation_report(iterations);', 1)):
    assert source.count(symbol) == count, f'benchmark changed: {symbol}'
(a.output/'matcher.goose').write_text(source)
for name in ('counters.h', 'profile-cc.py'):
    shutil.copyfile(Path(__file__).with_name(name), a.output/name)
(a.output/'profile-cc.py').chmod(0o755)
print(a.output/'matcher.goose')
