# SPDX-License-Identifier: Apache-2.0
"""Regression tests for benchmark contamination and provenance rejection."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BENCH = Path(__file__).resolve().parents[1] / 'bench'
sys.path.insert(0, str(BENCH))
spec = importlib.util.spec_from_file_location('glob_benchmark', BENCH / 'run.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class BenchmarkGuards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        self.override = patch.object(bench, 'OUT', self.out)
        self.override.start()
        self.addCleanup(self.override.stop)
        self.tree = self.out / 'tree'
        (self.tree / 'a').mkdir(parents=True)
        (self.tree / 'a/main.goose').touch()
        (self.out / 'corpus.tsv').write_text('corpus')
        (self.out / 'walk-expected.txt').write_text('a/main.goose\n')
        self.dependency = self.out / 'dependency.goose'
        self.dependency.write_text('original')
        self.manifest = {
            'environment': bench.runtime_environment(),
            'source_hashes': bench.inputs(),
            'tools': {}, 'binaries': {}, 'node_dependencies': {},
            'external_sources': {str(self.dependency): bench.digest(self.dependency)},
            'fixture_entries': bench.fixture_entries(self.tree),
            'walk_expected_sha256': bench.digest(self.out / 'walk-expected.txt'),
            'corpus_sha256': bench.digest(self.out / 'corpus.tsv'),
        }
        bench.verify(self.manifest)

    def test_extra_empty_directory_rejected(self):
        (self.tree / 'extra').mkdir()
        with self.assertRaises(SystemExit):
            bench.verify(self.manifest)

    def test_directory_symlink_rejected(self):
        (self.tree / 'linked').symlink_to(self.tree / 'a', target_is_directory=True)
        with self.assertRaises(SystemExit):
            bench.verify(self.manifest)

    def test_runtime_environment_change_rejected(self):
        with patch.dict(os.environ, {'NODE_OPTIONS': '--jitless'}):
            with self.assertRaises(SystemExit):
                bench.verify(self.manifest)

    def test_dependency_source_change_rejected(self):
        self.dependency.write_text('modified')
        with self.assertRaises(SystemExit):
            bench.verify(self.manifest)

    def test_expected_path_manifest_change_rejected(self):
        (self.out / 'walk-expected.txt').write_text('different.goose\n')
        with self.assertRaises(SystemExit):
            bench.verify(self.manifest)


if __name__ == '__main__':
    unittest.main()
