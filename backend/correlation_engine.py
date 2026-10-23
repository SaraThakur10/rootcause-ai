
import pandas as pd

from anomaly_detector import detect_anomalies

CORRELATION_WINDOW_MINUTES = 5


def correlate_events(
    logs: pd.DataFrame,
    events: pd.DataFrame,
) -> dict:
    required_event_columns = [
        "timestamp",
        "service",
        "event_type",
        "version",
        "description",
    ]

    missing = [
        column
        for column in required_event_columns
        if column not in events.columns
    ]

    if missing:
        raise ValueError(
            "Missing deployment event columns: "
            + ", ".join(missing)
        )

    if events.empty:
        return {
            "anomalies_analyzed": 0,
            "correlations_found": 0,
            "correlations": [],
            "notice": "No deployment events were provided.",
        }

    event_data = events[required_event_columns].copy()
    event_data["timestamp"] = pd.to_datetime(
        event_data["timestamp"],
        errors="coerce",
    )

    if event_data["timestamp"].isna().any():
        raise ValueError(
            "Deployment events contain invalid timestamps."
        )

    if event_data["service"].fillna("").astype(str).str.strip().eq("").any():
        raise ValueError(
            "Deployment event service names cannot be empty."
        )

    anomaly_result = detect_anomalies(logs)
    correlations = []

    for anomaly in anomaly_result["anomalies"]:
        anomaly_time = pd.Timestamp(anomaly["timestamp"])

        for _, event in event_data.iterrows():
            event_time = event["timestamp"]

            difference_minutes = (
                anomaly_time - event_time
            ).total_seconds() / 60

            if abs(difference_minutes) > CORRELATION_WINDOW_MINUTES:
                continue

            same_service = (
                str(event["service"]).strip().lower()
                in logs.loc[
                    pd.to_datetime(logs["timestamp"], errors="coerce")
                    .dt.floor("min") == anomaly_time,
                    "service",
                ].fillna("").astype(str).str.strip().str.lower().unique()
            )

            correlations.append({
                "anomaly_timestamp": anomaly["timestamp"],
                "anomaly_error_count": anomaly["error_count"],
                "event_timestamp": event_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "event_service": str(event["service"]),
                "event_type": str(event["event_type"]),
                "version": str(event["version"]),
                "description": str(event["description"]),
                "time_difference_minutes": round(
                    difference_minutes, 2
                ),
                "same_service": bool(same_service),
                "evidence": (
                    "Same service and nearby timestamp"
                    if same_service
                    else "Nearby timestamp; service match not established"
                ),
                "interpretation": (
                    "Potential investigation lead only; "
                    "temporal proximity does not prove causation."
                ),
            })

    correlations.sort(
        key=lambda item: (
            abs(item["time_difference_minutes"]),
            not item["same_service"],
        )
    )

    return {
        "anomalies_analyzed": len(anomaly_result["anomalies"]),
        "correlations_found": len(correlations),
        "correlation_window_minutes": CORRELATION_WINDOW_MINUTES,
        "correlations": correlations,
        "notice": (
            "Correlations indicate temporal proximity, not proof "
            "that a deployment or configuration change caused an anomaly."
        ),
    }
