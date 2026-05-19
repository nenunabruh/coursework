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