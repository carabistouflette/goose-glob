// SPDX-License-Identifier: Apache-2.0
import glob from "..";
import fs from "github.com/carabistouflette/goose-fs@0d84729aed8d72463349cac7d9439d4039ccd6d3";
import glob.walk;
import std;
import os;
fn before(a: const u8[:], b: const u8[:]) -> bool {
    for i in 0..min(a.len, b.len) { if a[i] != b[i] { return a[i] < b[i]; } }
    return a.len < b.len;
}
fn collect(root: const u8[:], paths: u8[][>..]&) -> i64 {
    let status = glob_walk::collect(root, "**/*.goose", [], glob_walk::Options { .. }, paths);
    assert(status.error == glob::Error.None);
    var checksum = paths.len * 1000003;
    for path in paths { checksum += path.len; }
    return checksum;
}
fn main() {
    let argv = args(); assert(argv.len == 4 && argv[3] == "walk");
    let count, ok = parse_int(argv[2]); assert(ok && count > 0);
    var paths: u8[][>..] = [];
    let expected = collect(argv[1], paths);
    // Observe the complete path set outside timing, not only a result count.
    var refs: const u8[:][>..] = [];
    for path in paths { refs.push(path); }
    sort(refs) { a, b => before(a, b) };
    var expected_text: u8[>..] = []; assert(read_file(str(argv[1], "/../walk-expected.txt"), expected_text));
    var actual:        u8[>..] = [];
    for path in refs { actual.append(path); actual.push('\n'); }
    assert(actual == expected_text);
    var checksum = 0;
    let start = clock_ns();
    for _ in count { checksum += collect(argv[1], paths); }
    let elapsed = clock_ns() - start;
    assert(checksum == count * expected);
    print("walk\t", elapsed, "\t", count, "\t", checksum);
}
