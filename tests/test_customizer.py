# tests/test_customizer.py
import unittest
import json
import os

class TestCustomizerSpec(unittest.TestCase):
    def test_custom_layout_schema(self):
        default_layout = {
            "dpad": {"x": 10, "y": 50, "scale": 1.0},
            "stick": {"x": 10, "y": 50, "scale": 1.0},
            "buttons": {"x": 80, "y": 50, "scale": 1.0},
            "triggers": {"x": 50, "y": 5, "scale": 1.0}
        }
        serialized = json.dumps(default_layout)
        loaded = json.loads(serialized)
        for key in ["dpad", "stick", "buttons", "triggers"]:
            self.assertIn(key, loaded)
            self.assertIn("scale", loaded[key])

    def test_customizer_js_exists_and_implements_layout_manager(self):
        js_path = 'client/customizer.js'
        self.assertTrue(os.path.exists(js_path), f"Missing {js_path}")
        with open(js_path, 'r') as f:
            content = f.read()
        self.assertIn('LayoutManager', content)
        self.assertIn('enableEditMode', content)
        self.assertIn('saveLayout', content)
        self.assertIn('loadLayout', content)
