# Di main.py
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, DateTime, create_engine
)
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.orm import declarative_base
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os


# Ambil dari environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/db_iclik")

# Jika tidak ada environment variable, pakai default (opsional)
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

# # ---------------------- Models ----------------------
# from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from database import Base

# ---------------------- Models ----------------------

class Symptoms(Base):
    __tablename__ = "symptoms"
    symptom_id = Column(Integer, primary_key=True, index=True)
    symptom_name = Column(String, index=True)
    user_symptoms = relationship("UserSymptoms", back_populates="symptom")


class User(Base):
    __tablename__ = "accounts_user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    umur = Column(Integer, name='umur')
    gender = Column(Integer)

    user_symptoms = relationship("UserSymptoms", back_populates="user")
    predictions = relationship("Prediction", back_populates="user")
    conversations = relationship("ChatConversation", back_populates="user")


class UserSymptoms(Base):
    __tablename__ = "user_symptoms"
    user_symptom_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('accounts_user.id'))  # sudah diarahkan ke accounts_user.id
    symptom_id = Column(Integer, ForeignKey('symptoms.symptom_id'))
    symptom_date = Column(DateTime, default=datetime.utcnow)
    value_symptom = Column(Integer)
    symptom_name = Column(String)

    user = relationship("User", back_populates="user_symptoms")
    symptom = relationship("Symptoms", back_populates="user_symptoms")
    prediction_symptoms = relationship("PredictionSymptoms", back_populates="user_symptom")


class Prediction(Base):
    __tablename__ = "predictions"
    prediction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('accounts_user.id'))  # sudah diarahkan ke accounts_user.id
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
    user_id = Column(Integer, ForeignKey("accounts_user.id"))  # sudah diarahkan ke accounts_user.id
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    message_id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversation.conversation_id"))
    sender = Column(String)
    message = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("ChatConversation", back_populates="messages")



class TemporaryData:
    def __init__(self):
        self.data = pd.DataFrame(columns=[
            'Age', 'gender', 'Heart_Rate_bpm', 'Body_Temperature_C', 
            'Oxygen_Saturation_%', 'Shortness_of_breath', 'Body_ache',
            'Cough', 'Fever', 'Fatigue'
        ])
    
    def add_data(self, user_email: str, extracted: dict):
        if user_email not in self.data.index:
            self.data.loc[user_email] = {col: None for col in self.data.columns}
        
        # Update data dari extracted info
        if 'Age' in extracted:
            self.data.at[user_email, 'Age'] = extracted['Age']
        if 'gender' in extracted:
            self.data.at[user_email, 'gender'] = extracted['gender']
        if 'Hr' in extracted:
            self.data.at[user_email, 'Heart_Rate_bpm'] = extracted['Hr']
        if 'Bt' in extracted:
            self.data.at[user_email, 'Body_Temperature_C'] = extracted['Bt']
        if 'Oxy' in extracted:
            self.data.at[user_email, 'Oxygen_Saturation_%'] = extracted['Oxy']
        
        # Update gejala
        if 'symptoms' in extracted:
            for symptom in extracted['symptoms']:
                symptom_name = symptom['name'].replace(' ', '_')
                if symptom_name in self.data.columns:
                    self.data.at[user_email, symptom_name] = symptom['value']
    
    def is_complete(self, user_email: str) -> bool:
        if user_email not in self.data.index:
            return False
        return not self.data.loc[user_email].isnull().any()


class ChatMessageInput(BaseModel):
    user_email: str
    message: str

    class Config:
        json_schema_extra = {  # Ganti schema_extra dengan json_schema_extra
            "example": {
                "user_email": "user@example.com",
                "message": "Halo, saya tidak enak badan"
            }
        }


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
    return joblib.load("iclik_model_fix.joblib")
    print("Model classes:", model.classes_) 

def make_prediction(model, data):
    if hasattr(model, 'predict') and hasattr(model, 'predict_proba'):
        prediction = model.predict(data)
        confidence = model.predict_proba(data)
        return prediction, confidence
    else:
        raise HTTPException(status_code=500, detail="Model does not support prediction methods.")

# ---------------------- FastAPI App ----------------------
app = FastAPI()

