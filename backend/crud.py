from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Dict, Any, Optional

import models, auth


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, email: str, password: str) -> models.User:
    user = models.User(email=email, hashed_password=auth.hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_demo_user(db: Session) -> models.User:
    user = get_user_by_email(db, "demo@fintrack.app")
    if not user:
        user = create_user(db, "demo@fintrack.app", "demo1234")
    else:
        # Wipe existing demo transactions for clean re-seed
        db.query(models.Transaction).filter(models.Transaction.user_id == user.id).delete()
        db.commit()
    return user


def bulk_insert_transactions(
    db: Session,
    transactions: List[Dict[str, Any]],
    user_id: int,
) -> List[models.Transaction]:
    objs = []
    for t in transactions:
        txn = models.Transaction(
            user_id=user_id,
            date=t["date"],
            description=t["description"],
            category=t["category"],
            amount=t["amount"],
        )
        db.add(txn)
        objs.append(txn)
    db.commit()
    return objs


def get_transactions(
    db: Session,
    user_id: int,
    month: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = db.query(models.Transaction).filter(models.Transaction.user_id == user_id)
    if month:
        q = q.filter(func.strftime("%Y-%m", models.Transaction.date) == month)
    if category:
        q = q.filter(models.Transaction.category == category)
    txns = q.order_by(models.Transaction.date.desc()).all()
    return [
        {
            "id": t.id,
            "date": str(t.date),
            "description": t.description,
            "category": t.category,
            "amount": t.amount,
            "is_anomaly": bool(t.is_anomaly),
        }
        for t in txns
    ]


def get_category_summary(
    db: Session,
    user_id: int,
    month: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = (
        db.query(
            models.Transaction.category,
            func.sum(models.Transaction.amount).label("total"),
            func.count(models.Transaction.id).label("count"),
        )
        .filter(models.Transaction.user_id == user_id)
    )
    if month:
        q = q.filter(func.strftime("%Y-%m", models.Transaction.date) == month)
    rows = q.group_by(models.Transaction.category).order_by(func.sum(models.Transaction.amount).desc()).all()
    return [{"category": r.category, "total": round(r.total, 2), "count": r.count} for r in rows]


def get_budgets(db: Session, user_id: int) -> List[models.Budget]:
    return db.query(models.Budget).filter(models.Budget.user_id == user_id).all()


def upsert_budget(db: Session, user_id: int, category: str, limit: float) -> models.Budget:
    budget = (
        db.query(models.Budget)
        .filter(models.Budget.user_id == user_id, models.Budget.category == category)
        .first()
    )
    if budget:
        budget.monthly_limit = limit
    else:
        budget = models.Budget(user_id=user_id, category=category, monthly_limit=limit)
        db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget
