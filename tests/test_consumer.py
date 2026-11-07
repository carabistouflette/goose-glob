# SPDX-License-Identifier: Apache-2.0
"""Guard version input and external-client isolation."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/check-consumer.py'
spec = importlib.util.spec_from_file_location('consumer_check', SCRIPT)
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)


class ConsumerGuards(unittest.TestCase):
    def test_version_tags(self):
        for tag in ('v0.1.0', 'v0.1.1-alpha.1'):
            self.assertTrue(consumer.consumer_import(tag, None).endswith('@'+tag))
        for tag in ('', 'main', '../v0.1.0', 'v0.1.0\n', 'v0.1.0"; import os;', 'v0.1.0/x'):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                consumer.consumer_import(tag, None)

    def test_source_requires_both_modules(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'quoted " package'
            root.mkdir()
            (root/'glob.goose').touch()
            with self.assertRaises(ValueError):
                consumer.consumer_import(None, root)
            (root/'walk.goose').touch()
            self.assertEqual(consumer.consumer_import(None, root), str(root.resolve()))

    def test_client_ignores_ambient_packages_and_git_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            goose = Path(directory)/'goose'
            goose.touch()
            observations = []
            def run(argv, **kwargs):
                client = kwargs['cwd']
                env = kwargs['env']
                observations.append((client, env, list(argv)))
                self.assertFalse(client.is_relative_to(consumer.ROOT))
                self.assertEqual(Path(env['GOOSE_HOME']).parent, client)
                self.assertNotIn('GOOSE_STDLIB', env)
                self.assertNotIn('GIT_CONFIG_COUNT', env)
                self.assertNotIn('GIT_ASKPASS', env)
                self.assertEqual(env['GIT_CONFIG_GLOBAL'], os.devnull)
                self.assertEqual(env['GIT_CONFIG_NOSYSTEM'], '1')
                self.assertEqual(env['GIT_TERMINAL_PROMPT'], '0')
                source = (client/'main.goose').read_text()
                self.assertIn(json.dumps(consumer.IMPORT), source)
                self.assertTrue((client/'fixture/nested/a.goose').is_file())
                self.assertTrue(kwargs['check'])
            dirty = {'GOOSE_HOME': '/stale', 'GOOSE_STDLIB': '/stale/stdlib',
                     'GIT_CONFIG_COUNT': '1', 'GIT_ASKPASS': '/credential-helper'}
            with patch.dict(os.environ, dirty), patch.object(sys, 'argv', [str(SCRIPT), '--goose', str(goose), '--tag', 'v0.1.0']), patch.object(consumer.subprocess, 'run', side_effect=run):
                consumer.main()
            self.assertEqual(len(observations), 3)
            self.assertFalse(observations[0][0].exists())
