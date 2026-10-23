
import pandas as pd
from sklearn.ensemble import IsolationForest


REQUIRED_COLUMNS = ["timestamp", "service", "level", "message"]


def detect_anomalies(data: pd.DataFrame) -> dict:
    """
    Detect unusual application activity using:
    1. A robust statistical baseline.
    2. An Isolation Forest model.

    Each row in the output represents one minute of log activity.
    """

    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing)
        )

    if data.empty:
        return {
            "windows_analyzed": 0,
            "anomalies_detected": 0,
            "method": "Statistical baseline + Isolation Forest",
            "anomalies": [],
            "windows": [],
            "notice": "No log records were provided.",
        }

    logs = data[REQUIRED_COLUMNS].copy()

    logs["timestamp"] = pd.to_datetime(
        logs["timestamp"], errors="coerce"
    )
    logs["level"] = logs["level"].fillna("").astype(str).str.upper()
    logs["service"] = logs["service"].fillna("").astype(str)

    if logs["timestamp"].isna().any():
        raise ValueError("One or more timestamps are invalid.")

    if (logs["service"].str.strip() == "").any():
        raise ValueError("Service names cannot be empty.")

    # Create one-minute time windows.
    logs["window"] = logs["timestamp"].dt.floor("min")
    logs["is_error"] = logs["level"].isin(["ERROR", "CRITICAL"]).astype(int)
    logs["is_warning"] = (logs["level"] == "WARNING").astype(int)

    # Aggregate raw logs into numerical features for ML.
    features = (
        logs.groupby("window")
        .agg(
            total_logs=("message", "size"),
            error_count=("is_error", "sum"),
            warning_count=("is_warning", "sum"),
            active_services=("service", "nunique"),
        )
        .sort_index()
    )

    features["error_rate"] = (
        features["error_count"] /
        features["total_logs"].clip(lower=1)
    )

    feature_columns = [
        "total_logs",
        "error_count",
        "warning_count",
        "active_services",
        "error_rate",
    ]

    # Statistical baseline: median + 3 times the MAD.
    # MAD = median absolute deviation.
    error_values = features["error_count"]
    median_errors = float(error_values.median())
    mad = float((error_values - median_errors).abs().median())

    if mad > 0:
        statistical_threshold = median_errors + (3 * 1.4826 * mad)
    else:
        statistical_threshold = median_errors

    features["statistical_anomaly"] = (
        (features["error_count"] > statistical_threshold)
        & (features["error_count"] > 0)
    )

    # Isolation Forest needs multiple time windows to learn a pattern.
    # With very little data, do not pretend its predictions are reliable.
    if len(features) >= 10:
        model = IsolationForest(
            n_estimators=100,
            contamination="auto",
            random_state=42,
        )

        predictions = model.fit_predict(features[feature_columns])
        features["ml_anomaly"] = predictions == -1
        ml_status = "available"
    else:
        features["ml_anomaly"] = False
        ml_status = "insufficient_data"

    # Combine the independent signals.
    features["anomaly"] = (
        features["statistical_anomaly"] | features["ml_anomaly"]
    )

    results = []

    for timestamp, row in features.iterrows():
        reasons = []

        if row["statistical_anomaly"]:
            reasons.append("Error count exceeds the statistical baseline")

        if row["ml_anomaly"]:
            reasons.append("Isolation Forest flagged an unusual feature pattern")

        if not reasons:
            continue

        results.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "total_logs": int(row["total_logs"]),
            "error_count": int(row["error_count"]),
            "warning_count": int(row["warning_count"]),
            "active_services": int(row["active_services"]),
            "error_rate": round(float(row["error_rate"]), 3),
            "statistical_anomaly": bool(row["statistical_anomaly"]),
            "ml_anomaly": bool(row["ml_anomaly"]),
            "reasons": reasons,
        })

    windows = []

    for timestamp, row in features.iterrows():
        windows.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "total_logs": int(row["total_logs"]),
            "error_count": int(row["error_count"]),
            "warning_count": int(row["warning_count"]),
            "active_services": int(row["active_services"]),
            "error_rate": round(float(row["error_rate"]), 3),
            "statistical_anomaly": bool(row["statistical_anomaly"]),
            "ml_anomaly": bool(row["ml_anomaly"]),
            "anomaly": bool(row["anomaly"]),
        })

    return {
        "windows_analyzed": int(len(features)),
        "anomalies_detected": len(results),
        "method": "Statistical baseline + Isolation Forest",
        "ml_status": ml_status,
        "statistical_threshold": round(statistical_threshold, 3),
        "anomalies": results,
        "windows": windows,
        "notice": (
            "Exploratory results only. An anomaly is unusual activity, "
            "not proof of a production incident or its root cause."
        ),
    }
