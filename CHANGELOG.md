# Changelog

## Unreleased

Fused pattern validation/classification; literal-run scanning, whole-literal and
single-component fast paths; bounded chunk searching for literal-only multi-star
patterns; single-pass class matching. Syntax, ownership and input caps remain.
Expanded malformed-input, bounded-search and multi-star compatibility tests.

## 0.1.0-alpha.2

Owned prepared patterns for repeated matching; literal/prefix/suffix comparisons,
linear component matching and greedy globstars; collector pattern reuse, held directory roots and listing-type reuse with a
no-follow metadata fallback when entry types are unavailable. Exact
fuel accounting is an implementation detail and can differ from alpha.1.
Pinned cross-language matcher and clean-tree collection benchmark harnesses.

## 0.1.0-alpha.1

Initial experimental release: byte-oriented component glob matching, `**`,
classes and escapes; bounded regular-file collection using goose-fs, exclusions,
explicit hidden-file policy, and no-follow traversal. Linux x86-64/glibc validated.
