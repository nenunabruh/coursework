from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base, Speciality
from passlib.context import CryptContext
from pydantic import BaseModel

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Приемная комиссия вуза")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "applicant"

@app.get("/")
def root():
    return {"message": "Система приемной комиссии работает"}

@app.get("/specialities")
def get_specialities(db: Session = Depends(get_db)):
    specialities = db.query(Speciality).all()
    return specialities

@app.post("/specialities")
def create_speciality(name: str, budget_places: int, fee_places: int, db: Session = Depends(get_db)):
    new_speciality = Speciality(
        name=name, 
        budget_places=budget_places, 
        fee_places=fee_places
    )
    db.add(new_speciality)
    db.commit()
    db.refresh(new_speciality)
    return new_speciality

@app.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Проверяем, существует ли пользователь с таким email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Хешируем пароль
    hashed_password = pwd_context.hash(user_data.password)
    
    # Создаём нового пользователя
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "user_id": new_user.id}