# tests/test_client_ui.py
import unittest
import os

class TestClientAssets(unittest.TestCase):
    def test_required_pwa_files_exist(self):
        for f in ['client/index.html', 'client/style.css', 'client/app.js', 'client/touch_engine.js', 'client/protocol.js']:
            self.assertTrue(os.path.exists(f), f"Missing {f}")

    def test_index_html_contains_viewport_and_touch_action(self):
        with open('client/index.html', 'r') as f:
            content = f.read()
        self.assertIn('viewport', content)
        self.assertIn('touch-action: none', content)
        self.assertIn('preset-tekken', content)
        self.assertIn('preset-fifa', content)
        self.assertIn('id="btn-fullscreen"', content)
        self.assertIn('id="connection-indicator"', content)
