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


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True


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
    
    user_dict = {"id": user.user_id, "name": user.name, "email": user.email}

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

    return new_user
