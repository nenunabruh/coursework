# Модель специальности (Speciality)
from sqlalchemy import Column, Integer, String
from database import Base

class Speciality(Base):
    __tablename__ = "specialities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    budget_places = Column(Integer, default=0)
    fee_places = Column(Integer, default=0)
    
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="applicant")  # applicant, commission, admin
    
class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # ID абитуриента
    speciality_id = Column(Integer, nullable=False)  # ID специальности
    exam_russian = Column(Integer)  # балл ЕГЭ русский
    exam_math = Column(Integer)     # балл ЕГЭ математика
    exam_it = Column(Integer)       # балл ЕГЭ информатика
    total_score = Column(Integer)   # сумма баллов
    status = Column(String, default="pending")  # pending, approved, rejected, enrolled
    created_at = Column(String)     # дата подачи
    
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)  # кто сделал
    action = Column(String)    # что сделал (зарегистрировался, подал заявление и т.д.)
    details = Column(String)   # подробности (например, "специальность №5")
    created_at = Column(String)  # когда сделал"# Model for storing university specialities" 
"# Model for users with roles" 
"# Model for applications" 
"# Model for audit logs (GOST requirement)" 