origins = [
    "http://localhost:8000",  # Django
    "http://127.0.0.1:8000",  # Django alternatif
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/predict/")
def predict(data: DataInput, db: Session = Depends(get_db)):
    user_email = data.user.email
    user_data = data.user.dict()
    
    # Ambil data dari TemporaryDataStorage
    from bot_logic import temp_storage
    if user_email not in temp_storage.data.index:
        raise HTTPException(status_code=400, detail="Data belum lengkap untuk prediksi.")
    
    # Ambil semua data vital dan gejala yang sudah diproses
    stored_data = temp_storage.get_user_data(user_email)
    
    # Bangun DataFrame langsung dari TemporaryDataStorage
    base_data = {
        'Age': user_data["age"],
        'Heart_Rate_bpm': stored_data['Heart_Rate_bpm'],
        'Body_Temperature_C': stored_data['Body_Temperature_C'],
        'Oxygen_Saturation_%': stored_data['Oxygen_Saturation_%'],
        'Shortness_of_breath': stored_data.get('Shortness_of_breath', 0),
        'Body_ache': stored_data.get('Body_ache', 0),
        'Cough': stored_data.get('Cough', 0),
        'Fever': stored_data.get('Fever', 0),
        'Fatigue': stored_data.get('Fatigue', 0)
    }
    
    # Buat DataFrame dengan urutan kolom yang benar
    column_order = [
        'Age', 'Heart_Rate_bpm', 'Body_Temperature_C', 'Oxygen_Saturation_%',
        'Shortness_of_breath', 'Body_ache', 'Cough', 'Fever', 'Fatigue'
    ]
    
    df = pd.DataFrame([base_data])[column_order].astype(float)
    
    # Validasi final DataFrame
    missing_cols = set(column_order) - set(df.columns)
    if missing_cols:
        raise HTTPException(status_code=500, detail=f"Kolom {missing_cols} hilang dari DataFrame")
    
    # Lakukan prediksi
    model = load_model()
    prediction, confidence = make_prediction(model, df)
    confidence_score = float(max(confidence[0]))
    
    # Simpan prediksi ke database
    user = db.query(User).filter(User.email == user_data["email"]).first()
    if not user:
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    diagnosis_encoding = {1: 'Healthy', 2: 'Bronchitis', 3: 'Flu', 4: 'Cold', 5: 'Pneumonia'}
    pred_label = diagnosis_encoding.get(prediction[0], "Unknown")
    
    new_pred = Prediction(
        user_id=user.id,
        prediction_name=pred_label,
        confidence_score=confidence_score
    )
    
    db.add(new_pred)
    db.commit()
    db.refresh(new_pred)

    return {
        "prediction": pred_label,
        "confidence_score": confidence_score,
        "data_used": df.to_dict()
    }




@app.post("/chat/")
async def chat(input: ChatMessageInput, db: Session = Depends(get_db)):
    # ... kode yang ada ...
    from bot_logic import HealthcareBot, temp_storage as temp_data
    try:
        bot = HealthcareBot()
        if input.message.lower().startswith("debug:"):
            from groq_api import extract_medical_info
            actual_message = input.message[6:].strip()
            extracted = extract_medical_info(actual_message)
            return {
                "debug": True,
                "message": actual_message,
                "extracted": extracted
            }
        
        response = bot.get_response(input.message, db_session=db, user_email=input.user_email)

        is_standard = bot.is_standard_message(input.message)

        # Cek apakah ini pesan standar
        if not is_standard:
            # Hanya simpan ke database jika BUKAN pesan standar
            user = db.query(User).filter(User.email == input.user_email).first()
            if not user:
                # User tidak ditemukan di DB
                raise Exception("User tidak ditemukan di database!")

            # lanjut buat conversation pakai user.id
            conversation = db.query(ChatConversation).filter(
                ChatConversation.user_id == user.id,
                ChatConversation.ended_at == None
            ).first()

            if not conversation:
                 conversation = ChatConversation(user_id=user.id)
                 db.add(conversation)
                 db.commit()
                 db.refresh(conversation)

            user_msg = ChatMessage(
                conversation_id=conversation.conversation_id,
                sender="user",
                message=input.message,
                sent_at=datetime.now()
            )
            db.add(user_msg)

            # Simpan respon bot
            bot_msg = ChatMessage(
                conversation_id=conversation.conversation_id,
                sender="bot",
                message=response,
                sent_at=datetime.now()
            )
            db.add(bot_msg)
            db.commit()

        return {
            "conversation_id": None if is_standard else conversation.conversation_id,
            "user_message": input.message,
            "bot_response": response,
            "data_status": "standard_message" if is_standard else 
                          ("complete" if temp_data.is_complete(input.user_email) else "incomplete")
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")