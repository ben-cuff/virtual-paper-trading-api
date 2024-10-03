from fastapi import FastAPI, HTTPException, Depends
from starlette.responses import RedirectResponse
from pydantic import BaseModel
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from passlib.context import CryptContext
from decimal import Decimal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True


class StockRequest(BaseModel):
    stock_symbol: str
    quantity: float
    price_per_share: float


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/")
def read_root():
    return RedirectResponse("https://www.virtualpapertrading.com")


@app.get("/users/{user_id}/")
def get_user(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    user_dict = {
        "id": user.user_id,
        "name": user.name,
        "email": user.email,
        "balance": user.balance,
    }

    return user_dict


@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: db_dependency):
    existing_user = (
        db.query(models.User).filter(models.User.email == user.email).first()
    )

    if existing_user:
        raise HTTPException(status_code=409, detail="409 Conflict: User already exists")

    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(
        name=user.name, email=user.email, hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    user_dict = {
        "id": new_user.user_id,
        "name": new_user.name,
        "email": new_user.email,
        "balance": new_user.balance,
    }
    return user_dict


@app.get("/portfolio/{user_id}/")
def get_portfolio(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    portfolio = (
        db.query(models.Portfolio).filter(models.Portfolio.user_id == user_id).all()
    )
    portfolio_list = [
        {
            "stock_symbol": item.ticker_symbol,
            "shares_owned": float(item.shares_owned),
            "average_price": float(item.average_price),
        }
        for item in portfolio
    ]

    user_dict = {
        "id": user.user_id,
        "name": user.name,
        "email": user.email,
        "balance": user.balance,
    }

    return {"user": user_dict, "portfolio": portfolio_list}


@app.get("/transactions/{user_id}")
def get_transactions(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    transactions = (
        db.query(models.Transaction).filter(models.Transaction.user_id == user_id).all()
    )

    transactions_list = [
        {
            "stock_symbol": item.ticker_symbol,
            "transaction type": item.transaction_type,
            "shares_quantity": float(item.shares_quantity),
            "price": float(item.price),
            "time": item.time,
        }
        for item in transactions
    ]

    user_dict = {
        "id": user.user_id,
        "name": user.name,
        "email": user.email,
        "balance": user.balance,
    }

    return {"user": user_dict, "transactions": transactions_list}


@app.post("/buy/{user_id}/")
def buy_stock(user_id: int, request: StockRequest, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    total_cost = Decimal(request.quantity) * Decimal(request.price_per_share)

    if total_cost > user.balance:
        raise HTTPException(
            status_code=400, detail="400 Bad Request: Insufficient balance"
        )

    user.balance -= total_cost

    portfolio_item = (
        db.query(models.Portfolio)
        .filter(
            models.Portfolio.user_id == user.user_id,
            models.Portfolio.ticker_symbol == request.stock_symbol,
        )
        .first()
    )

    if portfolio_item:
        total_shares = portfolio_item.shares_owned + Decimal(request.quantity)
        total_spent = (
            portfolio_item.shares_owned * portfolio_item.average_price
        ) + total_cost
        portfolio_item.shares_owned = total_shares
        portfolio_item.average_price = total_spent / total_shares
    else:
        portfolio_item = models.Portfolio(
            user_id=user_id,
            ticker_symbol=request.stock_symbol,
            shares_owned=Decimal(request.quantity),
            average_price=Decimal(request.price_per_share),
        )
        db.add(portfolio_item)

    transaction = models.Transaction(
        user_id=user_id,
        ticker_symbol=request.stock_symbol,
        shares_quantity=Decimal(request.quantity),
        price=Decimal(request.price_per_share),
        transaction_type="buy",
    )
    db.add(transaction)

    db.commit()
    db.refresh(user)
    db.refresh(portfolio_item)

    return {
        "user_id": user_id,
        "stock_symbol": request.stock_symbol,
        "quantity": request.quantity,
        "total_cost": float(total_cost),
        "balance": user.balance,
    }


@app.post("/sell/{user_id}")
def sell_stock(user_id: int, request: StockRequest, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    total_return = Decimal(request.quantity) * Decimal(request.price_per_share)

    portfolio_item = (
        db.query(models.Portfolio)
        .filter(
            models.Portfolio.user_id == user.user_id,
            models.Portfolio.ticker_symbol == request.stock_symbol,
        )
        .first()
    )

    if not portfolio_item:
        raise HTTPException(
            status_code=404, detail="404 Not Found: Portfolio item not found"
        )

    if request.quantity > portfolio_item.shares_owned:
        raise HTTPException(
            status_code=400, detail="400 Bad Request: Insufficient shares"
        )

    user.balance += total_return

    portfolio_item.shares_owned -= Decimal(request.quantity)

    if portfolio_item.shares_owned == 0:
        db.delete(portfolio_item)
    else:
        db.add(portfolio_item)

    transaction = models.Transaction(
        user_id=user_id,
        ticker_symbol=request.stock_symbol,
        shares_quantity=Decimal(request.quantity),
        price=Decimal(request.price_per_share),
        transaction_type="sell",
    )
    db.add(transaction)

    db.commit()
    db.refresh(user)

    return {
        "user_id": user_id,
        "stock_symbol": request.stock_symbol,
        "quantity": request.quantity,
        "total_return": float(total_return),
        "balance": user.balance,
    }


@app.delete("/reset/{user_id}")
def reset_user(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    db.query(models.Portfolio).filter(models.Portfolio.user_id == user_id).delete()
    db.query(models.Transaction).filter(models.Transaction.user_id == user_id).delete()

    user.balance = 100000.00
    db.add(user)

    db.commit()
    db.refresh(user)

    return {
        "message": "User reset successfully",
        "user_id": user_id,
        "name": user.name,
        "email": user.email,
    }