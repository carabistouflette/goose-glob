// SPDX-License-Identifier: Apache-2.0
import glob from "..";
import std;
import os;
struct Row { pattern: const u8[:], path: const u8[:], expected: i64 }
fn measure(name: const u8[:], rows: Row[:], iterations: i64) {
    for row in rows {
        let matched, status = glob::matches(row.pattern, row.path, glob::Options { hidden: true });
        assert(status.error == glob::Error.None && (if matched { 1 } else { 0 }) == row.expected);
    }
    var checksum = 0; var expected = 0;
    for i in iterations { expected += rows[i % rows.len].expected; }
    let start = clock_ns();
    for i in iterations {
        let row = rows[i % rows.len];
        let matched, status = glob::matches(row.pattern, row.path, glob::Options { hidden: true });
        checksum += if matched && status.error == glob::Error.None { 1 } else { 0 };
    }
    let elapsed = clock_ns() - start;
    assert(checksum == expected);
    print(name, "\t", elapsed, "\t", iterations, "\t", checksum);
}
fn main() {
    let argv = args(); assert(argv.len == 4 && (argv[3] == "oneshot" || argv[3] == "reused"));
    let iterations, ok = parse_int(argv[2]); assert(ok && iterations > 0);
    var data: u8[>..]  = []; assert(read_file(argv[1], data));
    var rows: Row[>..] = []; var name: const u8[:] = data[..0];
    for line in split(data, "\n") {
        if line.len == 0 { continue; }
        let fields = split(line, "\t"); assert(fields.len == 4);
        if rows.len > 0 && fields[0] != name { measure(name, rows, iterations); rows.clear(); }
        name = fields[0]; let expected, parsed = parse_int(fields[3]); assert(parsed);
        rows.push(Row { fields[1], fields[2], expected });
    }
    if rows.len > 0 { measure(name, rows, iterations); }
}
