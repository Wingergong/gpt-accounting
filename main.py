from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
import json
from pathlib import Path

ssl_args = {
    "ssl": {
        "ca": "/static/cacert.pem",
        "cert": "/static/www.gongpingting.top_cert_chain.pem",
        "key": "/static/www.gongpingting.top_key.key"
    }
}

DATABASE_URL = "mysql+pymysql://expense:mysql1234@localhost:3306/expense"

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
    __tablename__ = "monthdata"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String(7), index=True)  # 格式: 'YYYY-MM'
    category = Column(String(50))
    amount = Column(Float)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# 假设你的静态文件存放在项目的static文件夹内
app.mount("/static", StaticFiles(directory="static"), name="static")

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


def update_monthstatic(expense_date, category, amt, db):
    month = expense_date.strftime("%Y-%m")
    # 查询是否存在
    record = db.execute(
        text("SELECT id, amount FROM monthdata WHERE month = :month AND category = :category"),
        {"month": month, "category": category}
    ).fetchone()
    if record:
        # 存在则更新
        db.execute(
            text("UPDATE monthdata SET amount = amount + :amt WHERE id = :id"),
            {"amt": amt, "id": record[0]}
        )
    else:
        # 不存在则插入
        db.execute(
            text("INSERT INTO monthdata (month, category, amount) VALUES (:month, :category, :amt)"),
            {"month": month, "category": category, "amt": amt}
        )
    db.commit()

def del_monthstatic(expense_date, category, amt, db):
    month = expense_date.strftime("%Y-%m")
    # 查询是否存在
    record = db.execute(
        text("SELECT id, amount FROM monthdata WHERE month = :month AND category = :category"),
        {"month": month, "category": category}
    ).fetchone()
    if record:
        new_amount = record[1] - amt
        if new_amount <= 0:
            # 删除记录
            db.execute(
                text("DELETE FROM monthdata WHERE month = :month AND category = :category"),
                {"month": month, "category": category}
            )
        else:
            # 更新记录
            db.execute(
                text("UPDATE monthdata SET amount = :new_amount WHERE id = :id"),
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
    month_data = query.all()
    return month_data

@app.get("/")
async def root():
    return FileResponse("expenses.html")

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if db_expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    del_monthstatic(db_expense.date, db_expense.category, db_expense.amount, db)
    db.delete(db_expense)
    db.commit()
    return {"message": "Expense deleted"}

# Function to import expenses from a JSON file
def import_expenses_from_json(file_path: str, db: Session):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for expense in data.get("expenses", []):
            category = expense["customCategory"] if expense["category"] == "其他" and "customCategory" in expense else \
            expense["category"]
            db_expense = Expense(
                id=int(expense["id"]),
                category=category,
                amount=float(expense["amount"]),
                date=date.fromisoformat(expense["date"]),
            )
            db.add(db_expense)
        db.commit()


# Example usage
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
