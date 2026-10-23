import pandas as pd

from anomaly_detector import detect_anomalies
from correlation_engine import correlate_events


def investigate_root_causes(
    logs: pd.DataFrame,
    events: pd.DataFrame,
) -> dict:
    # Handle an empty CSV before calling the analysis engines.
    if logs is None or logs.empty:
        return {
            "anomalies_analyzed": 0,
            "deployment_correlations": 0,
            "hypotheses_generated": 0,
            "hypotheses": [],
            "notice": (
                "No log records were provided. Upload a CSV containing "
                "log records to investigate potential root causes."
            ),
        }

    anomaly_result = detect_anomalies(logs)
    correlation_result = correlate_events(logs, events)

    hypotheses = []

    anomaly_timestamps = {
        pd.Timestamp(item["timestamp"])
        for item in anomaly_result.get("anomalies", [])
        if item.get("timestamp") is not None
    }

    # Hypothesis 1: A deployment or configuration change
    # may be related to an anomaly.
    for correlation in correlation_result.get("correlations", []):
        if not correlation.get("same_service", False):
            continue

        event_type = str(correlation.get("event_type", "")).upper()

        if event_type not in {"DEPLOYMENT", "CONFIG_CHANGE"}:
            continue

        time_difference = abs(
            float(correlation.get("time_difference_minutes", 0))
        )

        if time_difference <= 2:
            priority = "High"
            confidence = "Moderate"
        else:
            priority = "Medium"
            confidence = "Low"

        event_service = str(correlation.get("event_service", "Unknown"))

        hypotheses.append({
            "title": (
                f"Recent {event_type.lower()} may be related "
                f"to an anomaly in {event_service}"
            ),
            "service": event_service,
            "confidence": confidence,
            "priority": priority,
            "evidence": [
                "Anomaly detected at "
                + str(correlation.get("anomaly_timestamp", "Unknown")),
                "Change recorded at "
                + str(correlation.get("event_timestamp", "Unknown")),
                "Change type: " + event_type,
                "Version or configuration: "
                + str(correlation.get("version", "Unknown")),
                "Time difference in minutes: "
                + str(correlation.get("time_difference_minutes", "Unknown")),
                "Anomaly error count: "
                + str(correlation.get("anomaly_error_count", 0)),
            ],
            "recommended_checks": [
                "Compare error rates before and after the change.",
                "Inspect deployment and configuration diffs.",
                "Review service health and dependency failures.",
                "Check whether rollback or remediation is warranted "
                "using your team's incident procedure.",
            ],
            "limitation": (
                "Priority reflects time proximity and service matching, "
                "not proof of causation. Validate with additional evidence."
            ),
        })

    # Hypothesis 2: Repeated error messages may indicate a shared issue.
    required_columns = {"message", "level", "timestamp", "service"}

    if required_columns.issubset(logs.columns):
        error_mask = (
            logs["level"]
            .fillna("")
            .astype(str)
            .str.upper()
            .isin(["ERROR", "CRITICAL"])
        )

        error_logs = logs.loc[error_mask].copy()

        if not error_logs.empty:
            error_logs["message"] = (
                error_logs["message"].fillna("").astype(str)
            )

            message_counts = error_logs["message"].value_counts()

            for message, count in message_counts.items():
                if count < 3:
                    continue

                matching_logs = error_logs.loc[
                    error_logs["message"] == message
                ].copy()

                matching_logs["timestamp"] = pd.to_datetime(
                    matching_logs["timestamp"],
                    errors="coerce",
                )

                matching_logs["window"] = (
                    matching_logs["timestamp"].dt.floor("min")
                )

                matching_anomaly_windows = sorted({
                    timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    for timestamp in matching_logs["window"].dropna()
                    if timestamp in anomaly_timestamps
                })

                affected_services = sorted(
                    matching_logs["service"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                supporting_records = []

                for _, log in matching_logs.iterrows():
                    timestamp = log["timestamp"]

                    if pd.isna(timestamp):
                        continue

                    window = timestamp.floor("min")

                    supporting_records.append({
                        "timestamp": timestamp.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "service": str(log["service"]),
                        "level": str(log["level"]).upper(),
                        "message": str(log["message"]),
                        "anomaly_window": (
                            window.strftime("%Y-%m-%d %H:%M:%S")
                            if window in anomaly_timestamps
                            else None
                        ),
                    })

                hypotheses.append({
                    "title": "Repeated error pattern detected",
                    "service": ", ".join(affected_services),
                    "confidence": (
                        "Moderate"
                        if matching_anomaly_windows
                        else "Low"
                    ),
                    "priority": (
                        "High"
                        if matching_anomaly_windows
                        else "Medium"
                    ),
                    "evidence": [
                        f"Error message occurred {int(count)} times.",
                        f"Message: {message}",
                        (
                            "Matching anomaly windows: "
                            f"{len(matching_anomaly_windows)}"
                        ),
                        (
                            "Services involved: "
                            + ", ".join(affected_services)
                        ),
                    ],
                    "matching_anomaly_windows": (
                        matching_anomaly_windows
                    ),
                    "supporting_records": supporting_records[:10],
                    "recommended_checks": [
                        "Inspect representative stack traces.",
                        "Check database and downstream service health.",
                        "Compare error timestamps across services.",
                    ],
                    "limitation": (
                        "Repeated errors and overlapping anomalies "
                        "indicate evidence to investigate, not a "
                        "confirmed underlying cause."
                    ),
                })

    # Rank hypotheses by priority, anomaly matches, and evidence.
    priority_order = {"High": 0, "Medium": 1, "Low": 2}

    def get_evidence_score(item):
        anomaly_matches = len(
            item.get("matching_anomaly_windows", [])
        )

        supporting_records_count = len(
            item.get("supporting_records", [])
        )

        evidence_items = len(item.get("evidence", []))

        return (
            priority_order.get(item.get("priority", "Low"), 3),
            -anomaly_matches,
            -supporting_records_count,
            -evidence_items,
        )

    hypotheses.sort(key=get_evidence_score)

    return {
        "anomalies_analyzed": len(
            anomaly_result.get("anomalies", [])
        ),
        "deployment_correlations": (
            correlation_result.get("correlations_found", 0)
        ),
        "hypotheses_generated": len(hypotheses),
        "hypotheses": hypotheses,
        "notice": (
            "These are investigation hypotheses, not confirmed root causes. "
            "Validate them against operational evidence."
        ),
    }
