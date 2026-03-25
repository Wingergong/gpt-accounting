from urllib import request

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import date, datetime, timedelta
import json
from typing import Optional
from pydantic import BaseModel
from pathlib import Path

ssl_args = {
    "ssl": {
        "ca": "/www-gongpingting-top/cacert.pem",
        "cert": "/www-gongpingting-top/Nginx/www.gongpingting.top_chain.pem",
        "key": "/www-gongpingting-top/Nginx/www.gongpingting.top_key.key"
    }
}

# MySQL DatabaseConfiguration
'''DATABASE_URL = "mysql+pymysql://root:mysql1234@localhost:3306/expenses_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)'''

DATABASE_URL = "sqlite:///./expenses.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    amount = Column(Float)
    category = Column(String(50))

class MonthStatic(Base):
    __tablename__ = "monthstatic"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String(7), index=True)  # 格式: 'YYYY-MM'
    category = Column(String(50))
    amount = Column(Float)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# 假设你的静态文件存放在项目的static文件夹内
app.mount("/static", StaticFiles(directory="static"), name="static")

# Enable CORS for all origins (for development purposes)
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

class ExpenseCreate(BaseModel):
    date: date
    amount: float
    category: str

from sqlalchemy import and_

def update_monthstatic(expense_date, category, amt, db):
    month = expense_date.strftime("%Y-%m")
    # 查询是否存在
    record = db.execute(
        text("SELECT id, amount FROM monthstatic WHERE month = :month AND category = :category"),
        {"month": month, "category": category}
    ).fetchone()
    if record:
        # 存在则更新
        db.execute(
            text("UPDATE monthstatic SET amount = amount + :amt WHERE id = :id"),
            {"amt": amt, "id": record[0]}
        )
    else:
        # 不存在则插入
        db.execute(
            text("INSERT INTO monthstatic (month, category, amount) VALUES (:month, :category, :amt)"),
            {"month": month, "category": category, "amt": amt}
        )
    db.commit()

def del_monthstatic(expense_date, category, amt, db):
    month = expense_date.strftime("%Y-%m")
    # 查询是否存在
    record = db.execute(
        text("SELECT id, amount FROM monthstatic WHERE month = :month AND category = :category"),
        {"month": month, "category": category}
    ).fetchone()
    if record:
        new_amount = record[1] - amt
        if new_amount <= 0:
            # 删除记录
            db.execute(
                text("DELETE FROM monthstatic WHERE month = :month AND category = :category"),
                {"month": month, "category": category}
            )
        else:
            # 更新记录
            db.execute(
                text("UPDATE monthstatic SET amount = :new_amount WHERE id = :id"),
                {"id": record[0], "new_amount": new_amount}
            )
        db.commit()

@app.post("/expenses/")
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = Expense(date=expense.date, amount=expense.amount, category=expense.category)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    update_monthstatic(expense.date, expense.category, expense.amount, db)
    return db_expense

@app.get("/expenses")
def read_expenses_date(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Expense)
    if date:
        try:
            query_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Bad date")
        query = query.filter(Expense.date == query_date)
    else:
        query = query.filter(Expense.date <= datetime.today().date())
    expenses = query.all()
    return expenses

@app.get("/monthData")
def get_month_data(
    month: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(MonthStatic)
    if month:
        try:
            query_month = datetime.strptime(month, "%Y-%m").strftime("%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Bad month")
        query = query.filter(MonthStatic.month == query_month)
    '''else:
        query = query.filter(MonthStatic.month <= datetime.today().strftime("%Y-%m"))'''
    month_data = query.all()
    return month_data

@app.get("/")
async def root():
    return FileResponse("expenses.html")

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if db_expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(db_expense)
    db.commit()
    del_monthstatic(db_expense.date, db_expense.category, db_expense.amount, db)
    return {"message": "Expense deleted"}

# Function to import expenses from a JSON file
def import_expenses_from_json(file_path: str, db: Session):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for expense in data.get("expenses", []):
            category = expense["customCategory"] if expense["category"] == "其他" and "customCategory" in expense else expense["category"]
            db_expense = Expense(
                id=int(expense["id"]),
                category=category,
                amount=float(expense["amount"]),
                date=date.fromisoformat(expense["date"]),
            )
            db.add(db_expense)
        db.commit()

from collections import defaultdict
# 假设数据格式：date,category,amount
def monthly_stats(db: Session, month: str):
    # month 格式: '2026-01'
    start_date = datetime.strptime(month, "%Y-%m").date()
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1, day=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1, day=1)
    # 查询本月所有支出
    expenses = db.query(Expense).filter(
        Expense.date >= start_date,
        Expense.date < end_date
    ).all()
    total = sum(e.amount for e in expenses)
    by_category = defaultdict(float)
    for e in expenses:
        by_category[e.category] += e.amount
    # 按金额降序排序
    sorted_by_category = sorted(by_category.items(), key=lambda x: -x[1])
    return {
        "total": total,
        "expenses": sorted_by_category
    }

# Example usage
if __name__ == "__main__":
#    json_file = Path("2025-12-26.json")
#    if json_file.exists():
#        with SessionLocal() as session:
#            import_expenses_from_json(str(json_file), session)
#            print("Expenses imported successfully.")
    import uvicorn
    
    # Get the absolute path to the certificate files
    base_path = Path(__file__).parent
    cert_file = base_path / "www-gongpingting-top/Nginx/www.gongpingting.top_cert_chain.pem"
    key_file = base_path / "www-gongpingting-top/Nginx/www.gongpingting.top_key.key"
    
    # Check if certificate files exist
    if cert_file.exists() and key_file.exists():
        # Run with HTTPS
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            ssl_keyfile=str(key_file),
            ssl_certfile=str(cert_file)
        )
    else:
        print(f"Warning: Certificate files not found at:")
        print(f"  Cert: {cert_file}")
        print(f"  Key: {key_file}")
        print("Running without HTTPS...")
        # Run without HTTPS as fallback
        uvicorn.run(app, host="0.0.0.0", port=8000)
