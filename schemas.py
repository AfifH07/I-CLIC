# schemas.py
from pydantic import BaseModel

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
