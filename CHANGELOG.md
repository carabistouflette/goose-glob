# Changelog

## Unreleased

Owned prepared patterns for repeated matching; literal/prefix/suffix comparisons,
linear component matching and greedy globstars; collector pattern reuse, held directory roots and listing-type reuse with a
no-follow metadata fallback when entry types are unavailable. Exact
fuel accounting is an implementation detail and can differ from alpha.1.
Pinned cross-language matcher and clean-tree collection benchmark harnesses.

## 0.1.0-alpha.1

Initial experimental release: byte-oriented component glob matching, `**`,
classes and escapes; bounded regular-file collection using goose-fs, exclusions,
explicit hidden-file policy, and no-follow traversal. Linux x86-64/glibc validated.
