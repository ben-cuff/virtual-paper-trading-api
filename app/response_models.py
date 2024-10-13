from pydantic import BaseModel
from typing import Optional


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    balance: float

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    message: str
    success: bool
    user: Optional[UserResponse]

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    stock_symbol: str
    shares_owned: float
    average_price: float


class UserPortfolioResponse(BaseModel):
    user: UserResponse
    portfolio: list[PortfolioResponse]

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    stock_symbol: str
    transaction_type: str
    shares_quantity: float
    price: float
    time: str

    class Config:
        from_attributes = True


class UserTransactionsResponse(BaseModel):
    user: UserResponse
    transactions: list[TransactionResponse]

    class Config:
        from_attributes = True


class BuyResponse(BaseModel):
    user_id: int
    stock_symbol: str
    quantity: float
    total_cost: float
    balance: float

    class Config:
        from_attributes = True


class SellResponse(BaseModel):
    user_id: int
    stock_symbol: str
    quantity: float
    total_return: float
    balance: float

    class Config:
        from_attributes = True


class ResetResponse(BaseModel):
    message: str
    user_id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class LeaderboardAdditionResponse(BaseModel):
    name: str
    total_worth: float


class LeaderboardResponse(BaseModel):
    leaderboard: list[LeaderboardAdditionResponse]
