
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from anomaly_detector import detect_anomalies
from log_analyzer import analyze_logs
from correlation_engine import correlate_events
from root_cause_engine import investigate_root_causes


app = FastAPI(
    title="RootCause AI",
    description="Intelligent production incident investigator",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "sample_logs.csv"
ANOMALY_TEST_FILE = DATA_DIR / "anomaly_test_logs.csv"
EVENTS_FILE = DATA_DIR / "deployment_events.csv"


@app.get("/")
def home():
    return {
        "message": "Welcome to RootCause AI",
        "status": "running",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RootCause AI backend",
    }


@app.get("/api/logs/sample")
def analyze_sample_logs():
    try:
        data = pd.read_csv(DATA_FILE)
        return analyze_logs(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Sample log dataset was not found.",
        ) from exc


@app.post("/api/logs/analyze")
async def analyze_uploaded_logs(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        data = pd.read_csv(BytesIO(content))
        return analyze_logs(data)
    except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="The file must be a valid UTF-8 CSV.",
        ) from exc


@app.get("/api/anomalies/sample")
def detect_sample_anomalies():
    try:
        data = pd.read_csv(DATA_FILE)
        return detect_anomalies(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Sample log dataset was not found.",
        ) from exc


@app.post("/api/anomalies/analyze")
async def detect_uploaded_anomalies(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        data = pd.read_csv(BytesIO(content))
        return detect_anomalies(data)
    except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="The file must be a valid UTF-8 CSV.",
        ) from exc


@app.get("/api/correlation/sample")
def correlate_sample_events():
    if not ANOMALY_TEST_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Anomaly test logs were not found. Generate the test dataset first.",
        )

    if not EVENTS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Deployment events file was not found.",
        )

    try:
        logs = pd.read_csv(ANOMALY_TEST_FILE)
        events = pd.read_csv(EVENTS_FILE)
        return correlate_events(logs, events)
    except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/root-cause/sample")
def investigate_sample_root_cause():
    if not ANOMALY_TEST_FILE.exists() or not EVENTS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Required test logs or deployment events were not found.",
        )

    try:
        logs = pd.read_csv(ANOMALY_TEST_FILE)
        events = pd.read_csv(EVENTS_FILE)
        return investigate_root_causes(logs, events)
    except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def build_investigation(logs: pd.DataFrame, dataset_name: str) -> dict:
    """Run all investigation stages against the same log dataset."""
    if not EVENTS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Deployment events file was not found.",
        )

    events = pd.read_csv(EVENTS_FILE)

    # Run each analysis stage on the same logs.
    analysis_result = analyze_logs(logs)
    anomaly_result = detect_anomalies(logs)
    correlation_result = correlate_events(logs, events)
    root_cause_result = investigate_root_causes(logs, events)

    return {
        "dataset_name": dataset_name,
        "analysis": analysis_result,
        "anomalies": anomaly_result,
        "correlation": correlation_result,
        "root_cause": root_cause_result,
        "notice": (
            "Deployment events come from the saved deployment_events.csv file. "
            "Correlations are evidence for investigation, not proof of causation."
        ),
    }


@app.get("/api/investigation/sample")
def investigate_sample_dataset():
    if not ANOMALY_TEST_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Anomaly test logs were not found. Generate the test dataset first.",
        )

    try:
        logs = pd.read_csv(ANOMALY_TEST_FILE)
        return build_investigation(logs, ANOMALY_TEST_FILE.name)
    except HTTPException:
        raise
    except (
        ValueError,
        KeyError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/investigation/analyze")
async def investigate_uploaded_dataset(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    try:
        logs = pd.read_csv(BytesIO(content))

        return build_investigation(logs, file.filename)

    except HTTPException:
        raise
    except (
        ValueError,
        KeyError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="The file must be a valid UTF-8 CSV.",
        ) from exc

