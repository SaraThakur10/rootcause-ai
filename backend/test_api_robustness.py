
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_logs_upload_rejects_non_csv():
    response = client.post(
        "/api/logs/analyze",
        files={"file": ("logs.txt", b"some text", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Please upload a CSV file."


def test_logs_upload_rejects_empty_file():
    response = client.post(
        "/api/logs/analyze",
        files={"file": ("logs.csv", b"", "text/csv")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is empty."


def test_logs_upload_rejects_invalid_csv():
    response = client.post(
        "/api/logs/analyze",
        files={
            "file": (
                "logs.csv",
                b"\xff\xfe\xfa",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400

import pytest


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/logs/analyze",
        "/api/anomalies/analyze",
        "/api/investigation/analyze",
    ],
)
def test_all_upload_endpoints_reject_non_csv(endpoint):
    response = client.post(
        endpoint,
        files={"file": ("logs.txt", b"some text", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Please upload a CSV file."

@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/logs/analyze",
        "/api/anomalies/analyze",
        "/api/investigation/analyze",
    ],
)
def test_all_upload_endpoints_reject_empty_files(endpoint):
    response = client.post(
        endpoint,
        files={"file": ("logs.csv", b"", "text/csv")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is empty."


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/logs/analyze",
        "/api/anomalies/analyze",
        "/api/investigation/analyze",
    ],
)
def test_all_upload_endpoints_reject_missing_columns(endpoint):
    csv_content = (
        "timestamp,service,level\n"
        "2026-10-24 10:00:00,payment-service,ERROR\n"
    )

    response = client.post(
        endpoint,
        files={
            "file": (
                "logs.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]

@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/logs/analyze",
        "/api/anomalies/analyze",
        "/api/investigation/analyze",
    ],
)
def test_all_upload_endpoints_reject_invalid_timestamps(endpoint):
    csv_content = (
        "timestamp,service,level,message\n"
        "not-a-valid-date,payment-service,ERROR,Test error\n"
    )

    response = client.post(
        endpoint,
        files={
            "file": (
                "logs.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 400

@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/logs/analyze",
        "/api/anomalies/analyze",
        "/api/investigation/analyze",
    ],
)
def test_all_upload_endpoints_reject_invalid_utf8(endpoint):
    response = client.post(
        endpoint,
        files={
            "file": (
                "logs.csv",
                b"\xff\xfe\xfa",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400

@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/logs/analyze",
        "/api/anomalies/analyze",
        "/api/investigation/analyze",
    ],
)
def test_all_upload_endpoints_reject_oversized_files(endpoint):
    oversized_content = b"x" * (10 * 1024 * 1024 + 1)

    response = client.post(
        endpoint,
        files={
            "file": (
                "logs.csv",
                oversized_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "File too large. Maximum upload size is 10 MB."
    )
