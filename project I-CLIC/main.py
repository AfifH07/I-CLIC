# main.py
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, DateTime, create_engine
)
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.orm import declarative_base
from datetime import datetime


# ---------------------- Database Setup ----------------------
DATABASE_URL = "postgresql://postgres:postgres@localhost/db_iclik"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency untuk session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------- Models ----------------------
class Symptoms(Base):
    __tablename__ = "symptoms"
    symptom_id = Column(Integer, primary_key=True, index=True)
    symptom_name = Column(String, index=True)
    user_symptoms = relationship("UserSymptoms", back_populates="symptom")

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    age = Column(Integer)
    gender = Column(Integer)
    user_symptoms = relationship("UserSymptoms", back_populates="user")
    predictions = relationship("Prediction", back_populates="user")

class UserSymptoms(Base):
    __tablename__ = "user_symptoms"
    user_symptom_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    symptom_id = Column(Integer, ForeignKey('symptoms.symptom_id'))
    symptom_date = Column(DateTime, default=datetime.utcnow)
    value_symptom = Column(Integer)

    user = relationship("User", back_populates="user_symptoms")
    symptom = relationship("Symptoms", back_populates="user_symptoms")
    prediction_symptoms = relationship("PredictionSymptoms", back_populates="user_symptom")

class Prediction(Base):
    __tablename__ = "predictions"
    prediction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    prediction_name = Column(String)
    confidence_score = Column(Float)
    predicted_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")
    prediction_symptoms = relationship("PredictionSymptoms", back_populates="prediction")

class PredictionSymptoms(Base):
    __tablename__ = "prediction_symptoms"
    prediction_symptom_id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey('predictions.prediction_id'))
    symptom_id = Column(Integer, ForeignKey('user_symptoms.user_symptom_id'))

    prediction = relationship("Prediction", back_populates="prediction_symptoms")
    user_symptom = relationship("UserSymptoms", back_populates="prediction_symptoms")

class ChatConversation(Base):
    __tablename__ = "chat_conversation"
    conversation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="conversation")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    message_id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversation.conversation_id"))
    sender = Column(String)
    message = Column(String)
    send_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("ChatConversation", back_populates="messages")


Base.metadata.create_all(bind=engine)

# ---------------------- Pydantic Schemas ----------------------
class Symptom(BaseModel):
    symptom_id: int
    value_symptom: int

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    age: int
    gender: int

class DataInput(BaseModel):
    user: UserCreate
    symptoms: list[Symptom]

class ChatMessageInput(BaseModel):
    user_email: str
    message: str

# ---------------------- Model Utilities ----------------------
def load_model():
    return joblib.load("iclic-model.pkl")

def make_prediction(model, data):
    if hasattr(model, 'predict') and hasattr(model, 'predict_proba'):
        prediction = model.predict(data)
        confidence = model.predict_proba(data)
        return prediction, confidence
    else:
        raise HTTPException(status_code=500, detail="Model does not support prediction methods.")

# ---------------------- FastAPI App ----------------------
app = FastAPI()

@app.post("/predict/")
def predict(data: DataInput, db: Session = Depends(get_db)):
    user_data = data.user.dict()
    symptoms_data = [s.dict() for s in data.symptoms]

    # Cek user atau buat baru
    user = db.query(User).filter(User.email == user_data["email"]).first()
    if not user:
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Simpan gejala
    user_symptom_objs = []
    for s in symptoms_data:
        us = UserSymptoms(user_id=user.user_id, symptom_id=s["symptom_id"], value_symptom=s["value_symptom"])
        db.add(us)
        db.flush()  # Flush untuk dapatkan ID tanpa commit
        user_symptom_objs.append(us)

    db.commit()

    # Mapping nama kolom dari symptom_id
    symptom_ids = [s["symptom_id"] for s in symptoms_data]
    values = [s["value_symptom"] for s in symptoms_data]
    symptoms = db.query(Symptoms).filter(Symptoms.symptom_id.in_(symptom_ids)).all()
    name_map = {s.symptom_id: s.symptom_name for s in symptoms}
    columns = [name_map.get(sid, f"Unknown_{sid}") for sid in symptom_ids]

    df = pd.DataFrame([values], columns=columns)
    df["Age"] = user_data["age"]
    df["Gender"] = user_data["gender"]

    column_order = [
        'Age', 'Gender', 'Heart_Rate_bpm', 'Body_Temperature_C', 'Oxygen_Saturation_%',
        'Systolic', 'Diastolic', 'Runny nose', 'Shortness of breath',
        'Body ache', 'Headache', 'Cough', 'Fever', 'Sore throat', 'Fatigue'
    ]
    for col in column_order:
        if col not in df.columns:
            df[col] = 0
    df = df[column_order].astype(float)

    model = load_model()
    prediction, confidence = make_prediction(model, df)
    confidence_score = float(max(confidence[0]))

    diagnosis_encoding = {1: 'Healthy', 2: 'Bronchitis', 3: 'Flu', 4: 'Cold', 5: 'Pneumonia'}
    pred_label = diagnosis_encoding.get(prediction[0], "Unknown")

    # Simpan prediksi
    new_pred = Prediction(user_id=user.user_id, prediction_name=pred_label, confidence_score=confidence_score)
    db.add(new_pred)
    db.commit()
    db.refresh(new_pred)

    for us in user_symptom_objs:
        db.add(PredictionSymptoms(prediction_id=new_pred.prediction_id, symptom_id=us.user_symptom_id))
    db.commit()

    return {"prediction": pred_label, "confidence_score": confidence_score}

@app.post("/chat/")
def chat(input: ChatMessageInput, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == input.user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        conversation = db.query(ChatConversation).filter(
            ChatConversation.user_id == user.user_id,
            ChatConversation.ended_at == None
        ).first()

        if not conversation:
            conversation = ChatConversation(user_id=user.user_id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        user_msg = ChatMessage(
            conversation_id=conversation.conversation_id,
            sender="user",
            message=input.message
        )
        db.add(user_msg)

        bot_reply = f"Halo! Kamu bilang: {input.message}"
        bot_msg = ChatMessage(
            conversation_id=conversation.conversation_id,
            sender="bot",
            message=bot_reply
        )
        db.add(bot_msg)

        db.commit()

        return {
            "conversation_id": conversation.conversation_id,
            "user_message": input.message,
            "bot_response": bot_reply
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")
