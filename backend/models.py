# Модель специальности (Speciality)
from sqlalchemy import Column, Integer, String
from database import Base

class Speciality(Base):
    __tablename__ = "specialities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    budget_places = Column(Integer, default=0)
    fee_places = Column(Integer, default=0)