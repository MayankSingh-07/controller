# tests/test_server.py
import unittest
from server.discovery import get_local_ips, format_connection_urls, generate_terminal_qr

class TestServerDiscovery(unittest.TestCase):
    def test_local_ip_discovery_returns_non_empty_list(self):
        ips = get_local_ips()
        self.assertIsInstance(ips, list)
        self.assertTrue(len(ips) > 0)
        for item in ips:
            self.assertIn('ip', item)
            self.assertIn('type', item)

    def test_format_connection_urls(self):
        mock_ips = [
            {'iface': 'wlan0', 'ip': '192.168.1.50', 'type': 'wifi'},
            {'iface': 'rndis0', 'ip': '192.168.42.10', 'type': 'usb_tether'}
        ]
        urls = format_connection_urls(mock_ips, port=8080)
        self.assertIn('wifi', urls)
        self.assertIn('usb_tether', urls)
        self.assertIn('http://192.168.1.50:8080', urls['wifi'])
        self.assertIn('http://192.168.42.10:8080', urls['usb_tether'])

    def test_generate_terminal_qr_creates_text(self):
        qr_text = generate_terminal_qr("http://192.168.1.50:8080")
        self.assertIsInstance(qr_text, str)
        self.assertTrue(len(qr_text) > 0)
