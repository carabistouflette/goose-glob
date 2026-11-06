// SPDX-License-Identifier: Apache-2.0
import glob from "..";
import std;
import os;
fn main() {
    let argv = args();
    if argv.len != 3 { exit(2); }
    let matched, status = glob::matches(argv[1], argv[2], glob::Options { hidden: true });
    if status.error != glob::Error.None { exit(2); }
    let compiled, prepared = glob::compile(argv[1]); assert(prepared.error == glob::Error.None);
    let reused, checked = glob::matches(compiled, argv[2], glob::Options { hidden: true });
    assert(checked.error == glob::Error.None && reused == matched);
    let visible, visible_status = glob::matches(argv[1], argv[2]);
    let reused_visible, reused_visible_status = glob::matches(compiled, argv[2]);
    assert(visible_status.error == glob::Error.None && reused_visible_status.error == glob::Error.None && visible == reused_visible);
    print(if matched { "1" } else { "0" }, " ", if visible { "1" } else { "0" });
}
