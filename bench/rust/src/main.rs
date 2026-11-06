// SPDX-License-Identifier: Apache-2.0
use globset::{GlobBuilder, GlobMatcher};
use std::{env, fs, hint::black_box, time::Instant};
fn matcher(p: &str) -> GlobMatcher {
    GlobBuilder::new(p).literal_separator(true).backslash_escape(true)
        .build().unwrap().compile_matcher()
}
fn main() {
    let args: Vec<_> = env::args().collect();
    let data = fs::read_to_string(&args[1]).unwrap();
    let iterations: usize = args[2].parse().unwrap();
    let reused = args[3] == "reused";
    let rows: Vec<Vec<&str>> = data.lines().map(|s| s.split('\t').collect()).collect();
    let mut start = 0;
    while start < rows.len() {
        let mut end = start + 1;
        while end < rows.len() && rows[end][0] == rows[start][0] { end += 1; }
        let group = &rows[start..end];
        let compiled: Vec<_> = group.iter().map(|r| matcher(r[1])).collect();
        for (row, re) in group.iter().zip(&compiled) {
            assert_eq!(re.is_match(row[2]), row[3] == "1", "{} {}", row[1], row[2]);
        }
        let expected: usize = (0..iterations).map(|i| usize::from(group[i % group.len()][3] == "1")).sum();
        let mut checksum = 0usize;
        let began = Instant::now();
        for i in 0..iterations {
            let at = black_box(i % group.len());
            let row = &group[at];
            checksum += usize::from(if reused { compiled[at].is_match(black_box(row[2])) }
                else { matcher(black_box(row[1])).is_match(black_box(row[2])) });
        }
        let ns = began.elapsed().as_nanos();
        assert_eq!(checksum, expected);
        println!("{}\t{}\t{}\t{}", group[0][0], ns, iterations, checksum);
        start = end;
    }
}
