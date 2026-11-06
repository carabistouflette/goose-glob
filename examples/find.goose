// SPDX-License-Identifier: Apache-2.0
import glob from "..";
import fs from "github.com/carabistouflette/goose-fs@0d84729aed8d72463349cac7d9439d4039ccd6d3";
import glob.walk;
import std;
import os;
fn main() {
    let argv = args();
    if argv.len != 2 { write_stderr("usage: find ABSOLUTE_DIRECTORY\n"); exit(2); }
    var paths: u8[][>..] = [];
    let excludes = ["vendor", ".build"];
    let status = glob_walk::collect(argv[1], "**/*.goose", excludes, glob_walk::Options { .. }, paths);
    if status.error != glob::Error.None { print("collection failed; errno=", status.os_error); exit(1); }
    // Escapes arbitrary filename bytes, including newlines and terminal controls.
    for path in paths {
        var line = str("");
        let hex = "0123456789abcdef";
        for c in path {
            if c >= 32 && c < 127 && c != '\\' { line.push(c); }
            else { line.append("\\x"); line.push(hex[c >> 4]); line.push(hex[c & 15]); }
        }
        print(line);
    }
}
