"""Verify owner-issued Ed25519 license certificates without storing signing secrets.

License JSON format:
{"payload": {"product": "PDF Studio Pro", "license_id": "...",
"device_id": "...", "expires_at": null}, "signature": "base64url"}
The canonical payload is sorted JSON with compact separators and UTF-8 encoding.
The signing private key must remain outside the public application repository.
"""
import base64
import json
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization


class LicenseError(ValueError):
    pass


def canonical_payload(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def verify_license(license_path, public_key_path, expected_device_id):
    """Fail closed unless a signed certificate matches this product and device."""
    try:
        certificate = json.loads(Path(license_path).read_text(encoding="utf-8"))
        payload = certificate["payload"]
        signature = certificate["signature"]
        if not isinstance(payload, dict) or not isinstance(signature, str):
            raise LicenseError("Invalid license format")
        if payload.get("product") != "PDF Studio Pro":
            raise LicenseError("Wrong product")
        if payload.get("device_id") != expected_device_id or not expected_device_id:
            raise LicenseError("License belongs to another device")
        if not payload.get("license_id"):
            raise LicenseError("Missing license identifier")
        if payload.get("expires_at") is not None:
            raise LicenseError("Expiring certificates are not supported by this lifetime verifier")
        public_key = serialization.load_pem_public_key(Path(public_key_path).read_bytes())
        raw = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        public_key.verify(raw, canonical_payload(payload))
        return payload
    except LicenseError:
        raise
    except (OSError, KeyError, TypeError, ValueError, InvalidSignature, AttributeError) as exc:
        raise LicenseError("License verification failed") from exc
