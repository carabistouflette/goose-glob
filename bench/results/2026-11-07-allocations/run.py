#!/usr/bin/env python3
"""Compare malloc-family and temporary-record counts; no latency measurements."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--baseline', type=Path, required=True)
p.add_argument('--instrumented', type=Path, required=True)
p.add_argument('--corpus', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--cpu', type=int, default=2)
a = p.parse_args()
a.output.mkdir(parents=True)  # Refuse to overwrite an earlier experiment.
inputs = {name: path.resolve() for name, path in vars(a).items() if name in ('baseline', 'instrumented', 'corpus')}
def hashes():
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in inputs.items()}
frozen = hashes()
os.sched_setaffinity(0, {a.cpu})
all_rows = inputs['corpus'].read_text().splitlines()
records = []
heap = []
for group in ('compiler_3', 'honk_1', 'glob_4'):
    rows = [r for r in all_rows if r.startswith(group+'\t')]
    assert rows, group
    fixture = a.output/f'{group}.tsv'
    fixture.write_text('\n'.join(rows)+'\n')
    fixture_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()
    for mode in ('oneshot', 'reused'):
        for cycles in (64, 128):
            count = len(rows)*cycles
            label = f'{group}-{mode}-{count}'
            assert hashes() == frozen
            assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture_hash
            with (a.output/f'{label}.log').open('w') as log:
                subprocess.run(['valgrind', '--tool=dhat', f'--dhat-out-file={a.output}/{label}.json', str(inputs['baseline']), str(fixture), str(count), mode], stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
            d = json.loads((a.output/f'{label}.json').read_text())
            heap.append({'group': group, 'mode': mode, 'calls': count, 'blocks': sum(x['tbk'] for x in d['pps']), 'bytes': sum(x['tb'] for x in d['pps']), 'live_at_end': sum(x['eb'] for x in d['pps'])})
            proc = subprocess.run([str(inputs['instrumented']), str(fixture), str(count), mode], capture_output=True, text=True, check=True, timeout=180)
            fields = proc.stderr.strip().split('\t')
            assert len(fields) == 7 and fields[0] == 'records', proc.stderr
            calls, parts, part_bytes, spans, span_bytes, maximum = map(int, fields[1:])
            assert calls == count
            result = proc.stdout.strip().split('\t')
            assert len(result) == 4 and result[0] == group and int(result[2]) == count
            assert int(result[3]) == cycles*sum(int(row.rsplit('\t', 1)[1]) for row in rows)
            records.append({'group': group, 'mode': mode, 'calls': calls, 'parts': parts, 'part_bytes': part_bytes, 'spans': spans, 'span_bytes': span_bytes, 'maximum_record_payload_per_call': maximum, 'per_call': {'parts': parts/calls, 'part_bytes': part_bytes/calls, 'spans': spans/calls, 'span_bytes': span_bytes/calls}})
            (a.output/f'{label}-records.log').write_text(proc.stderr)
    print(group, 'complete', flush=True)
assert hashes() == frozen
for name, data in (('records', records), ('heap', heap)):
    (a.output/f'{name}.json').write_text(json.dumps(data, indent=2)+'\n')
identity = {'sha256': frozen, 'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'cpu': a.cpu, 'valgrind': subprocess.check_output(['valgrind', '--version'], text=True).strip(), 'limits': 'Three earlier tuning groups; whole-process malloc-family counts include startup and IO. Temporary-record counters cover only the selected loop, after preparation. Mapping/commit events, native stack frames, whole RSS and latency are outside this profile.'}
(a.output/'run-identity.json').write_text(json.dumps(identity, indent=2)+'\n')
