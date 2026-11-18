import sys
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from license_server.app import app

def test_activation_binding_revoke_and_reset(tmp_path, monkeypatch):
    monkeypatch.setenv("PDF_STUDIO_LICENSE_DB", str(tmp_path / "licenses.db"))
    monkeypatch.setenv("PDF_STUDIO_ADMIN_TOKEN", "a" * 48)
    client = TestClient(app)
    headers = {"Authorization": "Bearer " + "a" * 48}
    assert client.post("/admin/licenses").status_code == 403
    key = client.post("/admin/licenses", headers=headers).json()["license_key"]
    one = {"license_key": key, "device_id": "1" * 64}
    two = {"license_key": key, "device_id": "2" * 64}
    assert client.post("/v1/activate", json=one).status_code == 200
    assert client.post("/v1/activate", json=one).status_code == 200
    assert client.post("/v1/activate", json=two).status_code == 409
    assert client.post("/v1/validate", json=one).status_code == 200
    assert client.post("/admin/reset-device", json={"license_key": key}, headers=headers).status_code == 200
    assert client.post("/v1/activate", json=two).status_code == 200
    assert client.post("/admin/revoke", json={"license_key": key}, headers=headers).status_code == 200
    assert client.post("/v1/validate", json=two).status_code == 403
