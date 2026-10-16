# tests/test_driver_setup.py
import unittest
from unittest.mock import patch, MagicMock
from server.driver_setup import (
    VIGEMBUS_DOWNLOAD_URL,
    check_vigembus_installed,
    ensure_dependencies
)

class TestDriverSetup(unittest.TestCase):
    def test_vigembus_url_is_valid_github_release(self):
        self.assertTrue(VIGEMBUS_DOWNLOAD_URL.startswith("https://github.com/nefarius/ViGEmBus/releases/download/"))
        self.assertTrue(VIGEMBUS_DOWNLOAD_URL.endswith(".exe"))

    @patch('sys.platform', 'linux')
    def test_check_vigembus_returns_true_on_non_windows(self):
        # On non-Windows platforms (like Linux/Mac development), ViGEmBus is not needed
        self.assertTrue(check_vigembus_installed())

    @patch('sys.platform', 'win32')
    @patch('subprocess.run')
    def test_check_vigembus_on_windows_detected(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="SERVICE_NAME: ViGEmBus\nSTATE: RUNNING")
        self.assertTrue(check_vigembus_installed())
