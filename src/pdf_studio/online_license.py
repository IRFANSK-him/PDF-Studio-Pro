"""Online-only activation client. No offline grace period."""
import hashlib
import json
import os
from pathlib import Path
import platform
import uuid
import httpx

def device_id():
    if os.name == "nt":
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            raw = winreg.QueryValueEx(key, "MachineGuid")[0]
    else:
        raw = platform.node() + ":" + str(uuid.getnode())
    return hashlib.sha256(("PDF-Studio-Pro:v1:" + raw).encode()).hexdigest()

def license_file():
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".config"))) / "PDFStudioPro" / "license.json"

def server_url():
    url = os.environ.get("PDF_STUDIO_LICENSE_URL", "").rstrip("/")
    if not url.startswith("https://"):
        raise ValueError("HTTPS licensing server URL is required")
    return url

def request_license(endpoint, key):
    response = httpx.post(server_url() + endpoint,
                          json={"license_key": key, "device_id": device_id()},
                          timeout=10, follow_redirects=False)
    response.raise_for_status()
    result = response.json()
    if result.get("active") is not True or result.get("product") != "PDF Studio Pro":
        raise ValueError("Unexpected licensing response")
    return True

def activate(key):
    request_license("/v1/activate", key)
    path = license_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"license_key": key}), encoding="utf-8")
    if os.name != "nt":
        path.chmod(0o600)
    return True

def validate_saved_license():
    path = license_file()
    if not path.exists():
        return False
    return request_license("/v1/validate", json.loads(path.read_text(encoding="utf-8"))["license_key"])
