import socket
import subprocess
import shutil
import os
from typing import List, Dict

def get_local_ips() -> List[Dict[str, str]]:
    """Discovers all local network interface IPs categorized by connection type."""
    discovered = []
    seen_ips = set()

    # Always include localhost
    discovered.append({'iface': 'lo', 'ip': '127.0.0.1', 'type': 'localhost'})
    seen_ips.add('127.0.0.1')

    # Primary route discovery via outbound probe socket (doesn't send traffic)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        primary_ip = s.getsockname()[0]
        s.close()
        if primary_ip not in seen_ips:
            conn_type = 'usb_tether' if primary_ip.startswith('192.168.42.') else 'wifi'
            discovered.append({'iface': 'primary', 'ip': primary_ip, 'type': conn_type})
            seen_ips.add(primary_ip)
    except Exception:
        pass

    # Try resolving hostname
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip not in seen_ips:
                conn_type = 'usb_tether' if ip.startswith('192.168.42.') else 'wifi'
                discovered.append({'iface': 'host', 'ip': ip, 'type': conn_type})
                seen_ips.add(ip)
    except Exception:
        pass

    return discovered

def format_connection_urls(ips: List[Dict[str, str]], port: int = 8080) -> Dict[str, str]:
    """Formats connection URLs categorized by transport type."""
    urls = {}
    for item in ips:
        t = item['type']
        url = f"http://{item['ip']}:{port}"
        urls[t] = url
    return urls

def check_and_run_adb_reverse(port: int = 8080) -> bool:
    """Checks if ADB is available and runs reverse port forwarding."""
    adb_path = shutil.which('adb')
    if not adb_path:
        return False
    try:
        res = subprocess.run(
            [adb_path, 'reverse', f'tcp:{port}', f'tcp:{port}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        return res.returncode == 0
    except Exception:
        return False

def generate_terminal_qr(url: str) -> str:
    """Generates an ASCII box with URL instructions for terminal display."""
    width = max(len(url) + 4, 46)
    border = "═" * width
    lines = [
        f"╔{border}╗",
        f"║  CONNECT CONTROLLER PHONE{' ' * (width - 27)}║",
        f"╟{border}╢",
        f"║  Open Chrome on your phone and go to:{' ' * (width - 40)}║",
        f"║  👉 {url}{' ' * (width - len(url) - 5)}║",
        f"║{' ' * width}║",
        f"║  • Sub-1ms over USB Cable (USB Tethering/ADB){' ' * (width - 48)}║",
        f"║  • Sub-5ms over Wi-Fi (Same home network){' ' * (width - 44)}║",
        f"╚{border}╝"
    ]
    return "\n".join(lines)
