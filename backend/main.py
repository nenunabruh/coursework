from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base, Speciality, User, Application, AuditLog
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Приемная комиссия вуза")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки для пропуска (ключ и срок действия)
SECRET_KEY = "ваш-секретный-ключ-для-курсовой"  # в реальном проекте хранить в .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Настройка проверки пропуска
security = HTTPBearer()

# Функция, которая проверяет пропуск и возвращает user_id и роль
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        role = payload.get("role")
        if user_id is None or role is None:
            raise HTTPException(status_code=401, detail="Неверный пропуск")
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Пропуск недействителен")

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "applicant"
    
class ApplicationCreate(BaseModel):
    speciality_id: int
    exam_russian: int
    exam_math: int
    exam_it: int
    
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
    
    # ЗАПИСЬ В ЖУРНАЛ
    log_action(new_user.id, "register", f"email {new_user.email}", db)
    
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
    
    # ЗАПИСЬ В ЖУРНАЛ
    log_action(user.id, "login", f"email {user.email}", db)
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/applications")
def create_application(
    app_data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # проверяем пропуск
):
    # Считаем сумму баллов
    total = app_data.exam_russian + app_data.exam_math + app_data.exam_it
    
    # Создаём заявление
    new_app = Application(
        user_id=current_user["user_id"],
        speciality_id=app_data.speciality_id,
        exam_russian=app_data.exam_russian,
        exam_math=app_data.exam_math,
        exam_it=app_data.exam_it,
        total_score=total,
        status="pending",
        created_at=str(datetime.now())
    )
    
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    
    # ЗАПИСЬ В ЖУРНАЛ
    log_action(current_user["user_id"], "create_application", f"speciality {app_data.speciality_id}", db)
    
    return {"message": "Заявление подано", "application_id": new_app.id, "total_score": total}

@app.get("/my-applications")
def get_my_applications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    apps = db.query(Application).filter(Application.user_id == current_user["user_id"]).all()
    return apps

@app.get("/all-applications")
def get_all_applications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Только для комиссии и админа
    if current_user["role"] not in ["commission", "admin"]:
        raise HTTPException(status_code=403, detail="Нет прав")
    
    apps = db.query(Application).all()
    return apps

@app.put("/application/{app_id}/status")
def change_status(
    app_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user["role"] not in ["commission", "admin"]:
        raise HTTPException(status_code=403, detail="Нет прав")
    
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Заявление не найдено")
    
    app.status = new_status
    db.commit()
    
    return {"message": f"Статус изменён на {new_status}"}

@app.post("/specialities")
def create_speciality(
    name: str, budget_places: int, fee_places: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user["role"] not in ["commission", "admin"]:
        raise HTTPException(status_code=403, detail="Нет прав")
    
    new_speciality = Speciality(name=name, budget_places=budget_places, fee_places=fee_places)
    
    db.add(new_speciality)
    db.commit()
    db.refresh(new_speciality)
    
    # ЗАПИСЬ В ЖУРНАЛ
    log_action(current_user["user_id"], "create_speciality", f"{name}", db)
    
    return new_speciality

def log_action(user_id: int, action: str, details: str = "", db: Session = None):
    if db:
        log_entry = AuditLog(user_id=user_id, action=action, details=details, created_at=str(datetime.now()))
        db.add(log_entry)
        db.commit()"# Root endpoint returns welcome message" 
"# Get all specialities (public)" 
"# Create speciality (commission only)" 
"# Register new user with hashed password" 
"# Login endpoint returns JWT token" 
"# JWT token creation function" 
"# JWT validation and user extraction" 
"# Security scheme HTTPBearer" 
"# Create application (requires JWT)" 
"# Get user's own applications" 
"# Get all applications (commission only)" 
"# Change application status (commission only)" 
