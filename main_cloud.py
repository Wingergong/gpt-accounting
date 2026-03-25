from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import date
import json
from pathlib import Path

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

@app.post("/expenses/")
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = Expense(date=expense.date, amount=expense.amount, category=expense.category)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/expenses/")
def read_expenses(db: Session = Depends(get_db)):
    expenses = db.query(Expense).all()
    return expenses

@app.get("/")
async def root():
    return FileResponse("expenses_1.html")

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
            category = expense["customCategory"] if expense["category"] == "其他" and "customCategory" in expense else expense["category"]
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
#    json_file = Path("2025-12-26.json")
#    if json_file.exists():
#        with SessionLocal() as session:
#            import_expenses_from_json(str(json_file), session)
#            print("Expenses imported successfully.")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
