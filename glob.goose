// SPDX-License-Identifier: Apache-2.0
namespace glob;
import std;

const MAX_PATTERN_BYTES = 1024;
const MAX_PATH_BYTES = 4095;
const MAX_COMPONENTS = 128;
const MAX_WORK = 16777216;
enum Error { None, InvalidPattern, InvalidPath, InvalidOptions, LimitExceeded, Filesystem }
struct Status { error: Error = Error.None, os_error: i64 = 0 }
struct Options { hidden: bool = false, work_limit: i64 = 1048576 }
struct Span { start: i64, end: i64 }
enum ComponentKind { General, Literal, Prefix, Suffix, Globstar }
struct Part { start: i64, end: i64, kind: ComponentKind }
struct Pattern { source: u8[], parts: Part[], globstars: i64 = 0 }
struct Budget { remaining: i64, exhausted: bool = false }

fn spend(budget: Budget&) -> bool {
    if budget.remaining == 0 { budget.exhausted = true; return false; }
    budget.remaining--; return true;
}
fn split(path: const u8[:], out: Span[>..]&) -> bool {
    out.clear();
    if path.len == 0 || path.len > MAX_PATH_BYTES { return false; }
    var start = 0;
    for i in 0..path.len + 1 {
        if i < path.len && path[i] == 0 { return false; }
        if i == path.len || path[i] == '/' {
            let part = path[start..i];
            if part.len == 0 || part == "." || part == ".." || out.len == MAX_COMPONENTS { return false; }
            out.push(Span { start: start, end: i }); start = i + 1;
        }
    }
    return true;
}
// Returns the closing bracket, or -1 for an empty/malformed class.
fn class_end(pattern: const u8[:], start: i64) -> i64 {
    var at = start + 1;
    if at < pattern.len && (pattern[at] == '!' || pattern[at] == '^') { at++; }
    let first = at;
    while at < pattern.len && pattern[at] != ']' {
        // Escapes inside classes are deliberately unsupported.
        if pattern[at] == '\\' { return -1; }
        if at + 2 < pattern.len && pattern[at + 1] == '-' && pattern[at + 2] != ']' {
            if pattern[at] > pattern[at + 2] || pattern[at + 2] == '\\' { return -1; }
            at += 3;
        } else { at++; }
    }
    return if at < pattern.len && at > first { at } else { -1 };
}
fn valid_component(pattern: const u8[:]) -> bool {
    if pattern == "**" { return true; }
    var at = 0;
    while at < pattern.len {
        let c = pattern[at];
        if c == '\\' {
            at++;
            if at == pattern.len { return false; }
        } else if c == '[' {
            at = class_end(pattern, at);
            if at < 0 { return false; }
        } else if c == '*' && at + 1 < pattern.len && pattern[at + 1] == '*' { return false; }
        at++;
    }
    return true;
}
fn component_kind(pattern: const u8[:]) -> ComponentKind {
    if pattern == "**" { return ComponentKind.Globstar; }
    var stars = 0;
    for c in pattern {
        if c == '?' || c == '[' || c == '\\' { return ComponentKind.General; }
        if c == '*' { stars++; }
    }
    if stars == 0 { return ComponentKind.Literal; }
    if stars == 1 && pattern[0] == '*' { return ComponentKind.Suffix; }
    if stars == 1 && pattern[pattern.len - 1] == '*' { return ComponentKind.Prefix; }
    return ComponentKind.General;
}
fn parse_pattern(pattern: const u8[:], out: Part[>..]&) -> bool {
    out.clear();
    var spans: Span[>..] = [];
    if pattern.len > MAX_PATTERN_BYTES || !split(pattern, spans) { return false; }
    for span in spans {
        let part = pattern[span.start..span.end];
        if !valid_component(part) { out.clear(); return false; }
        out.push(Part { start: span.start, end: span.end, kind: component_kind(part) });
    }
    return true;
}
fn validate(pattern: const u8[:]) -> Status {
    var parts: Part[>..] = [];
    return Status { error: if parse_pattern(pattern, parts) { Error.None } else { Error.InvalidPattern } };
}
fn owned<T>(source: const T[:]) -> T[] {
    var out: T[>..] = []; out.append(source); return out;
}
fn compile(pattern: const u8[:]) -> Pattern, Status {
    var parts: Part[>..] = [];
    if !parse_pattern(pattern, parts) { return Pattern { .. }, Status { error: Error.InvalidPattern }; }
    return Pattern { source: owned(pattern), parts: owned(parts), globstars: count_globstars(parts) }, Status { .. };
}
fn class_matches(pattern: const u8[:], start: i64, end: i64, c: u8) -> bool {
    var at = start + 1;
    let negate = pattern[at] == '!' || pattern[at] == '^';
    if negate { at++; }
    var found = false;
    while at < end {
        if at + 2 < end && pattern[at + 1] == '-' {
            if c >= pattern[at] && c <= pattern[at + 2] { found = true; }
            at += 3;
        } else {
            if c == pattern[at] { found = true; }
            at++;
        }
    }
    return if negate { !found } else { found };
}
// Greedy component matching with one saved star. No recursive backtracking.
fn component_matches(pattern: const u8[:], name: const u8[:], hidden: bool, budget: Budget&) -> bool {
    let explicit_dot = pattern[0] == '.' || (pattern.len >= 2 && pattern[0] == '\\' && pattern[1] == '.');
    if !hidden && name[0] == '.' && !explicit_dot { return false; }
    let last = pattern[pattern.len - 1];
    if last != '*' && last != '?' && last != ']' && name[name.len - 1] != last { return false; }
    var p = 0; var n = 0; var star = -1; var retry = 0;
    while n < name.len {
        if !spend(budget) { return false; }
        if p < pattern.len && pattern[p] == '*' { star = p; p++; retry = n; continue; }
        var next = p + 1;
        var matched = false;
        if p < pattern.len {
            let c = pattern[p];
            if c == '?' { matched = true; }
            else if c == '\\' { matched = pattern[p + 1] == name[n]; next = p + 2; }
            else if c == '[' {
                let end = class_end(pattern, p);
                // Charge the complete class scan, including ranges.
                if budget.remaining < end - p { budget.exhausted = true; return false; }
                budget.remaining -= end - p;
                matched = class_matches(pattern, p, end, name[n]); next = end + 1;
            } else { matched = c == name[n]; }
        }
        if matched { p = next; n++; }
        else if star >= 0 { retry++; n = retry; p = star + 1; }
        else { return false; }
    }
    if p < pattern.len && pattern[p] == '*' { p++; }
    return p == pattern.len;
}
// Literal components and single edge-stars use bounded slice comparisons.
fn part_matches(pattern: const u8[:], name: const u8[:], kind: ComponentKind, hidden: bool, budget: Budget&) -> bool {
    if kind == ComponentKind.General { return component_matches(pattern, name, hidden, budget); }
    if !hidden && name[0] == '.' && pattern[0] != '.' { return false; }
    let work = if pattern.len < name.len { pattern.len } else { name.len };
    if budget.remaining < work { budget.exhausted = true; return false; }
    budget.remaining -= work;
    if kind == ComponentKind.Literal { return pattern == name; }
    if kind == ComponentKind.Prefix { return starts_with(name, pattern[..pattern.len - 1]); }
    return ends_with(name, pattern[1..]);
}
fn match_part(pattern: const u8[:], path: const u8[:], part: Part, name: Span, hidden: bool, budget: Budget&) -> bool {
    return spend(budget) && part_matches(pattern[part.start..part.end], path[name.start..name.end], part.kind, hidden, budget);
}
// Match fixed components from the two ends when there is at most one **.
// Multiple ** components use a bounded greedy scan with one retry point.
fn match_parts(pattern: const u8[:], path: const u8[:], patterns: Part[:], names: Span[:], globstars: i64, hidden: bool, budget: Budget&) -> bool {
    if globstars == 0 {
        if patterns.len != names.len { return false; }
        for part, i in patterns {
            if !match_part(pattern, path, part, names[i], hidden, budget) { return false; }
        }
        return true;
    }
    if globstars == 1 {
        if names.len < patterns.len - 1 { return false; }
        var star = 0;
        while patterns[star].kind != ComponentKind.Globstar {
            if !match_part(pattern, path, patterns[star], names[star], hidden, budget) { return false; }
            star++;
        }
        let consumed_end = names.len - (patterns.len - star - 1);
        for i in star..consumed_end {
            if !spend(budget) { return false; }
            if !hidden && path[names[i].start] == '.' { return false; }
        }
        for i in star + 1..patterns.len {
            if !match_part(pattern, path, patterns[i], names[consumed_end + i - star - 1], hidden, budget) { return false; }
        }
        return true;
    }
    var p = 0; var n = 0; var star = -1; var retry = 0;
    while n < names.len {
        if !spend(budget) { return false; }
        if p < patterns.len && patterns[p].kind == ComponentKind.Globstar {
            star = p; p++; retry = n; continue;
        }
        if p < patterns.len && match_part(pattern, path, patterns[p], names[n], hidden, budget) { p++; n++; }
        else {
            if budget.exhausted || star < 0 || retry == names.len || (!hidden && path[names[retry].start] == '.') { return false; }
            retry++; n = retry; p = star + 1;
        }
    }
    while p < patterns.len && patterns[p].kind == ComponentKind.Globstar { p++; }
    return p == patterns.len;
}
fn count_globstars(parts: Part[:]) -> i64 {
    var count = 0;
    for part in parts { if part.kind == ComponentKind.Globstar { count++; } }
    return count;
}
// Internal traversal entry point shares one work budget across all paths.
fn match_with_budget(pattern: Pattern&, path: const u8[:], hidden: bool, budget: Budget&) -> bool {
    var names: Span[>..] = [];
    if !split(path, names) { return false; }
    return match_parts(pattern.source, path, pattern.parts, names, pattern.globstars, hidden, budget);
}
fn valid_options(options: Options) -> bool { options.work_limit >= 1 && options.work_limit <= MAX_WORK }
fn match_result(pattern: const u8[:], parts: Part[:], globstars: i64, path: const u8[:], options: Options) -> bool, Status {
    var names: Span[>..] = [];
    if !split(path, names) { return false, Status { error: Error.InvalidPath }; }
    var budget = Budget { remaining: options.work_limit };
    let matched = match_parts(pattern, path, parts, names, globstars, options.hidden, budget);
    if budget.exhausted { return false, Status { error: Error.LimitExceeded }; }
    return matched, Status { .. };
}
fn matches(pattern: const u8[:], path: const u8[:], options: Options = Options { .. }) -> bool, Status {
    if !valid_options(options) { return false, Status { error: Error.InvalidOptions }; }
    var parts: Part[>..] = [];
    if !parse_pattern(pattern, parts) { return false, Status { error: Error.InvalidPattern }; }
    return match_result(pattern, parts, count_globstars(parts), path, options);
}
fn matches(pattern: Pattern&, path: const u8[:], options: Options = Options { .. }) -> bool, Status {
    if !valid_options(options) { return false, Status { error: Error.InvalidOptions }; }
    if pattern.parts.len == 0 { return false, Status { error: Error.InvalidPattern }; }
    return match_result(pattern.source, pattern.parts, pattern.globstars, path, options);
}
