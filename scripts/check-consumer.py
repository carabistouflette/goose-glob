#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check supported APIs from a clean external client, locally or at a public tag."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
IMPORT = 'github.com/carabistouflette/goose-glob@v0.1.0'
TAG = re.compile(r'v[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?')


def consumer_import(tag, source):
    if tag is not None:
        if not TAG.fullmatch(tag):
            raise ValueError('tag must be a version such as v0.1.0 or v0.1.1-alpha.1')
        return f'github.com/carabistouflette/goose-glob@{tag}'
    source = source.resolve(strict=True)
    if not all((source/name).is_file() for name in ('glob.goose', 'walk.goose')):
        raise ValueError('source must contain glob.goose and walk.goose')
    return str(source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--goose', type=Path, required=True)
    parser.add_argument('--cc', choices=('gcc', 'clang'), default='gcc')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--tag')
    mode.add_argument('--source', type=Path)
    args = parser.parse_args()
    try:
        location = consumer_import(args.tag, args.source)
        goose = args.goose.resolve(strict=True)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    template = (ROOT/'tests/consumer.goose').read_text()
    marker = json.dumps(IMPORT)
    if template.count(marker) != 1:
        raise SystemExit('consumer template must contain exactly one library import')
    with tempfile.TemporaryDirectory(prefix='goose-glob consumer ') as directory:
        client = Path(directory).resolve()
        roots = [ROOT] + ([args.source.resolve()] if args.source else [])
        if any(client.is_relative_to(root) for root in roots):
            raise SystemExit('temporary client must be outside the source checkout; set TMPDIR elsewhere')
        program = client/'main.goose'
        program.write_text(template.replace(marker, json.dumps(location, ensure_ascii=False)))
        fixture = client/'fixture'
        for name in ('main.goose', 'nested/a.goose', 'ignored/skip.goose', '.hidden/h.goose', 'readme.txt'):
            path = fixture/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('')
        temporary = client/'tmp'
        temporary.mkdir()
        env = os.environ.copy()
        for key in tuple(env):
            if key.startswith('GIT_CONFIG') or key in ('GOOSE_STDLIB', 'GOOSE_CC', 'LD_PRELOAD', 'LD_LIBRARY_PATH', 'ASAN_OPTIONS', 'UBSAN_OPTIONS', 'GIT_ASKPASS', 'SSH_ASKPASS'):
                env.pop(key)
        env.update(GOOSE_HOME=str(client/'home'), TMPDIR=str(temporary), GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
        def run(*command):
            subprocess.run(list(map(str, command)), cwd=client, env=env, check=True, timeout=300)
        run(goose, 'run', program, '--', fixture)
        binary = client/'consumer'
        run(goose, 'build', program, '--cc', args.cc, '-O2', '-o', binary)
        run(binary, fixture)
    print(f'Isolated consumer verified: {args.tag or "candidate checkout"} ({args.cc})')


if __name__ == '__main__':
    main()
