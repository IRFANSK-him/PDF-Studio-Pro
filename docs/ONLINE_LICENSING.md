# PDF Studio Pro — Online-Only Lifetime Licensing

## Status
Development implementation. Not production-deployed or security-audited. One license is permanently bound to one device until an authorized administrator resets the binding. A lifetime license means no expiry date, **not** permanent offline access. The desktop requires a successful online check before opening a PDF or running editing commands.

## Architecture
- Windows desktop: `src/pdf_studio/online_license.py`, `main.py`.
- Private HTTPS API: `license_server/app.py` (FastAPI + SQLite).
- Device identifier: SHA-256 of Windows MachineGuid with product-specific domain separator. A Windows reinstall may change it.
- License key: cryptographically random; database stores SHA-256 hashes of keys and devices, not the raw keys.
- Admin API: bearer token read from server environment, never committed or bundled.
- Endpoints: `POST /admin/licenses`, `POST /v1/activate`, `POST /v1/validate`, `POST /admin/revoke`, `POST /admin/reset-device`.

## Local development
Install `requirements.txt`. Set a 32+ character random `PDF_STUDIO_ADMIN_TOKEN` and `PDF_STUDIO_LICENSE_DB`. Start the server with `uvicorn license_server.app:app --host 127.0.0.1 --port 8000`. The desktop deliberately requires `PDF_STUDIO_LICENSE_URL=https://<your-domain>`, so a plain localhost HTTP server is **not** accepted. Use a real HTTPS endpoint for end-to-end tests.

Issue a key using an authenticated HTTPS request to `/admin/licenses`. Activate with the desktop **Activate License** toolbar action. The desktop saves the license key under the user's LOCALAPPDATA; production should move the key into Windows Credential Manager or DPAPI-protected storage.

## Before production deployment
1. Deploy API on a private service behind TLS termination and trusted proxy configuration; protect admin endpoints with separate network restrictions and stronger operator authentication. Do not expose the admin bearer token in source, logs or desktop binaries.
2. Add request throttling, monitoring, audit logging, backups, database migrations and transactional concurrency tests; SQLite with a Python lock is only appropriate for a single-process prototype.
3. Add key storage protection on Windows, certificate validation tests, device fingerprint resilience and anti-tamper protections. A Python desktop licensing check can be patched; do not promise unbreakable enforcement.
4. Define a device-transfer and support policy. Device reset is administrator-only.
5. Test all PDF commands against server failure, revocation, PC replacement and concurrent activation. Consider disabling existing document interactions immediately when verification fails.
6. Do not publish an installer or represent this as production licensing until security review and Windows integration tests pass.
