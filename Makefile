GOOSE ?= .toolchain/goose/build/goose
CC ?= gcc
SANITIZER_CC ?= gcc
.NOTPARALLEL:
.PHONY: setup format check test differential sanitize
setup:
	./scripts/setup-goose.sh
format:
	"$(GOOSE)" format glob.goose walk.goose tests examples
check:
	"$(GOOSE)" format --check glob.goose walk.goose tests examples
	"$(GOOSE)" check tests/matcher.goose
	"$(GOOSE)" check tests/walk.goose
	"$(GOOSE)" check tests/oracle.goose
	"$(GOOSE)" check examples/find.goose
test:
	mkdir -p .build
	"$(GOOSE)" run tests/matcher.goose
	python3 tests/walk.py "$(GOOSE)" run tests/walk.goose --
	"$(GOOSE)" build tests/matcher.goose --cc "$(CC)" -O2 -o .build/matcher
	./.build/matcher
	"$(GOOSE)" build tests/walk.goose --cc "$(CC)" -O2 -o .build/walk
	python3 tests/walk.py ./.build/walk
	"$(GOOSE)" build tests/matcher.goose --cc "$(CC)" --debug --no-bce -o .build/matcher-debug
	./.build/matcher-debug
	"$(GOOSE)" build tests/walk.goose --cc "$(CC)" --debug --no-bce -o .build/walk-debug
	python3 tests/walk.py ./.build/walk-debug
differential:
	mkdir -p .build
	"$(GOOSE)" build tests/oracle.goose --cc "$(CC)" -O2 -o .build/oracle
	python3 tests/model.py ./.build/oracle
sanitize:
	mkdir -p .build
	SANITIZER_CC="$(SANITIZER_CC)" "$(GOOSE)" build tests/matcher.goose --cc "$(abspath scripts/sanitizer-cc.sh)" --standalone --debug --no-bce -o .build/matcher-sanitize
	ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1 ./.build/matcher-sanitize
	SANITIZER_CC="$(SANITIZER_CC)" "$(GOOSE)" build tests/walk.goose --cc "$(abspath scripts/sanitizer-cc.sh)" --standalone --debug --no-bce -o .build/walk-sanitize
	ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1 python3 tests/walk.py ./.build/walk-sanitize
