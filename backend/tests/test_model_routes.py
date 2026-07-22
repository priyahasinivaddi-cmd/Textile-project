"""API tests for textile composition model endpoints."""

from io import BytesIO

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.routes import model as model_routes
from app.services.model_service import ModelService


class FakeModel:
    output_shape = (None, 2)

    def predict(self, _batch, verbose=0):
        return np.array([[80.0, 20.0]], dtype=np.float32)


def make_service() -> ModelService:
    service = ModelService()
    service.model = FakeModel()
    service.target_columns = ["cotton_pct", "polyester_pct"]
    return service


def make_png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color=(80, 120, 160)).save(buffer, format="PNG")
    return buffer.getvalue()


def make_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(model_routes, "model_service", make_service())
    app = FastAPI()
    app.include_router(model_routes.router)
    return TestClient(app)


def test_model_status(monkeypatch):
    response = make_client(monkeypatch).get("/api/model/status")
    assert response.status_code == 200
    assert response.json()["outputs_match_target_labels"] is True


def test_valid_image_prediction(monkeypatch):
    response = make_client(monkeypatch).post(
        "/api/model/predict-composition",
        files={"file": ("fabric.png", make_png(), "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["dominant_fibre"] == "cotton"
    assert body["total_percentage"] == 100.0


def test_unsupported_file_type(monkeypatch):
    response = make_client(monkeypatch).post(
        "/api/model/predict-composition",
        files={"file": ("fabric.gif", b"GIF89a", "image/gif")},
    )
    assert response.status_code == 415


def test_missing_file(monkeypatch):
    response = make_client(monkeypatch).post("/api/model/predict-composition")
    assert response.status_code == 422


def test_corrupted_image(monkeypatch):
    response = make_client(monkeypatch).post(
        "/api/model/predict-composition",
        files={"file": ("broken.png", b"not an image", "image/png")},
    )
    assert response.status_code == 400
