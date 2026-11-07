#!/usr/bin/env python3
"""Render retained alpha.4 measurements; requires matplotlib 3.10.7."""
import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--directory',type=Path,default=Path(__file__).resolve().parent)
args=parser.parse_args();out=args.directory
series={name:json.loads((out/f'{name}.json').read_text()) for name in ('legacy','regression','validation')}
engines={'goose':'Alpha.4','baseline':'Alpha.3','rust':'Rust','go':'Go','node':'Node'}
titles={'legacy':'Legacy tuning corpus','regression':'Earlier corpus, now regression/tuning','validation':'Fresh frozen alpha.4 validation'}
lines=['# Alpha.4 qualification — 2026-11-07','',
       'Seven shuffled rounds on a shared Linux x86-64 host, CPU 2 and warm caches. Lower times are better. Every slower result and observed range is retained; lower medians do not establish statistical significance or a universal ranking.','',
       'The fresh corpus and collection geometry were frozen at `d5b86d1` before optimization, with SHA-256 `0197483c7e8058d056dfff86ba5d0ea6616bdfbac4bb206a171b950fcf552afa`. Its timings were first examined after candidate freeze and independent review. The two earlier corpora are now explicitly tuning/regression data.','',
       f'Measured candidate: `{series["validation"]["prepared"]["source_head"]}`. Reference: `1c2cb05988a253c8f9c4922659dd4a669e0b80cf`, whose runtime is identical to alpha.3. Later documentation/release commits may follow; the raw source hashes identify the actual matcher, collector, harness, binaries and tools.','',
       'Changes: long paths use std byte searches; prepared literal-prefix misses validate without retaining unused spans; collection reuses validated spans and first tries a 4 KiB listing before retrying the original 1 MiB/4096-entry bounded adaptive path. Short-path scalar scanning and exact work/error contracts are preserved. Large directories may incur one additional partial listing.','',
       '[Method and reproduction](../../README.md#alpha4-candidate-qualification) · [Fresh frozen inputs](../../validation-alpha4.json) · [Plot generator](render.py)','',
       'Rust globset 0.4.21/glob 0.3.4, Go doublestar 4.10.4, Node picomatch 4.0.7/fast-glob 3.3.3. One-shot includes pattern compilation; reused mode excludes compilation where supported (Go has no prepared API). All results/path sets are preflighted; source, dependency, binary, corpus and complete fixture maps are checked. Node uses explicit JIT warmup. Error and filesystem policies differ.','',
       'Own heavy correctness/build/profiling jobs finished before retained timings. Other host activity was uncontrolled. Matcher timers exclude process startup/input IO; collection includes traversal IO. Generated collection trees contain empty regular files. No cold-storage, security-equivalence or language-wide ranking follows.','',
       '## Summary','', '| Set | Samples | Lower medians vs alternatives | Fastest workload/mode cells | Lower medians vs alpha.3 |','| --- | ---: | ---: | ---: | ---: |']
scores={}
for name,data in series.items():
    rows=data['summary'];samples=data['samples'];groups=len(rows)
    for row in rows:
        for engine in engines:
            subset=[s for s in samples if (s['mode'],s['workload'],s['engine'])==(row['mode'],row['workload'],engine)]
            assert len(subset)==7,(name,row['mode'],row['workload'],engine)
    wins=sum(r['engines']['goose']['median']<r['engines'][e]['median'] for r in rows for e in ('rust','go','node'))
    best=sum(r['engines']['goose']['median']<min(r['engines'][e]['median'] for e in ('rust','go','node')) for r in rows)
    improved=sum(r['engines']['goose']['median']<r['engines']['baseline']['median'] for r in rows)
    scores[name]=dict(samples=len(samples),wins=wins,total=groups*3,best=best,cells=groups,improved=improved)
    lines.append(f'| {titles[name]} | {len(samples)} | {wins}/{groups*3} | {best}/{groups} | {improved}/{groups} |')
lines+=['','## Fresh matching workloads','','Real tracked path names only; these projects are not built or executed. Natural hit ratios, including all-negative groups, remain. All engines see identical path order and call counts within each mode.','','| Workload | Pattern | Paths | Hits |','| --- | --- | ---: | ---: |']
fresh=series['validation']
for source in fresh['sources']['sources']:
    for i,pattern in enumerate(source['patterns'],1):
        name=f'{source["name"]}_{i}';values=fresh['workloads'][name]
        lines.append(f'| {name} | `{pattern}` | {values["rows"]} | {values["hits"]} |')
