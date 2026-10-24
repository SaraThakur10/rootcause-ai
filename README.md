# RootCause AI — Intelligent Production Incident Investigator

RootCause AI is a full-stack application designed to analyze application logs, identify unusual activity, correlate deployment events, and generate evidence-based root-cause hypotheses to support production incident investigation.

**Live Demo:** [Open RootCause AI](https://rootcause-i2n54neiq-sarathakur10s-projects.vercel.app)  
**API Documentation:** [Explore the REST API](https://rootcause-ai-qqd9.onrender.com/docs)  
**Backend Health:** [Check API Status](https://rootcause-ai-qqd9.onrender.com/api/health)

## Overview

Troubleshooting production incidents can involve reviewing large volumes of application logs and identifying patterns across services and deployment events. RootCause AI brings several investigation capabilities into a single dashboard to help developers examine errors, detect anomalies, and explore potential causes of incidents.

## Key Features

- **Log Analysis:** Upload CSV application logs and review log statistics, error counts, warnings, and common error messages.
- **Anomaly Detection:** Analyze unusual patterns in application activity using statistical techniques and an Isolation Forest model.
- **Deployment Correlation:** Examine relationships between application activity and deployment events.
- **Root-Cause Hypotheses:** Present potential causes, supporting evidence, and recommended investigation checks.
- **Interactive Dashboard:** View summary metrics and service-level error visualizations.
- **CSV Upload:** Upload structured log data for analysis.
- **Search and Filtering:** Find relevant log entries through dashboard search and filtering.
- **REST API:** Access backend functionality through FastAPI endpoints.
- **Deployment:** Frontend hosted on Vercel and backend hosted on Render.

## Technology Stack

**Frontend**
- React
- TypeScript
- Vite
- CSS

**Backend**
- Python
- FastAPI
- Pandas
- Scikit-learn

**Machine Learning and Data Analysis**
- Isolation Forest for anomaly detection
- Statistical analysis of log activity
- Event correlation and root-cause investigation logic

**Deployment and Tools**
- Git and GitHub
- Vercel
- Render

## System Architecture

1. The user uploads a CSV file through the React dashboard.
2. The frontend sends the file to the FastAPI backend.
3. The backend processes the log data using Python and Pandas.
4. The analysis modules generate log summaries and investigation results.
5. The frontend displays the returned data through dashboard metrics, charts, and investigation panels.

## CSV Input Format

The application expects log CSV files with the following columns:

| Column | Description |
|---|---|
| `timestamp` | Date and time of the log event |
| `service` | Application service associated with the event |
| `level` | Log severity, such as INFO, WARNING, or ERROR |
| `message` | Log message or event description |

Use a CSV file containing these required columns when testing the log-analysis upload feature.

## Project Structure

```text
rootcause-ai/
├── backend/
│   ├── main.py
│   ├── log_analyzer.py
│   ├── anomaly_detector.py
│   ├── correlation_engine.py
│   ├── root_cause_engine.py
│   ├── requirements.txt
│   └── data/
│       ├── sample_logs.csv
│       ├── anomaly_test_logs.csv
│       └── deployment_events.csv
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   └── ...
├── .gitignore
└── README.md
```

## Run Locally

### Prerequisites

- Python
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/SaraThakur10/rootcause-ai.git
cd rootcause-ai
```

### 2. Set up the backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
python -m uvicorn main:app --reload --port 8000
```

Backend API: `http://127.0.0.1:8000`  
Interactive API documentation: `http://127.0.0.1:8000/docs`

### 3. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
```

Start the development server:

```bash
npm run dev
```

Open the local URL displayed by Vite, usually `http://localhost:5173`.

For local development, configure the frontend to use `http://127.0.0.1:8000` as the backend URL and allow the frontend origin in the backend CORS configuration.

## API Endpoints

The backend exposes endpoints for health checks, log analysis, anomaly detection, deployment correlation, and root-cause investigation.

Visit the interactive API documentation for the current endpoint list, request formats, and responses:

[RootCause AI API Docs](https://rootcause-ai-qqd9.onrender.com/docs)

## Current Status

- Frontend and backend deployed.
- Dashboard refresh and CSV upload tested successfully.
- Log statistics, charts, and search/filter functionality tested.
- Anomaly detection, deployment correlation, and root-cause investigation panels tested.

## Future Improvements

- Integrate investigation results directly with uploaded log datasets.
- Add persistent incident history and investigation reports.
- Support integrations with monitoring and observability platforms.
- Improve root-cause ranking and model evaluation using labeled incident datasets.
- Add automated tests and expanded error-handling coverage.

## Author

**Sara Amit Thakur**

GitHub: [SaraThakur10](https://github.com/SaraThakur10)

---

*RootCause AI — Turning application logs into actionable incident insights.*
