# models/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class Patient(BaseModel):
    name: str
    phone: str
    email: EmailStr

class BookingRequest(BaseModel):
    appointment_type: str
    date: str
    start_time: str
    patient: Patient
    reason: Optional[str] = None
