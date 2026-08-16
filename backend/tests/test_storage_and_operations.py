from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware import operations_middleware
from app.services.storage_service import LocalStorageProvider


def test_local_storage_uses_safe_server_key(tmp_path):
    provider = LocalStorageProvider(str(tmp_path))
    url = provider.save("../safe-image.png", b"image", "image/png")
    assert url == "/static/uploads/safe-image.png"
    assert (tmp_path / "safe-image.png").read_bytes() == b"image"
    provider.delete(url)
    assert not (tmp_path / "safe-image.png").exists()


def test_operations_middleware_sets_trace_and_security_headers():
    app = FastAPI(); app.middleware("http")(operations_middleware)
    @app.get("/check")
    def check(): return {"ok": True}
    response = TestClient(app).get("/check", headers={"X-Request-ID": "test-request"})
    assert response.headers["X-Request-ID"] == "test-request"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
