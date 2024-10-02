from fastapi import FastAPI, HTTPException, Depends
from starlette.responses import RedirectResponse
from pydantic import BaseModel
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


app = FastAPI()

models.Base.metadata.create_all(bind=engine)


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


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


@app.post("/users/")
def create_user(user: UserCreate, db: db_dependency):
    existing_user = (
        db.query(models.User).filter(models.User.email == user.email).first()
    )

    if existing_user:
        raise HTTPException(status_code=404, detail="user already exists")
    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(
        name=user.name, email=user.email, hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
