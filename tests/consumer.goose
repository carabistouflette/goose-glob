// SPDX-License-Identifier: Apache-2.0
import glob from "github.com/carabistouflette/goose-glob@v0.1.0";
import fs from "github.com/carabistouflette/goose-fs@0d84729aed8d72463349cac7d9439d4039ccd6d3";
import glob.walk;
import std; import os;
fn main() {
    let argv = args(); assert(argv.len == 2);
    let pattern, prepared = glob::compile("src/**/x.goose"); assert(prepared.error == glob::Error.None);
    var long_name = str(""); long_name.resize(96, 'z');
    let positive = str("src/", long_name, "/x.goose");
    let hit, checked = glob::matches(pattern, positive); assert(hit && checked.error == glob::Error.None);
    let raw_hit, raw_checked = glob::matches("src/**/x.goose", positive);
    assert(raw_hit && raw_checked.error == glob::Error.None);
    let miss = str(long_name, "/x.goose");
    let direct, raw_status = glob::matches("src/**/x.goose", miss);
    let reused, reused_status = glob::matches(pattern, miss);
    assert(!direct && !reused && raw_status.error == glob::Error.None && reused_status.error == glob::Error.None);
    let invalid_hit, invalid = glob::matches(pattern, str(long_name, "//x.goose")); assert(!invalid_hit && invalid.error == glob::Error.InvalidPath);
    let option_hit, bad_options = glob::matches(pattern, positive, glob::Options { work_limit: 0 });
    assert(!option_hit && bad_options.error == glob::Error.InvalidOptions);
    assert(glob::validate("a/**/[").error == glob::Error.InvalidPattern);
    let empty, rejected = glob::compile("a/**/[");
    assert(rejected.error == glob::Error.InvalidPattern);
    let bad_hit, bad_pattern = glob::matches(empty, "a/x");
    assert(!bad_hit && bad_pattern.error == glob::Error.InvalidPattern);
    var paths: u8[][>..] = [];
    let collected = glob_walk::collect(argv[1], "**/*.goose", ["ignored"], glob_walk::Options { .. }, paths);
    assert(collected.error == glob::Error.None && paths.len == 2);
    let expected = ["main.goose", "nested/a.goose"];
    for path, i in paths { assert(path == expected[i]); }
    let limited = glob_walk::collect(argv[1], "**/*.goose", ["ignored"],
        glob_walk::Options { max_results: 1, .. }, paths);
    assert(limited.error == glob::Error.LimitExceeded && paths.len == 0);
    print("external consumer passed");
}