lines+=['', 'Fresh collection geometry: wide has 112 directories, 1008 files and 336 matches; deep has 10 branches, 28 nested levels each, 840 files and 560 matches. The earlier regression fixture names/geometry are unchanged.','']
for name,data in series.items():
    lines += [f'## {titles[name]}','',f'[Complete raw report]({name}.json). Every cell shows median **[minimum, maximum]**. Matching units are ns/call; collection units are µs/collection.','']
    if name=='legacy':lines+=['Legacy calls per round: 65536 for Goose/Go one-shot and all reused engines; Rust/Node one-shot 2048; 64 collections. All matching groups have 64 rows and counts are exact full cycles, so path weights agree.','']
    else:lines+=['Calls per round for every engine: 8192 one-shot, 65536 reused, 32 collections; identical path sequence and weights within each mode.','']
    for mode in ('oneshot','reused','collection'):
        lines += [f'### {mode}','', '| Workload | Alpha.4 | Alpha.3 | Rust | Go | Node |','| --- | ---: | ---: | ---: | ---: | ---: |']
        for row in data['summary']:
            walk=row['mode'] in ('walk','wide','deep')
            if (mode=='collection' and not walk) or (mode!='collection' and row['mode']!=mode):continue
            scale=1000 if walk else 1;cells=[]
            for engine in engines:
                v=row['engines'][engine];cells.append(f'{v["median"]/scale:.1f} [{v["min"]/scale:.1f}, {v["max"]/scale:.1f}]')
            lines.append('| '+row['workload']+' | '+' | '.join(cells)+' |')
        lines.append('')
lines+=['## Correctness and scope','', 'GCC/Clang normal, optimized/debug and ASan/UBSan checks pass. The seeded model covers 7081 cases; 12160 alpha.3 comparisons cover exact hidden, fuel and invalid-path outcomes through both matching APIs. Listing tests cover exact 4 KiB, one byte above, large listings, original caps, unknown entry types and output clearing. Eleven Python guard tests pass. Independent spec review found no issues; the sole standards finding was stale staging documentation, corrected before measurement.','', 'This validation set is frozen in-project evidence, not blind third-party validation. Keep all three sets together: improvements in selected long-path and collection cases do not imply every short-path case improves. Honk command measurements belong to their separately identified combined-build report; matcher ratios must not be projected onto whole-command latency.','']
(out/'README.md').write_text('\n'.join(lines))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=fresh['summary'];fig,axes=plt.subplots(1,3,figsize=(15,6),gridspec_kw={'width_ratios':[1.3,1.3,1.15]})
for ax,mode,title in zip(axes[:2],('oneshot','reused'),('Parse + match','Reuse pattern')):
    selected=[r for r in rows if r['mode']==mode]
    values=[r['engines']['baseline']['median']/r['engines']['goose']['median'] for r in selected]
    ax.barh([r['workload'].replace('_',' ') for r in selected],values,color=['#287d59' if v>1 else '#b47b24' for v in values]);ax.axvline(1,color='#444',ls='--',lw=1);ax.invert_yaxis();ax.set_title(title);ax.set_xlabel('Alpha.3 time / alpha.4 time')
    for i,v in enumerate(values):ax.text(v+.015,i,f'{v:.2f}×',va='center',fontsize=8)
    ax.set_xlim(0,max(1.15,max(values)*1.18))
labels=[];values=[]
for row in rows:
    if row['mode'] in ('wide','deep'):
        for engine,label in engines.items():labels.append(row['mode']+' '+label);values.append(row['engines'][engine]['median']/1e6)
axes[2].barh(labels,values,color=['#287d59' if x.endswith('Alpha.4') else '#607b9b' for x in labels]);axes[2].invert_yaxis();axes[2].set_title('Fresh clean-tree collection');axes[2].set_xlabel('Milliseconds / collection (lower is better)')
fig.suptitle('Alpha.4: fresh validation, with wins and losses retained',fontsize=14);fig.text(.5,.012,'Seven shuffled rounds · shared host · warm caches · matching ratio >1 favors alpha.4 · full ranges in report',ha='center',fontsize=9);fig.tight_layout(rect=[0,.04,1,.95]);fig.savefig(out/'comparison.png',dpi=160);fig.savefig(out/'comparison.svg');plt.close(fig)
(out/'scores.json').write_text(json.dumps(scores,indent=2)+'\n')
print(json.dumps(scores,indent=2))
