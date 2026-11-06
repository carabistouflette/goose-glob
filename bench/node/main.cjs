// SPDX-License-Identifier: Apache-2.0
const fs = require('node:fs');
const picomatch = require('picomatch');
const rows = fs.readFileSync(process.argv[2], 'utf8').trim().split('\n').map(s => s.split('\t'));
// Picomatch uses regex-style ^ for class negation; normalize once before timing.
for (const row of rows) row[1] = row[1].replaceAll('[!', '[^');
const count = Number(process.argv[3]), reused = process.argv[4] === 'reused';
const options = {dot:true, nobrace:true, noext:true, posixSlashes:true};
for (let start=0; start<rows.length;) {
  let end=start+1; while(end<rows.length && rows[end][0]===rows[start][0]) end++;
  const group=rows.slice(start,end), compiled=group.map(r=>picomatch(r[1], options));
  for(let j=0;j<group.length;j++) {
    if(compiled[j](group[j][2]) !== (group[j][3]==='1')) throw new Error(JSON.stringify(group[j]));
  }
  const match = j => reused ? compiled[j](group[j][2]) : picomatch(group[j][1], options)(group[j][2]);
  // JIT warmup is outside measured steady-state time for both modes.
  let warm=0; for(let i=0;i<20000;i++) warm+=Number(match(i%group.length));
  let expected=0; for(let i=0;i<count;i++) expected+=Number(group[i%group.length][3]==='1');
  let sum=0; const began=process.hrtime.bigint();
  for(let i=0;i<count;i++) sum+=Number(match(i%group.length));
  const elapsed=process.hrtime.bigint()-began;
  if(sum!==expected || warm<0) throw new Error('checksum');
  console.log(`${group[0][0]}\t${elapsed}\t${count}\t${sum}`); start=end;
}
