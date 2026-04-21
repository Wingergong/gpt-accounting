from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
import json
import os

from expense_logic import build_month_summary, format_amount, normalize_amount, normalize_category

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'expenses.db'}")
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",") if origin.strip()]

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50))


Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExpenseCreate(BaseModel):
    date: date
    amount: Decimal
    category: str


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    amount: Decimal
    category: str


class MonthSummaryResponse(BaseModel):
    month: str
    category: str
    amount: Decimal


class ExpenseApiResponse(BaseModel):
    id: int
    date: date
    amount: str
    category: str


class MonthSummaryApiResponse(BaseModel):
    month: str
    category: str
    amount: str



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def serialize_expense(expense: Expense) -> ExpenseApiResponse:
    validated = ExpenseResponse.model_validate(expense)
    return ExpenseApiResponse(
        id=validated.id,
        date=validated.date,
        amount=format_amount(validated.amount),
        category=validated.category,
    )



def serialize_month_summary(db: Session) -> list[MonthSummaryApiResponse]:
    expenses = db.query(Expense).all()
    normalized_expenses = [
        {"date": expense.date, "category": expense.category, "amount": expense.amount}
        for expense in expenses
    ]
    summary = build_month_summary(normalized_expenses)
    return [
        MonthSummaryApiResponse(
            month=item["month"],
            category=item["category"],
            amount=format_amount(item["amount"]),
        )
        for item in summary
    ]


@app.post("/expenses/", response_model=ExpenseApiResponse)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = Expense(
        date=expense.date,
        amount=normalize_amount(expense.amount),
        category=expense.category,
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return serialize_expense(db_expense)


@app.get("/expenses", response_model=list[ExpenseApiResponse])
def read_expenses_date(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Expense)
    if date:
        try:
            query_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Bad date") from exc
        query = query.filter(Expense.date == query_date)
    else:
        query = query.filter(Expense.date <= datetime.today().date())
    expenses = query.all()
    return [serialize_expense(expense) for expense in expenses]


@app.get("/monthData", response_model=list[MonthSummaryApiResponse])
def get_month_data(
    month: Optional[str] = None,
    db: Session = Depends(get_db)
):
    summary = serialize_month_summary(db)
    if month:
        try:
            query_month = datetime.strptime(month, "%Y-%m").strftime("%Y-%m")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Bad month") from exc
        return [item for item in summary if item.month == query_month]
    return summary


@app.get("/")
async def root():
    return FileResponse(str(BASE_DIR / "expenses.html"))


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if db_expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(db_expense)
    db.commit()
    return {"message": "Expense deleted"}


# Function to import expenses from a JSON file
def import_expenses_from_json(file_path: str, db: Session):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for expense in data.get("expenses", []):
            category = normalize_category(expense)
            db_expense = Expense(
                id=int(expense["id"]),
                category=category,
                amount=normalize_amount(expense["amount"]),
                date=date.fromisoformat(expense["date"]),
            )
            db.add(db_expense)
        db.commit()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
