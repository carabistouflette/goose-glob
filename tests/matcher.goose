// SPDX-License-Identifier: Apache-2.0
import glob from "..";
import std;
fn check(pattern: const u8[:], path: const u8[:], expected: bool) {
    let matched, status = glob::matches(pattern, path);
    let compiled, prepared = glob::compile(pattern); assert(prepared.error == glob::Error.None);
    let reused, reused_status = glob::matches(compiled, path);
    assert(reused_status.error == status.error && reused == matched);
    if status.error != glob::Error.None || matched != expected { print("failed: ", pattern, " / ", path); assert(false); }
}
fn check_status(pattern: const u8[:], path: const u8[:], options: glob::Options, expected: bool, error: glob::Error) {
    let matched, status = glob::matches(pattern, path, options);
    assert(matched == expected && status.error == error);
    let compiled, prepared = glob::compile(pattern); assert(prepared.error == glob::Error.None);
    let reused, checked = glob::matches(compiled, path, options);
    assert(reused == expected && checked.error == error);
}
fn main() {
    check("*.goose", "main.goose", true);
    check("*.goose", "src/main.goose", false);
    check("**/*.goose", "main.goose", true);
    check("**/*.goose", "src/deep/main.goose", true);
    check("a/**/b", "a/b", true);
    check("a/**/b", "a/x/y/b", true);
    check("a/**/b", "a/x/y/c", false);
    check("[*]/**/x", "*/a/x", true);
    check("\\*\\*/x", "**/x", true);
    let rejected_tail, rejected_status = glob::compile("a/**/[");
    assert(rejected_status.error == glob::Error.InvalidPattern);
    let _, rejected_match = glob::matches(rejected_tail, "a/x");
    assert(rejected_match.error == glob::Error.InvalidPattern);
    check("**", "a/b", true);
    check("**/**/b", "a/b", true);
    check("a/**", "a", true);
    check("a/?", "a/é", false);
    check("a/??", "a/é", true);
    check("*a*b", "aaacb", true);
    check("*a*b", "aaac", false);
    check("*ab*bc", "abc", false);
    check("*ab*bc", "abbc", true);
    check("ab*cd*ef", "abXXcdYYef", true);
    check("ab*cd*ef", "abXXcdYYefZZ", false);
    check("ab*cd*ef*", "abXXcdYYefZZ", true);
    check("*é*é", "éxé", true);
    check("[a-c][!0-9]", "bz", true);
    check("[a-c][^0-9]", "b1", false);
    check("[-a]", "-", true);
    check("[a-]", "-", true);
    check("[--a]", "Z", true);
    check("[--a]", "z", false);
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
    for pattern in ["", "/a", "a/", "a//b", ".", "..", "a/../b", "a\\", "***", "a**", "[]", "[!]", "[z-a]", "[a", "[\\a]", "a\0b", "[a/b]", "[.-/]", "[a-\0]", "a\\\0"] {
        let _, status = glob::matches(pattern, "a"); assert(status.error == glob::Error.InvalidPattern);
    }
    for path in ["", "/a", "a/", "a//b", ".", "..", "a/./b", "a\0b"] {
        let _, status = glob::matches("**", path); assert(status.error == glob::Error.InvalidPath);
    }
    for path in ["src//other", "src/../other", "src/other/", "src/other\0x"] {
        let _, status = glob::matches("src/main", path); assert(status.error == glob::Error.InvalidPath);
    }
    // A prefix miss still validates the complete path, including vector-scan
    // boundaries and binary bytes. Validation precedes fuel exhaustion.
    for width in [15, 16, 31, 32, 63, 64, 127] {
        var prefix = str(""); prefix.resize(width, 'a');
        for ending in ["/", "//x", "/./x", "/../x", "\0x"] {
            for limit in [1, 1048576] {
                check_status("different/**", str(prefix, ending), glob::Options { work_limit: limit, .. }, false, glob::Error.InvalidPath);
            }
        }
        check("**/\xff.goose", str(prefix, "/\xff.goose"), true);
    }
    // Both APIs share the prefix shortcut only when the first literal
    // comparison fits the budget, including a prefix lacking a separator.
    for path in ["other/abcdefghijklmnopqrstuvwxyz/x", "srcmore/abcdefghijklmnopqrstuvwxyz/x"] {
        check_status("src/**/x", path, glob::Options { work_limit: 3, .. }, false, glob::Error.LimitExceeded);
        check_status("src/**/x", path, glob::Options { work_limit: 4, .. }, false, glob::Error.None);
    }
    // Counting components cannot change the old order of fuel/hidden checks.
    check_status("src/*", "one", glob::Options { work_limit: 1, .. }, false, glob::Error.None);
    check_status("src/**/x", "one", glob::Options { work_limit: 1, .. }, false, glob::Error.None);
    check_status("**/x", "a/b/x", glob::Options { work_limit: 4, .. }, true, glob::Error.None);
    check_status("**/x", "a/b/x", glob::Options { work_limit: 3, .. }, false, glob::Error.LimitExceeded);
    check_status("a/**", "a", glob::Options { work_limit: 2, .. }, true, glob::Error.None);
    check_status("a/**", "a", glob::Options { work_limit: 1, .. }, false, glob::Error.LimitExceeded);
    check_status("a/**/b", "a/.hidden/b", glob::Options { work_limit: 3, .. }, false, glob::Error.None);
    check_status("a/**/b", "a/.hidden/b", glob::Options { hidden: true, work_limit: 3 }, false, glob::Error.LimitExceeded);
    // Long cheap misses must not be charged a full chunk per candidate.
    var long_pattern = str("*"); long_pattern.resize(501, 'a'); long_pattern.append("*b");
    var long_name = str(""); long_name.resize(3000, 'x'); long_name.resize(3500, 'a'); long_name.push('b');
    check(long_pattern, long_name, true);
    var partial_pattern = str("*a"); partial_pattern.resize(501, 'b'); partial_pattern.append("*z");
    var partial_name = str(""); for _ in 1500 { partial_name.append("ac"); }
    partial_name.push('a'); for _ in 499 { partial_name.push('b'); } partial_name.push('z');
    check(partial_pattern, partial_name, true);
    let _, search_limit = glob::matches("*abc*def*", "XXXXXXXXabcYYYYdefZZ", glob::Options { work_limit: 2 });
    assert(search_limit.error == glob::Error.LimitExceeded);
    let searched, search_ok = glob::matches("*abc*def*", "XXXXXXXXabcYYYYdefZZ");
    assert(searched && search_ok.error == glob::Error.None);
    let _, limited = glob::matches("*a*a*a*a*b", "aaaaaaaaaaaab", glob::Options { work_limit: 3 });
    assert(limited.error == glob::Error.LimitExceeded);
    let _, invalid = glob::matches("*", "a", glob::Options { work_limit: -1 });
    assert(invalid.error == glob::Error.InvalidOptions);
    var big = str(""); big.resize(1024, 'a');
    let exact_pattern, exact_status = glob::matches(big, big);
    assert(exact_pattern && exact_status.error == glob::Error.None);
    big.push('a');
    assert(glob::validate(big).error == glob::Error.InvalidPattern);
    big.resize(4095, 'a');
    let exact_path, path_status = glob::matches("*", big);
    assert(exact_path && path_status.error == glob::Error.None);
    big.push('a');
    let _, too_long = glob::matches("*", big);
    assert(too_long.error == glob::Error.InvalidPath);
    var components = str("a");
    for _ in 127 { components.append("/a"); }
    let exact_components, components_status = glob::matches(components, components);
    assert(exact_components && components_status.error == glob::Error.None);
    components.append("/a");
    assert(glob::validate(components).error == glob::Error.InvalidPattern);
    let _, too_many = glob::matches("**", components);
    assert(too_many.error == glob::Error.InvalidPath);
    check_status("different/**", components, glob::Options { .. }, false, glob::Error.InvalidPath);
    let exact_fuel, fuel_status = glob::matches("**", "a", glob::Options { work_limit: 1 });
    assert(exact_fuel && fuel_status.error == glob::Error.None);
    let max_fuel, max_status = glob::matches("*", "a", glob::Options { work_limit: glob::MAX_WORK });
    assert(max_fuel && max_status.error == glob::Error.None);
    let _, too_much_fuel = glob::matches("*", "a", glob::Options { work_limit: glob::MAX_WORK + 1 });
    assert(too_much_fuel.error == glob::Error.InvalidOptions);
    let empty, rejected = glob::compile("[");
    assert(rejected.error == glob::Error.InvalidPattern);
    let _, unusable = glob::matches(empty, "a");
    assert(unusable.error == glob::Error.InvalidPattern);
    let pattern, prepared = glob::compile("*.goose"); assert(prepared.error == glob::Error.None);
    for path in ["a.goose", "b.txt", "c.goose"] {
        let expected, direct_status = glob::matches("*.goose", path);
        let matched, reused_status = glob::matches(pattern, path);
        assert(matched == expected && reused_status.error == direct_status.error);
    }
    var source = str("a/**/b");
    let owned_pattern, owned_status = glob::compile(source); assert(owned_status.error == glob::Error.None);
    source.clear();
    let kept, kept_status = glob::matches(owned_pattern, "a/x/b"); assert(kept && kept_status.error == glob::Error.None);
    let _, invalid_compiled_path = glob::matches(owned_pattern, "a//b"); assert(invalid_compiled_path.error == glob::Error.InvalidPath);
    let _, invalid_compiled_options = glob::matches(owned_pattern, "a/b", glob::Options { work_limit: 0 });
    assert(invalid_compiled_options.error == glob::Error.InvalidOptions);
    let _, compiled_limit = glob::matches(owned_pattern, "a/x/b", glob::Options { work_limit: 1 });
    assert(compiled_limit.error == glob::Error.LimitExceeded);
    print("matcher tests passed");
}
