
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

OUTPUT_FILE = (
    Path(__file__).parent
    / "data"
    / "anomaly_test_logs.csv"
)

services = [
    "api-gateway",
    "payment-service",
    "auth-service",
    "database-service",
    "notification-service",
]

normal_messages = [
    ("INFO", "Request processed successfully"),
    ("INFO", "Health check passed"),
    ("INFO", "Request completed"),
    ("WARNING", "Response time slightly elevated"),
    ("ERROR", "Temporary request failure"),
]

incident_messages = [
    "Database connection timeout",
    "Payment transaction failed",
    "Service dependency unavailable",
]

start_time = datetime(2026, 10, 18, 10, 0, 0)
rows = []

for minute in range(60):
    current_time = start_time + timedelta(minutes=minute)

    # Normal activity: approximately 3 logs per minute.
    for _ in range(3):
        level, message = random.choices(
            normal_messages,
            weights=[45, 25, 15, 10, 5],
            k=1,
        )[0]

        rows.append([
            current_time.strftime("%Y-%m-%d %H:%M:%S"),
            random.choice(services),
            level,
            message,
        ])

    # Inject two known unusual periods.
    if 20 <= minute <= 23:
        error_count = 12
    elif 45 <= minute <= 47:
        error_count = 8
    else:
        error_count = 0

    for _ in range(error_count):
        rows.append([
            current_time.strftime("%Y-%m-%d %H:%M:%S"),
            random.choice(["payment-service", "database-service"]),
            "ERROR",
            random.choice(incident_messages),
        ])

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open(
    "w", newline="", encoding="utf-8"
) as file:
    writer = csv.writer(file)
    writer.writerow([
        "timestamp",
        "service",
        "level",
        "message",
    ])
    writer.writerows(rows)

print("Test dataset created successfully!")
print(f"File: {OUTPUT_FILE}")
print(f"Total log records: {len(rows)}")
print("Injected anomaly windows: minutes 20-23 and 45-47")
