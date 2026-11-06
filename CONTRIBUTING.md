# Contributing

Use focused changes and Conventional Commits. Keep the supported API small,
functions direct, and matching separate from filesystem collection. Reuse
stdlib/goose-fs rather than adding another native backend. Document changes to
pattern rules, errors and limits, including failure behavior.

Run `make setup`, then `make check test differential` and `make sanitize`.
Tests require Linux x86-64/glibc, Git, Make, CMake 3.27+, C/C++20 compilers,
Python 3.11+, and Linux headers with openat2. GCC and Clang are exercised in CI.
Use `make format` for Goose source. New behavior needs positive, failure and
boundary tests; correctness changes require independent review before release.

Contributions are licensed under Apache-2.0. Report vulnerabilities privately as
described in SECURITY.md. Do not commit credentials, private planning or build
output. Compiler and dependency pins are explicit review decisions.
