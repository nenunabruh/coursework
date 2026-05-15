# FastAPI приложение для приемной комиссии
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base, Speciality

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Приемная комиссия вуза")

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