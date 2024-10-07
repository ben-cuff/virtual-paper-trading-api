from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    balance = Column(DECIMAL(12, 3), default=100000.000)

    portfolio = relationship(
        "Portfolio", back_populates="user", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )


class Portfolio(Base):
    __tablename__ = "portfolio"

    portfolio_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"))
    ticker_symbol = Column(String(10))
    shares_owned = Column(DECIMAL(12, 3))
    average_price = Column(DECIMAL(12, 3))
    last_transaction = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="portfolio")


class Transaction(Base):
    __tablename__ = "transaction"

    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"))
    ticker_symbol = Column(String(10))
    transaction_type = Column(String(10))
    shares_quantity = Column(DECIMAL(12, 3))
    price = Column(DECIMAL(12, 3))
    time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="transaction")


class Leaderboard(Base):
    __tablename__ = "leaderboard"

    leaderboard_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"))
    name = Column(String(10))
    total_worth = Column(DECIMAL(12, 3))

    user = relationship("User", back_populates="leaderboard")
