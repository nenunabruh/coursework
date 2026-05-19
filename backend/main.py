from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base, Speciality, User
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from jose import jwt

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Приемная комиссия вуза")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки для пропуска (ключ и срок действия)
SECRET_KEY = "ваш-секретный-ключ-для-курсовой"  # в реальном проекте хранить в .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "applicant"
    
# Создание временного пропуска (токена)
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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

@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    # Ищем пользователя с таким email
    user = db.query(User).filter(User.email == email).first()
    
    # Если не нашли или пароль не подходит
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    # Создаём пропуск (токен)
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    return {"access_token": access_token, "token_type": "bearer"}