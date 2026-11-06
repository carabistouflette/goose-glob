// SPDX-License-Identifier: Apache-2.0
import glob from "..";
import std;
fn check(pattern: const u8[:], path: const u8[:], expected: bool) {
    let matched, status = glob::matches(pattern, path);
    if status.error != glob::Error.None || matched != expected { print("failed: ", pattern, " / ", path); assert(false); }
}
fn main() {
    check("*.goose", "main.goose", true);
    check("*.goose", "src/main.goose", false);
    check("**/*.goose", "main.goose", true);
    check("**/*.goose", "src/deep/main.goose", true);
    check("a/**/b", "a/b", true);
    check("a/**/b", "a/x/y/b", true);
    check("a/**/b", "a/x/y/c", false);
    check("**", "a/b", true);
    check("**/**/b", "a/b", true);
    check("a/**", "a", true);
    check("a/?", "a/é", false);
    check("a/??", "a/é", true);
    check("*a*b", "aaacb", true);
    check("*a*b", "aaac", false);
    check("[a-c][!0-9]", "bz", true);
    check("[a-c][^0-9]", "b1", false);
    check("[-a]", "-", true);
    check("[a-]", "-", true);
    check("\\*", "*", true);
    check("\\?", "?", true);
    check("\\[", "[", true);
    check("*", "\xff", true);
    check("*", ".git", false);
    check("[.]git", ".git", false);
    check(".*", ".git", true);
    check("\\.*", ".git", true);
    check("**/file", ".hidden/file", false);
    check("**/.hidden/file", ".hidden/file", true);
    check("**", "a/.hidden", false);
    let hidden, hs = glob::matches("**", "a/.hidden", glob::Options { hidden: true });
    assert(hidden && hs.error == glob::Error.None);
    for pattern in ["", "/a", "a/", "a//b", ".", "..", "a/../b", "a\\", "***", "a**", "[]", "[!]", "[z-a]", "[a", "[\\a]", "a\0b"] {
        let _, status = glob::matches(pattern, "a"); assert(status.error == glob::Error.InvalidPattern);
    }
    for path in ["", "/a", "a/", "a//b", ".", "..", "a/./b", "a\0b"] {
        let _, status = glob::matches("**", path); assert(status.error == glob::Error.InvalidPath);
    }
    let _, limited = glob::matches("*a*a*a*a*b", "aaaaaaaaaaaa", glob::Options { work_limit: 3 });
    assert(limited.error == glob::Error.LimitExceeded);
    let _, invalid = glob::matches("*", "a", glob::Options { work_limit: -1 });
    assert(invalid.error == glob::Error.InvalidOptions);
    var big = str(""); big.resize(1025, 'a');
    assert(glob::validate(big).error == glob::Error.InvalidPattern);
    print("matcher tests passed");
}
