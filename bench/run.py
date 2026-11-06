#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Sequential, CPU-affined steady-state benchmark with raw samples and provenance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import statistics
import subprocess
import time
import sys
import corpus

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.build/bench'


def call(cmd, **kwargs):
    return subprocess.run(list(map(str, cmd)), check=True, text=True, **kwargs)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inputs():
    files = [ROOT/'glob.goose', ROOT/'walk.goose', ROOT/'GOOSE_REVISION', ROOT/'glob.build']
    files += [p for p in (ROOT/'bench').rglob('*') if p.is_file() and
              not any(s in p.parts for s in ('node_modules', 'target', '__pycache__', 'results'))]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(files)}


def version(cmd):
    return call(cmd, capture_output=True).stdout.strip()


def prepare(args):
    OUT.mkdir(parents=True, exist_ok=True)
    corpus.write(OUT/'corpus.tsv')
    tree = OUT/'tree'
    tree.mkdir(exist_ok=True)
    expected = []
    for group in range(8):
        for leaf in range(4):
            directory = tree/f'group{group}'/f'leaf{leaf}'
            directory.mkdir(parents=True, exist_ok=True)
            for item in range(8):
                name = f'module{item}.' + ('goose' if item % 2 == 0 else 'txt')
                path = directory/name
                if not path.exists(): path.touch()
                if path.stat().st_size: raise SystemExit('Fixture contains unexpected data')
                if item % 2 == 0: expected.append(str(path.relative_to(tree)))
    (OUT/'walk-expected.txt').write_text(''.join(p+'\n' for p in sorted(expected)))
    goose = Path(args.goose).resolve()
    cc = Path(shutil.which(args.cc)).resolve()
    call([goose, 'build', ROOT/'bench/matcher.goose', '--cc', cc, '-O2', '-o', OUT/'goose'])
    # Same adapter/corpus against the original public implementation.
    reference = OUT/'reference'
    reference.mkdir(exist_ok=True)
    source = call(['git','-C',ROOT,'show', f'{args.reference}:glob.goose'],capture_output=True).stdout
    (reference/'glob.goose').write_text(source)
    adapter = (ROOT/'bench/baseline.goose').read_text().replace('from ".."', f'from "{reference}"')
    (OUT/'baseline.goose').write_text(adapter)
    call([goose, 'build', OUT/'baseline.goose', '--cc', cc, '-O2', '-o', OUT/'baseline'])
    (reference/'walk.goose').write_text(call(['git','-C',ROOT,'show', f'{args.reference}:walk.goose'],capture_output=True).stdout)
    (OUT/'baseline-walk.goose').write_text((ROOT/'bench/walk.goose').read_text().replace('from ".."', f'from "{reference}"'))
    call([goose, 'build', ROOT/'bench/walk.goose', '--cc', cc, '-O2', '-o', OUT/'goose-walk'])
    call([goose, 'build', OUT/'baseline-walk.goose', '--cc', cc, '-O2', '-o', OUT/'baseline-walk'])
    host = next(line[6:] for line in version(['rustc','-vV']).splitlines() if line.startswith('host: '))
    rust = call(['cargo','build','--locked','--release','--target',host,'--manifest-path',ROOT/'bench/rust/Cargo.toml',
                 '--target-dir',OUT/'rust','--message-format=json'],capture_output=True)
    artifacts = [json.loads(line) for line in rust.stdout.splitlines() if line.startswith('{')]
    executable = next(x['executable'] for x in artifacts if x.get('executable') and x.get('target',{}).get('name')=='glob-competitor')
    call(['go','build','-mod=readonly','-o',OUT/'go-competitor','.'],cwd=ROOT/'bench/go')
    call(['npm','ci','--ignore-scripts'],cwd=ROOT/'bench/node')
    commands = {'goose':[str(OUT/'goose')], 'baseline':[str(OUT/'baseline')],
                'rust':[executable], 'go':[str(OUT/'go-competitor')],
                'node':[shutil.which('node'),str(ROOT/'bench/node/main.cjs')]}
    tools = {str(p):digest(p) for p in [goose,cc,Path(commands['node'][0]),Path(shutil.which('go')).resolve(),Path(shutil.which('rustc')).resolve()]}
    manifest = {'source_hashes':inputs(), 'tools':tools, 'commands':commands,
        'binaries':{cmd[0]:digest(cmd[0]) for cmd in [*commands.values(), [str(OUT/'goose-walk')], [str(OUT/'baseline-walk')]]},
        'baseline_source_sha256':digest(reference/'glob.goose'), 'baseline_adapter_sha256':digest(OUT/'baseline.goose'),
        'corpus_sha256':digest(OUT/'corpus.tsv'), 'reference':version(['git','-C',str(ROOT),'rev-parse',args.reference]),
        'versions':{'goose':version([goose,'version']),'cc':version([cc,'--version']),
            'rust':version(['rustc','-vV']),'go':version(['go','version']),'node':version(['node','--version'])},
        'platform':platform.platform(), 'libc':platform.libc_ver(),
        'environment':{k:os.environ.get(k) for k in ('NODE_OPTIONS','GOFLAGS','GODEBUG','GOMAXPROCS','RUSTFLAGS','CARGO_BUILD_TARGET')},
        'node_dependencies':{str(p):digest(p) for p in (ROOT/'bench/node/node_modules').rglob('*') if p.is_file()}, 'cpuinfo':Path('/proc/cpuinfo').read_text(),
        'source_head':version(['git','-C',str(ROOT),'rev-parse','HEAD']),
        'source_status':version(['git','-C',str(ROOT),'status','--short'])}
    (OUT/'prepared.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def verify(manifest):
    if manifest['source_hashes'] != inputs(): raise SystemExit('Prepared source changed; prepare again')
    for group in ('tools','binaries','node_dependencies'):
        for path, sha in manifest[group].items():
            if digest(path) != sha: raise SystemExit(f'Prepared {group} changed: {path}')
    tree = OUT/'tree'
    files = sorted(tree.rglob('*'))
    regular = [p for p in files if p.is_file()]
    expected = (OUT/'walk-expected.txt').read_text().splitlines()
    if len(regular)!=256 or any(p.is_symlink() or p.stat().st_size for p in regular) or sorted(str(p.relative_to(tree)) for p in regular if p.suffix=='.goose') != expected:
        raise SystemExit('Collection fixture changed')
    if digest(OUT/'corpus.tsv') != manifest['corpus_sha256']: raise SystemExit('Corpus changed')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--goose',default=str(ROOT/'.toolchain/goose/build/goose'))
    parser.add_argument('--cc',default='gcc')
    parser.add_argument('--reference',default='4e8d7830e81b8ffd1c4d8ae2716ea93edc7ea8e3')
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--prepared',action='store_true')
    parser.add_argument('--rounds',type=int,default=7)
    parser.add_argument('--iterations',type=int,default=300000)
    parser.add_argument('--compile-iterations',type=int,default=5000)
    parser.add_argument('--walk-iterations',type=int,default=100)
    parser.add_argument('--cpu',type=int,default=2)
    parser.add_argument('--label',default='comparison')
    args=parser.parse_args()
    if min(args.rounds,args.iterations,args.compile_iterations,args.walk_iterations)<1: parser.error('positive counts required')
    if args.cpu not in os.sched_getaffinity(0): parser.error('CPU unavailable')
    manifest=json.loads((OUT/'prepared.json').read_text()) if args.prepared else prepare(args)
    verify(manifest)
    if args.prepare_only:
        print(OUT/'prepared.json');return
    os.sched_setaffinity(0,{args.cpu})
    tasks=[(engine,mode) for mode in ('oneshot','reused','walk') for engine in manifest['commands']]
    samples=[]; rng=random.Random(20261106)
    checkpoint=OUT/f'{args.label}.partial.json'
    checkpoint.write_text(json.dumps({'prepared':manifest,'args':vars(args),'samples':samples},indent=2)+'\n')
    for round_index in range(args.rounds):
        order=tasks.copy();rng.shuffle(order)
        for engine,mode in order:
            # Rust/JS parse+compile does substantially more work per call.
            count=args.compile_iterations if mode=='oneshot' and engine in ('rust','node') else args.iterations
            command = manifest['commands'][engine]
            fixture = OUT/'corpus.tsv'
            if mode == 'walk':
                count = args.walk_iterations
                fixture = OUT/'tree'
                if engine in ('goose','baseline'): command = [str(OUT/f'{engine}-walk')]
            start=time.monotonic_ns()
            proc=subprocess.run(list(map(str,[*command,fixture,count,mode])),capture_output=True,text=True,timeout=120)
            if proc.returncode:
                checkpoint.with_suffix('.stderr.txt').write_text(proc.stderr)
                raise SystemExit(f'{engine} {mode} failed: {proc.stderr}')
            elapsed=time.monotonic_ns()-start
            lines=proc.stdout.splitlines()
            if len(lines)!=(1 if mode=='walk' else 9): raise SystemExit(f'Missing workloads: {engine} {mode}')
            for line in lines:
                name,ns,n,checksum=line.split('\t');n=int(n);ns=int(ns);checksum=int(checksum)
                # Every fixture is exactly 64 alternating outcomes.
                expected_checksum = count*(128*1000003 + sum(len(p) for p in (OUT/'walk-expected.txt').read_text().splitlines())) if mode=='walk' else (count+1)//2
                if n!=count or checksum!=expected_checksum or ns<=0: raise SystemExit('Bad timed checksum/count')
                samples.append({'round':round_index,'engine':engine,'mode':mode,'workload':name,'elapsed_ns':ns,
                    'operations':n,'checksum':checksum,'ns_per_op':ns/n,'process_elapsed_ns':elapsed})
            checkpoint.write_text(json.dumps({'prepared':manifest,'args':vars(args),'samples':samples},indent=2)+'\n')
            print(f'{round_index+1}/{args.rounds} {engine} {mode}',flush=True)
    verify(manifest)
    summaries=[]
    for mode in ('oneshot','reused','walk'):
        for name in (['walk'] if mode=='walk' else dict.fromkeys(r[0] for r in corpus.rows())):
            values={}
            for engine in manifest['commands']:
                times=[s['ns_per_op'] for s in samples if (s['mode'],s['workload'],s['engine'])==(mode,name,engine)]
                values[engine]={'median':statistics.median(times),'min':min(times),'max':max(times)}
            summaries.append({'mode':mode,'workload':name,'engines':values})
    report={'recorded_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'args':vars(args),
        'prepared':manifest,'samples':samples,'summary':summaries,'limits':'Shared host; no speed claim outside these inputs/modes. Process startup and fixture IO excluded from matcher timing; traversal IO included from per-operation times; Node includes measured GC with explicit JIT warmup.'}
    path=OUT/f'{args.label}.json';path.write_text(json.dumps(report,indent=2)+'\n')
    for s in summaries:
        print(s['mode'],s['workload'],' '.join(f'{k}={v["median"]:.1f}' for k,v in s['engines'].items()))
    print(path)

if __name__=='__main__':main()
