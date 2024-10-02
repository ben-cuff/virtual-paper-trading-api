from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Portfolio(Base):
    __tablename__ = "portfolio"

    portfolio_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"))
    ticker_symbol = Column(String(10))
    shares_owned = Column(DECIMAL(10, 2))
    average_price = Column(DECIMAL(10, 2))
    last_transaction = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="portfolio")


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
