# v0.1 compatibility policy

v0.1.0 is the first non-prerelease of goose-glob. It preserves the matcher and
collector runtime from v0.1.0-alpha.5; the additional qualification covers the
supported surface, installation and documented failure behavior. This is a
0.1 release, not a 1.0 language or cross-platform stability promise.

## Supported surface

The `glob` module supports:

- `matches(raw_pattern, path, options)` and `matches(compiled_pattern, path, options)`.
- `compile(raw_pattern)` and `validate(raw_pattern)`.
- Owned `Pattern` values returned by `compile`, passed by reference to `matches`.
  Their fields and representation are implementation details; do not construct
  or mutate them. Failed compilation returns an unusable empty value.
- `Options.hidden`, `Options.work_limit`, `Status.error`, `Status.os_error`, and
  the documented `Error` cases. Defaults, accepted ranges and error meanings are
  in the README.
- `MAX_PATTERN_BYTES`, `MAX_PATH_BYTES`, `MAX_COMPONENTS`, and `MAX_WORK`.

The optional `glob_walk` module supports `collect`, its `Options` fields and
`MAX_QUEUED_PATH_BYTES`. It returns the same `glob::Status`. The caller supplies
the pinned goose-fs mapping described in the README. Collection owns its output,
clears it on every failure, and accepts arguments borrowing the prior output.

Other declarations, metadata types, storage layouts and dispatch thresholds are
internal. There is no serialized pattern format or C ABI compatibility promise.

## Compatibility within 0.1.x

Patch releases preserve the supported calls, ownership rules, pattern dialect,
option defaults/ranges and documented error meanings. Breaking supported API or
dialect changes require 0.2. Timing, allocation strategy, private representation
and exact work-fuel exhaustion thresholds may change as documented. Callers must
handle `LimitExceeded` instead of relying on a precise operation count.

The README's byte-path rules, hidden-file semantics, no-follow policy and bounded
failure behavior are part of the contract. Collection order is breadth-first
with unsigned byte sorting within each directory; there is no global sort or
filesystem snapshot guarantee. Paths must be re-opened with appropriate policy.

## Qualified environment and dependencies

The qualified target is Linux x86-64/glibc with Goose
`eadca409f68210893f366e60d0c2f0dc29a339be`. The optional collector uses goose-fs
`0d84729aed8d72463349cac7d9439d4039ccd6d3`. The matcher uses only Goose `std`;
collection additionally needs the pinned Linux filesystem backend. Other
compiler revisions, dependencies and platforms require separate qualification.
Changing these pins requires explicit review and documented validation.

A release requires clean source installation, public consumer checks, GCC/Clang
normal/debug and ASan/UBSan checks, the differential model, and independent
standards/API-contract reviews. Performance reports retain their original source
identities and limits; v0.1.0 makes no new comparative speed claim. The alpha.5
measurements remain historical evidence for the unchanged runtime.

## Automated consumer verification

`scripts/check-consumer.py` creates a client outside the checkout with a fresh
`GOOSE_HOME`, using only documented APIs. It runs interpreted and optimized
compiled checks for raw/prepared matches, syntax/path/option errors, collection
and output clearing on a result limit. Git global/system configuration and
ambient package/loader overrides are excluded from the child environment.

Push and pull-request CI checks the candidate via `--source`. Published-release
CI checks the public release tag, including prereleases. Manual CI runs accept a
`tag` input, or check the candidate when it is empty. The tagged check runs after
publication; it complements the candidate gate and the remaining release
qualification rather than publishing or moving a tag itself.

```sh
python3 scripts/check-consumer.py --goose .toolchain/goose/build/goose --cc gcc --source "$PWD"
python3 scripts/check-consumer.py --goose .toolchain/goose/build/goose --cc clang --tag v0.1.0
```

The temporary directory must be outside the source checkout. Set `TMPDIR` to an
external writable directory if the default temporary filesystem is unsuitable.

GitHub documents the publication trigger under
[release events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#release)
and the manual input under
[workflow_dispatch](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onworkflow_dispatchinputs).
