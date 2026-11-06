// SPDX-License-Identifier: Apache-2.0
import glob from "..";
import fs from "github.com/carabistouflette/goose-fs@0d84729aed8d72463349cac7d9439d4039ccd6d3";
import glob.walk;
import std;
import os;
fn failed(root: const u8[:], options: glob_walk::Options, expected: glob::Error) {
    var out: u8[][>..] = []; out.push(str("old"));
    let status = glob_walk::collect(root, "**/*.goose", ["vendor"], options, out);
    assert(status.error == expected && out.len == 0);
}
fn main() {
    let argv = args(); assert(argv.len == 3);
    let root = argv[1];
    var out: u8[][>..] = [];
    let excludes = ["vendor", ".build"];
    let status = glob_walk::collect(root, "**/*.goose", excludes, glob_walk::Options { .. }, out);
    assert(status.error == glob::Error.None && out.len == 4);
    let expected = ["main.goose", "src/a.goose", "src/\xff.goose", "src/deep/b.goose"];
    for path, i in out { assert(path == expected[i]); }
    let hidden = glob_walk::collect(root, "**/*.goose", excludes, glob_walk::Options { hidden: true }, out);
    assert(hidden.error == glob::Error.None && out.len == 6);
    failed(root, glob_walk::Options { max_results: 3 }, glob::Error.LimitExceeded);
    failed(root, glob_walk::Options { max_result_bytes: 1 }, glob::Error.LimitExceeded);
    failed(root, glob_walk::Options { max_entries: 0 }, glob::Error.LimitExceeded);
    failed(root, glob_walk::Options { max_depth: 1 }, glob::Error.LimitExceeded);
    failed(root, glob_walk::Options { work_limit: 1 }, glob::Error.LimitExceeded);
    failed(root, glob_walk::Options { max_depth: 0 }, glob::Error.InvalidOptions);
    failed(root, glob_walk::Options { max_results: -1 }, glob::Error.InvalidOptions);
    failed("relative", glob_walk::Options { .. }, glob::Error.Filesystem);
    failed(str(root, "/missing"), glob_walk::Options { .. }, glob::Error.Filesystem);
    // Per-directory backend cap: no incomplete success for a huge listing.
    failed(argv[2], glob_walk::Options { .. }, glob::Error.LimitExceeded);
    let invalid = glob_walk::collect(root, "[", excludes, glob_walk::Options { .. }, out);
    assert(invalid.error == glob::Error.InvalidPattern && out.len == 0);
    let bad_exclude = glob_walk::collect(root, "**", ["["], glob_walk::Options { .. }, out);
    assert(bad_exclude.error == glob::Error.InvalidPattern && out.len == 0);
    // Result bytes and limits at the exact boundary.
    let single = glob_walk::collect(root, "main.goose", ["src", "vendor"],
        glob_walk::Options { max_results: 1, max_result_bytes: 10 }, out);
    assert(single.error == glob::Error.None && out.len == 1);
    // A borrowed argument may refer to the old output: it is staged safely.
    out.clear(); out.push(str(root));
    for old in out {
        let aliased = glob_walk::collect(old, "main.goose", ["src", "vendor"], glob_walk::Options { .. }, out);
        assert(aliased.error == glob::Error.None && out.len == 1); break;
    }
    print("traversal tests passed");
}
