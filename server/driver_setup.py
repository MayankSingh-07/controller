import sys
import os
import subprocess
import tempfile
import urllib.request
import shutil

VIGEMBUS_DOWNLOAD_URL = "https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/ViGEmBus_1.22.0_x64_x86_arm64.exe"

def check_vigembus_installed() -> bool:
    """Checks whether the ViGEmBus kernel driver is installed on Windows."""
    if not sys.platform.startswith('win'):
        return True

    # 1. Check if the Windows driver service is registered
    try:
        res = subprocess.run(
            ["sc", "query", "ViGEmBus"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3
        )
        if res.returncode == 0 and "ViGEmBus" in res.stdout:
            return True
    except Exception:
        pass

    # 2. Try importing vgamepad and instantiating
    try:
        import vgamepad as vg
        pad = vg.VX360Gamepad()
        del pad
        return True
    except Exception:
        return False

def download_and_install_vigembus() -> bool:
    """Automatically downloads and installs the official ViGEmBus driver."""
    if not sys.platform.startswith('win'):
        print("[Setup] ViGEmBus is only required on Windows.")
        return True

    print("\n" + "=" * 60)
    print("⚡ AUTOMATIC DRIVER INSTALLATION")
    print("   ViGEmBus is required so Windows recognizes your phone as an authentic")
    print("   Xbox 360 controller in FIFA, Tekken, Steam, and PC games.")
    print("=" * 60)
    print(f"[1/2] Downloading official ViGEmBus installer from GitHub...")

    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, "ViGEmBus_Setup.exe")

    try:
        urllib.request.urlretrieve(VIGEMBUS_DOWNLOAD_URL, installer_path)
        print(f"[2/2] Running ViGEmBus installer. Please click 'Yes' if prompted by Windows...")
        
        # Run installer with passive progress display
        result = subprocess.run([installer_path, "/passive"], check=False)
        if result.returncode == 0:
            print("[✓] ViGEmBus driver installed successfully!")
            return True
        else:
            # Fallback to interactive mode if passive fails
            print("[!] Running interactive installer...")
            subprocess.run([installer_path], check=False)
            return check_vigembus_installed()
    except Exception as e:
        print(f"[!] Error during automatic driver installation: {e}")
        print(f"    You can manually download the installer at: {VIGEMBUS_DOWNLOAD_URL}")
        return False

def ensure_dependencies() -> bool:
    """Ensures python dependencies like vgamepad are installed automatically."""
    try:
        import vgamepad
        return True
    except ImportError:
        if sys.platform.startswith('win'):
            print("\n[*] Installing required gamepad driver package (vgamepad)...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "vgamepad>=0.3.3"])
                print("[✓] 'vgamepad' installed successfully!")
                return True
            except Exception as e:
                print(f"[!] Failed to auto-install vgamepad: {e}")
                return False
        return True

def auto_setup():
    """Performs full automated pre-flight setup on Windows."""
    if sys.platform.startswith('win'):
        ensure_dependencies()
        if not check_vigembus_installed():
            download_and_install_vigembus()
