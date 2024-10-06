from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    balance: float

    class Config:
        orm_mode = True


class LoginResponse(BaseModel):
    message: str
    success: bool
    user: UserResponse

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
        orm_mode = True


class TransactionResponse(BaseModel):
    stock_symbol: str
    transaction_type: str
    shares_quantity: float
    price: float
    time: str

    class Config:
        orm_mode = True


class UserTransactionsResponse(BaseModel):
    user: UserResponse
    transactions: list[TransactionResponse]

    class Config:
        orm_mode = True


class BuyResponse(BaseModel):
    user_id: int
    stock_symbol: str
    quantity: float
    total_cost: float
    balance: float

    class Config:
        orm_mode = True


class SellResponse(BaseModel):
    user_id: int
    stock_symbol: str
    quantity: float
    total_return: float
    balance: float

    class Config:
        orm_mode = True


class ResetResponse(BaseModel):
    message: str
    user_id: int
    name: str
    email: str

    class Config:
        orm_mode = True
