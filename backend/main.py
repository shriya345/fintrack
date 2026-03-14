from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import io, os

from database import SessionLocal, engine, Base
import models, auth, crud
from parser import parse_csv
from categorizer import categorize_transactions
from anomaly import detect_anomalies
from report import generate_pdf_report

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinTrack API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Auth ────────────────────────────────────────────────────────────────────

@app.post("/auth/signup", tags=["auth"])
def signup(payload: auth.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, payload.email, payload.password)
    token = auth.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/login", tags=["auth"])
def login(payload: auth.UserCreate, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, payload.email)
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


# ── Upload ───────────────────────────────────────────────────────────────────

@app.post("/upload", tags=["transactions"])
def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Upload a bank statement CSV.
    Parses → categorizes → saves transactions → detects anomalies.
    Supports HDFC, ICICI, SBI, Axis Bank formats.
    """
    content = file.file.read().decode("utf-8")
    raw_txns = parse_csv(io.StringIO(content))
    if not raw_txns:
        raise HTTPException(status_code=422, detail="Could not parse CSV — check format")

    categorized = categorize_transactions(raw_txns)
    saved = crud.bulk_insert_transactions(db, categorized, user_id=current_user.id)
    anomalies = detect_anomalies(db, current_user.id)

    return {
        "message": f"Uploaded {len(saved)} transactions",
        "anomalies_flagged": len(anomalies),
        "categories_found": list({t["category"] for t in categorized}),
    }


# ── Transactions ─────────────────────────────────────────────────────────────

@app.get("/transactions", tags=["transactions"])
def get_transactions(
    month: str = None,           # e.g. "2025-02"
    category: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    txns = crud.get_transactions(db, user_id=current_user.id, month=month, category=category)
    return txns


@app.get("/transactions/anomalies", tags=["transactions"])
def get_anomalies(
    month: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return detect_anomalies(db, current_user.id, month=month)


@app.get("/transactions/summary", tags=["transactions"])
def get_summary(
    month: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.get_category_summary(db, user_id=current_user.id, month=month)


# ── Budget Goals ─────────────────────────────────────────────────────────────

@app.get("/budget", tags=["budget"])
def get_budgets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.get_budgets(db, current_user.id)


@app.post("/budget", tags=["budget"])
def set_budget(
    category: str,
    limit: float,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.upsert_budget(db, current_user.id, category, limit)


# ── Report ───────────────────────────────────────────────────────────────────

@app.get("/report/{month}", tags=["report"])
def download_report(
    month: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Generate and return a PDF monthly report for the given month (YYYY-MM).
    """
    summary = crud.get_category_summary(db, user_id=current_user.id, month=month)
    anomalies = detect_anomalies(db, current_user.id, month=month)
    budgets = crud.get_budgets(db, current_user.id)

    pdf_path = generate_pdf_report(
        month=month,
        summary=summary,
        anomalies=anomalies,
        budgets={b.category: b.monthly_limit for b in budgets},
    )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"fintrack_report_{month}.pdf",
    )


# ── Demo mode ────────────────────────────────────────────────────────────────

@app.get("/demo/seed", tags=["demo"])
def seed_demo(db: Session = Depends(get_db)):
    """Loads sample transactions — used for recruiter demos."""
    from demo_data import DEMO_TRANSACTIONS
    demo_user = crud.get_or_create_demo_user(db)
    crud.bulk_insert_transactions(db, DEMO_TRANSACTIONS, user_id=demo_user.id)
    token = auth.create_access_token({"sub": str(demo_user.id)})
    return {"access_token": token, "message": "Demo data loaded — 32 transactions"}
