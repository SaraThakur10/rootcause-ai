
import pandas as pd


REQUIRED_COLUMNS = ["timestamp", "service", "level", "message"]

VALID_LEVELS = {"INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"}


def analyze_logs(data: pd.DataFrame) -> dict:
    """Validate application logs and produce an incident summary."""

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing_columns)
        )

    logs = data[REQUIRED_COLUMNS].copy()

    # Clean text fields and standardize severity labels.
    for column in ["service", "level", "message"]:
        logs[column] = logs[column].fillna("").astype(str).str.strip()

    logs["level"] = logs["level"].str.upper()

    if (logs[["service", "level", "message"]] == "").any().any():
        raise ValueError(
            "Service, level, and message cannot be empty."
        )

    unknown_levels = sorted(set(logs["level"]) - VALID_LEVELS)

    if unknown_levels:
        raise ValueError(
            "Unsupported log levels: " + ", ".join(unknown_levels)
        )

    # Parse timestamps and reject invalid dates.
    logs["timestamp"] = pd.to_datetime(
        logs["timestamp"], errors="coerce"
    )

    if logs["timestamp"].isna().any():
        raise ValueError("One or more timestamps are invalid.")

    # Sort the logs chronologically.
    logs = logs.sort_values("timestamp").reset_index(drop=True)

    error_logs = logs[logs["level"].isin(["ERROR", "CRITICAL"])]

    # Count logs by severity.
    severity_counts = (
        logs["level"].value_counts().to_dict()
    )

    # Count errors and critical failures by service.
    service_error_counts = (
        error_logs.groupby("service")
        .size()
        .sort_values(ascending=False)
        .to_dict()
    )

    # Find the most frequently repeated error messages.
    top_errors = (
        error_logs.groupby(["message", "service"])
        .size()
        .reset_index(name="count")
        .sort_values(
            ["count", "message"],
            ascending=[False, True]
        )
    )

    top_errors_result = [
        {
            "message": row["message"],
            "service": row["service"],
            "count": int(row["count"]),
        }
        for _, row in top_errors.head(10).iterrows()
    ]

    # Convert timestamps to strings for JSON responses.
    logs["timestamp"] = logs["timestamp"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return {
        "total_logs": int(len(logs)),
        "error_count": int(len(error_logs)),
        "warning_count": int((logs["level"] == "WARNING").sum()),
        "critical_count": int((logs["level"] == "CRITICAL").sum()),
        "severity_counts": {
            key: int(value)
            for key, value in severity_counts.items()
        },
        "service_error_counts": {
            key: int(value)
            for key, value in service_error_counts.items()
        },
        "top_errors": top_errors_result,
        "logs": logs.to_dict(orient="records"),
    }
