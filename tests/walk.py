#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build a real filesystem fixture, then exercise the Goose collector."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory(prefix="goose-glob-") as tmp:
    base = Path(tmp)
    root = base / "tree"
    for name in ("src/deep", "vendor", ".build", ".hidden"):
        (root / name).mkdir(parents=True)
    for name in ("main.goose", "readme.txt", "src/a.goose", "src/deep/b.goose",
                 "vendor/ignored.goose", ".build/ignored.goose", ".hidden/secret.goose", ".dot.goose"):
        (root / name).write_bytes(b"")
    (root / "src" / os.fsdecode(b"\xff.goose")).write_bytes(b"")
    (base / "outside").mkdir()
    (base / "outside" / "outside.goose").touch()
    (root / "linkdir").symlink_to(base / "outside", target_is_directory=True)
    (root / "link.goose").symlink_to(root / "main.goose")
    (root / "dangling.goose").symlink_to(base / "missing")
    os.mkfifo(root / "pipe.goose")
    huge = base / "huge"
    huge.mkdir()
    for i in range(4097):
        (huge / str(i)).touch()
    wide = base / "wide"
    wide.mkdir()
    for i in range(300):
        (wide / ("x" * 230 + f"{i:03}.goose")).touch()
    edges = []
    for packed_bytes in (4096, 4097):
        edge = base/str(packed_bytes)
        edge.mkdir()
        # Packed entries use one kind byte, the name, and a NUL terminator.
        for i in range(16):
            width = 247 if packed_bytes == 4097 and i == 0 else 246
            (edge/('x'*width + f'{i:02}.goose')).touch()
        edges.append(str(edge))
    subprocess.run([*sys.argv[1:], str(root), str(huge), str(wide), *edges], check=True, timeout=60)
