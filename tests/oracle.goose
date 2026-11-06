// SPDX-License-Identifier: Apache-2.0
import glob from "..";
import std;
import os;
fn main() {
    let argv = args();
    if argv.len != 3 { exit(2); }
    let matched, status = glob::matches(argv[1], argv[2], glob::Options { hidden: true });
    if status.error != glob::Error.None { exit(2); }
    print(if matched { "1" } else { "0" });
}
