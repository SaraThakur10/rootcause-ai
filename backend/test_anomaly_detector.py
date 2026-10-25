
import pandas as pd
import pytest

from anomaly_detector import detect_anomalies


def create_test_logs():
    rows = []

    for minute in range(12):
        for i in range(10):
            if minute == 11:
                level = (
                    "ERROR" if i < 8 else
                    "WARNING" if i == 8 else
                    "INFO"
                )
            else:
                level = (
                    "ERROR" if i == 0 else
                    "WARNING" if i == 1 else
                    "INFO"
                )

            rows.append({
                "timestamp": f"2026-10-24 10:{minute:02d}:00",
                "service": "payment-service",
                "level": level,
                "message": f"Test log {i}",
            })

    return pd.DataFrame(rows)


def test_error_spike_detection():
    result = detect_anomalies(create_test_logs())

    assert result["windows_analyzed"] == 12
    assert result["ml_status"] == "available"
    assert result["anomalies_detected"] >= 1

    assert any(
        anomaly["timestamp"] == "2026-10-24 10:11:00"
        for anomaly in result["anomalies"]
    ), "Expected error spike was not detected."


def test_insufficient_data():
    rows = []

    for minute in range(5):
        rows.append({
            "timestamp": f"2026-10-24 11:{minute:02d}:00",
            "service": "payment-service",
            "level": "INFO",
            "message": f"Test log {minute}",
        })

    result = detect_anomalies(pd.DataFrame(rows))

    assert result["windows_analyzed"] == 5
    assert result["ml_status"] == "insufficient_data"
    assert all(not w["ml_anomaly"] for w in result["windows"])


def test_normal_logs():
    rows = []

    for minute in range(15):
        for i in range(10):
            level = (
                "ERROR" if i == 0 else
                "WARNING" if i == 1 else
                "INFO"
            )

            rows.append({
                "timestamp": f"2026-10-24 12:{minute:02d}:00",
                "service": "payment-service",
                "level": level,
                "message": f"Normal log {i}",
            })

    result = detect_anomalies(pd.DataFrame(rows))

    assert result["windows_analyzed"] == 15
    assert result["anomalies_detected"] == 0


def test_missing_columns():
    data = pd.DataFrame({
        "timestamp": ["2026-10-24 13:00:00"],
        "service": ["payment-service"],
        "level": ["ERROR"],
    })

    with pytest.raises(ValueError, match="Missing required columns"):
        detect_anomalies(data)


def test_invalid_timestamp():
    data = pd.DataFrame({
        "timestamp": ["not-a-valid-date"],
        "service": ["payment-service"],
        "level": ["ERROR"],
        "message": ["Test error"],
    })

    with pytest.raises(ValueError, match="timestamps are invalid"):
        detect_anomalies(data)


def test_empty_data():
    data = pd.DataFrame(
        columns=["timestamp", "service", "level", "message"]
    )

    result = detect_anomalies(data)

    assert result["windows_analyzed"] == 0
    assert result["anomalies_detected"] == 0
    assert result["notice"] == "No log records were provided."


def test_blank_service():
    data = pd.DataFrame({
        "timestamp": ["2026-10-24 14:00:00"],
        "service": ["   "],
        "level": ["ERROR"],
        "message": ["Test error"],
    })

    with pytest.raises(ValueError, match="Service names cannot be empty"):
        detect_anomalies(data)

