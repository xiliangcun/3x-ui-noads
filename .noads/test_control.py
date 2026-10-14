import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('select_release', ROOT / 'select-release.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def release(tag, draft=False, prerelease=False):
    return {'tag_name': tag, 'draft': draft, 'prerelease': prerelease}

class ReleaseSelectionTests(unittest.TestCase):
    def test_catches_up_oldest_first_and_skips_development(self):
        upstream = [release('dev-latest', prerelease=True), release('v3.12.0'), release('v3.11.0'), release('v3.10.0'), release('v3.9.0')]
        self.assertEqual(module.select(upstream, [release('v3.10.0')])['tag_name'], 'v3.11.0')

    def test_incomplete_draft_is_retried(self):
        self.assertEqual(module.select([release('v3.10.0')], [release('v3.10.0', draft=True)])['tag_name'], 'v3.10.0')

    def test_published_version_is_never_rebuilt(self):
        self.assertIsNone(module.select([release('v3.10.0')], [release('v3.10.0')]))

    def test_arbitrary_tag_and_unpublished_release_are_rejected(self):
        for value in ('dev-latest', 'v3.11.0', 'v3.10.0;touch /tmp/example'):
            with self.assertRaises(ValueError):
                module.select([release('v3.10.0')], [], value)

if __name__ == '__main__':
    unittest.main()
