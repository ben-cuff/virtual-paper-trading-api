from fastapi import FastAPI, HTTPException, Depends, Header
from starlette.responses import RedirectResponse
from pydantic import BaseModel
import app.models as models
from app.database import engine, SessionLocal
import app.response_models as response_models
from sqlalchemy.orm import Session
from typing import Annotated
from passlib.context import CryptContext
from decimal import Decimal
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware


load_dotenv(dotenv_path=".env.local")

API_KEY = os.getenv("X_API_KEY")
DEV_MODE = os.getenv("DEV_MODE").lower() == "true"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


models.Base.metadata.create_all(bind=engine)


class UserCreateRequest(BaseModel):
    name: str
    email: str
    password: str


class StockRequest(BaseModel):
    stock_symbol: str
    quantity: float
    price_per_share: float


class LoginRequest(BaseModel):
    email: str
    password: str


class LeaderboardRequest(BaseModel):
    total_worth: float


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def verify_api_key(x_api_key: str = Header(None)):
    if DEV_MODE:
        return
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")


api_key_dependency = Depends(verify_api_key)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get(
    "/users/{user_id}/",
    response_model=response_models.UserResponse,
    dependencies=[api_key_dependency],
)
def get_user(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    user_dict = response_models.UserResponse(
        id=user.user_id,
        name=user.name,
        email=user.email,
        balance=user.balance,
    )

    return user_dict


@app.post(
    "/users/",
    response_model=response_models.UserResponse,
    dependencies=[api_key_dependency],
)
def create_user(user: UserCreateRequest, db: db_dependency):
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

    user_dict = response_models.UserResponse(
        id=new_user.user_id,
        name=new_user.name,
        email=new_user.email,
        balance=new_user.balance,
    )

    return user_dict


@app.post(
    "/login/",
    response_model=response_models.LoginResponse,
    dependencies=[api_key_dependency],
)
def login(userAttempt: LoginRequest, db: db_dependency):
    user = db.query(models.User).filter(models.User.email == userAttempt.email).first()
    if not user:
        return response_models.LoginResponse(
            message="Email or password incorrect", success=False
        )

    if not pwd_context.verify(userAttempt.password, user.hashed_password):
        return response_models.LoginResponse(
            message="Email or password incorrect", success=False
        )

    user_dict = response_models.UserResponse(
        id=user.user_id,
        name=user.name,
        email=user.email,
        balance=user.balance,
    )

    return response_models.LoginResponse(
        message="User successfully logged in", success=True, user=user_dict
    )


@app.get(
    "/portfolio/{user_id}/",
    response_model=response_models.UserPortfolioResponse,
    dependencies=[api_key_dependency],
)
def get_portfolio(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    portfolio = (
        db.query(models.Portfolio).filter(models.Portfolio.user_id == user_id).all()
    )

    portfolio_list = [
        response_models.PortfolioResponse(
            stock_symbol=item.ticker_symbol,
            shares_owned=float(item.shares_owned),
            average_price=float(item.average_price),
        )
        for item in portfolio
    ]

    user_dict = response_models.UserResponse(
        id=user.user_id, name=user.name, email=user.email, balance=user.balance
    )

    return response_models.UserPortfolioResponse(
        user=user_dict, portfolio=portfolio_list
    )


@app.get(
    "/transactions/{user_id}",
    response_model=response_models.UserTransactionsResponse,
    dependencies=[api_key_dependency],
)
def get_transactions(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    transactions = (
        db.query(models.Transaction).filter(models.Transaction.user_id == user_id).all()
    )

    transactions_list = [
        response_models.TransactionResponse(
            stock_symbol=item.ticker_symbol,
            transaction_type=item.transaction_type,
            shares_quantity=float(item.shares_owned),
            price=float(item.price),
            time=item.time,
        )
        for item in transactions
    ]

    user_dict = response_models.UserResponse(
        id=user.user_id, name=user.name, email=user.email, balance=user.balance
    )

    return response_models.UserTransactionsResponse(
        user=user_dict, transactions=transactions_list
    )


@app.post(
    "/buy/{user_id}/",
    response_model=response_models.BuyResponse,
    dependencies=[api_key_dependency],
)
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
            ticker_symbol=request.stock_symbol.upper(),
            shares_owned=Decimal(request.quantity),
            average_price=Decimal(request.price_per_share),
        )
        db.add(portfolio_item)

    transaction = models.Transaction(
        user_id=user_id,
        ticker_symbol=request.stock_symbol.upper(),
        shares_quantity=Decimal(request.quantity),
        price=Decimal(request.price_per_share),
        transaction_type="buy",
    )
    db.add(transaction)

    db.commit()
    db.refresh(user)
    db.refresh(portfolio_item)

    return response_models.BuyResponse(
        user_id=user_id,
        stock_symbol=request.stock_symbol.upper(),
        quantity=request.quantity,
        total_cost=float(total_cost),
        balance=user.balance,
    )


@app.post(
    "/sell/{user_id}",
    response_model=response_models.SellResponse,
    dependencies=[api_key_dependency],
)
def sell_stock(user_id: int, request: StockRequest, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    total_return = Decimal(request.quantity) * Decimal(request.price_per_share)

    portfolio_item = (
        db.query(models.Portfolio)
        .filter(
            models.Portfolio.user_id == user.user_id,
            models.Portfolio.ticker_symbol == request.stock_symbol.upper(),
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
        ticker_symbol=request.stock_symbol.upper(),
        shares_quantity=Decimal(request.quantity),
        price=Decimal(request.price_per_share),
        transaction_type="sell",
    )
    db.add(transaction)

    db.commit()
    db.refresh(user)

    return response_models.SellResponse(
        user_id=user_id,
        stock_symbol=request.stock_symbol.upper(),
        quantity=request.quantity,
        total_return=float(total_return),
        balance=user.balance,
    )


@app.delete(
    "/reset/{user_id}",
    response_model=response_models.ResetResponse,
    dependencies=[api_key_dependency],
)
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

    return response_models.ResetResponse(
        message="User reset successfully",
        user_id=user_id,
        name=user.name,
        email=user.email,
    )


@app.get(
    "/leaderboard",
    response_model=response_models.LeaderboardResponse,
    dependencies=[api_key_dependency],
)
def get_leaderBoard(db: db_dependency):
    leaderboard_entries = (
        db.query(models.Leaderboard)
        .order_by(models.Leaderboard.total_worth.desc())
        .all()
    )

    leaderboard_list = [
        response_models.LeaderboardAdditionResponse(
            name=item.name, total_worth=item.total_worth
        )
        for item in leaderboard_entries
    ]

    return response_models.LeaderboardResponse(leaderboard=leaderboard_list)


@app.post(
    "/leaderboard/{user_id}",
    response_model=response_models.LeaderboardAdditionResponse,
    dependencies=[api_key_dependency],
)
def update_leaderboard(user_id: int, request: LeaderboardRequest, db: db_dependency):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="404 Not Found: User not found")

    user_leaderboard = (
        db.query(models.Leaderboard)
        .filter(models.Leaderboard.user_id == user_id)
        .first()
    )

    if user_leaderboard:
        user_leaderboard.total_worth = request.total_worth

        db.commit()
        db.refresh(user_leaderboard)

        return response_models.LeaderboardAdditionResponse(
            name=user.name, total_worth=user_leaderboard.total_worth
        )
    else:
        new_leaderboard = models.Leaderboard(
            user_id=user_id, name=user.name, total_worth=request.total_worth
        )

        db.add(new_leaderboard)
        db.commit()
        db.refresh(new_leaderboard)

        return response_models.LeaderboardAdditionResponse(
            name=user.name, total_worth=new_leaderboard.total_worth
        )
