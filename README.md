# FinTrack — Smart Personal Finance Tracker

A full-stack expense tracking app that automatically categorizes bank transactions, detects spending anomalies, and generates monthly PDF reports.

## Features
- CSV bank statement upload (supports HDFC, ICICI, SBI, Axis formats)
- Auto-categorization engine (80+ keyword rules, 11 categories)
- Anomaly detection (flags transactions 2× above monthly average)
- Interactive dashboard with charts and category breakdowns
- Budget goal setting with visual progress tracking
- PDF monthly report export
- Demo mode with preloaded sample data

## Tech Stack
- **Backend:** Python, FastAPI, SQLAlchemy, Pandas
- **Frontend:** React, Recharts
- **Database:** SQLite
- **Auth:** JWT

## Running Locally
```bash
# Backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 and click "Try Demo Mode".
