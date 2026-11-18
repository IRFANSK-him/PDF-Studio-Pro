import base64
import json
import sys
from pathlib import Path
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pdf_studio.licensing import canonical_payload, verify_license, LicenseError


def test_valid_and_tampered_license(tmp_path):
    private = Ed25519PrivateKey.generate()
    pub = tmp_path / "public.pem"
    pub.write_bytes(private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    payload = {"product": "PDF Studio Pro", "license_id": "sample-1",
               "device_id": "test-device", "expires_at": None}
    signature = base64.urlsafe_b64encode(private.sign(canonical_payload(payload))).decode().rstrip("=")
    path = tmp_path / "license.json"
    path.write_text(json.dumps({"payload": payload, "signature": signature}))
    assert verify_license(path, pub, "test-device") == payload
    with pytest.raises(LicenseError):
        verify_license(path, pub, "other-device")
    payload["license_id"] = "forged"
    path.write_text(json.dumps({"payload": payload, "signature": signature}))
    with pytest.raises(LicenseError):
        verify_license(path, pub, "test-device")
