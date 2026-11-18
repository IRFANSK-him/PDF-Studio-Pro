"""Online-only one-PC licensing service; deploy behind HTTPS."""
import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="PDF Studio Pro License API", docs_url=None, redoc_url=None, openapi_url=None)
_lock = threading.RLock()

@contextmanager
def connection():
    with _lock:
        db = sqlite3.connect(Path(os.environ.get("PDF_STUDIO_LICENSE_DB", "licenses.sqlite3")), timeout=30)
        try:
            db.execute("CREATE TABLE IF NOT EXISTS licenses (key_hash TEXT PRIMARY KEY, device_hash TEXT, revoked INTEGER NOT NULL DEFAULT 0)")
            db.commit()
            yield db
            db.commit()
        finally:
            db.close()

def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def admin_auth(authorization: str = Header(default="")):
    secret = os.environ.get("PDF_STUDIO_ADMIN_TOKEN", "")
    if len(secret) < 32 or not hmac.compare_digest(authorization, "Bearer " + secret):
        raise HTTPException(status_code=403, detail="Unauthorized")

class LicenseRequest(BaseModel):
    license_key: str = Field(min_length=20, max_length=128)
    device_id: str = Field(min_length=32, max_length=128)

class AdminLicense(BaseModel):
    license_key: str = Field(min_length=20, max_length=128)

@app.post("/admin/licenses", dependencies=[Depends(admin_auth)])
def issue_license():
    key = "PSP-" + secrets.token_urlsafe(32)
    with connection() as db:
        db.execute("INSERT INTO licenses (key_hash, device_hash) VALUES (?, NULL)", (digest(key),))
    return {"license_key": key}

@app.post("/v1/activate")
def activate(request: LicenseRequest):
    key_hash, device_hash = digest(request.license_key), digest(request.device_id)
    with connection() as db:
        row = db.execute("SELECT device_hash, revoked FROM licenses WHERE key_hash=?", (key_hash,)).fetchone()
        if row is None or row[1]:
            raise HTTPException(status_code=403, detail="Invalid or revoked license")
        if row[0] is not None and not hmac.compare_digest(row[0], device_hash):
            raise HTTPException(status_code=409, detail="License assigned to another device")
        db.execute("UPDATE licenses SET device_hash=? WHERE key_hash=? AND device_hash IS NULL", (device_hash, key_hash))
    return {"active": True, "product": "PDF Studio Pro"}

@app.post("/v1/validate")
def validate(request: LicenseRequest):
    with connection() as db:
        row = db.execute("SELECT device_hash, revoked FROM licenses WHERE key_hash=?", (digest(request.license_key),)).fetchone()
    if not row or row[1] or not row[0] or not hmac.compare_digest(row[0], digest(request.device_id)):
        raise HTTPException(status_code=403, detail="License not active on this device")
    return {"active": True, "product": "PDF Studio Pro"}

@app.post("/admin/revoke", dependencies=[Depends(admin_auth)])
def revoke(request: AdminLicense):
    with connection() as db:
        result = db.execute("UPDATE licenses SET revoked=1 WHERE key_hash=?", (digest(request.license_key),))
        if not result.rowcount:
            raise HTTPException(status_code=404, detail="Unknown license")
    return {"revoked": True}

@app.post("/admin/reset-device", dependencies=[Depends(admin_auth)])
def reset_device(request: AdminLicense):
    with connection() as db:
        result = db.execute("UPDATE licenses SET device_hash=NULL WHERE key_hash=? AND revoked=0", (digest(request.license_key),))
        if not result.rowcount:
            raise HTTPException(status_code=404, detail="Unknown or revoked license")
    return {"reset": True}
