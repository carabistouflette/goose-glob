# SPDX-License-Identifier: Apache-2.0
"""Checks for the separate benchmark's fixture and outcome guards."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'bench'))
import independent


class Independent(unittest.TestCase):
    def test_natural_hit_ratio_and_incomplete_cycle(self):
        self.assertEqual(independent.checksum([0, 1, 0, 0, 1], 13), 5)
        self.assertEqual(independent.checksum([0, 0, 0], 17), 0)
        self.assertEqual(independent.checksum([1, 1], 3), 3)

    def test_frozen_corpus_has_twelve_complete_groups(self):
        rows = independent.rows()
        names = list(dict.fromkeys(r[0] for r in rows))
        self.assertEqual(len(names), 12)
        self.assertEqual(len(rows), 4 * (768 + 255 + 49))
        for name in names:
            self.assertTrue(all(r[1] == next(r[1] for r in rows if r[0] == name)
                                for r in rows if r[0] == name))

    def test_collection_fixture_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'corpus.tsv').write_text('frozen')
            fixtures = {'deep': independent.make_tree(root/'deep', 'deep')}
            args = root, independent.run.digest(independent.FROZEN), independent.run.digest(root/'corpus.tsv'), fixtures
            independent.verify_fixtures(*args)
            (root/'deep/tree/extra.txt').touch()
            with self.assertRaisesRegex(SystemExit, 'fixture changed'):
                independent.verify_fixtures(*args)

    def test_path_manifest_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'corpus.tsv').write_text('frozen')
            fixtures = {'wide': independent.make_tree(root/'wide', 'wide')}
            (root/'wide/walk-expected.txt').write_text('wrong\n')
            with self.assertRaisesRegex(SystemExit, 'fixture changed'):
                independent.verify_fixtures(root, independent.run.digest(independent.FROZEN),
                                            independent.run.digest(root/'corpus.tsv'), fixtures)


if __name__ == '__main__':
    unittest.main()
