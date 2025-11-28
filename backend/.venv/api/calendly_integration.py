from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
import uuid
import os

router = APIRouter()

# Simple in-memory schedule for demo (could be replaced with data/doctor_schedule.json)
DOCTOR_SCHEDULE = {
    "working_hours": {"start": "09:00", "end": "17:00"},
    "booked": []  # list of {"date":"YYYY-MM-DD","start":"HH:MM","end":"HH:MM","booking_id": "..."}
}

class AvailabilityQuery(BaseModel):
    date: str
    appointment_type: str

class BookingRequest(BaseModel):
    appointment_type: str
    date: str
    start_time: str
    patient: Dict[str, Any]
    reason: Optional[str] = None

def _parse_time_str(t: str) -> time:
    h, m = map(int, t.split(":"))
    return time(h, m)

def slot_conflicts(date: str, start: str, end: str) -> bool:
    """
    date: 'YYYY-MM-DD'
    start, end: 'HH:MM'
    returns True if any booking on same date overlaps [start, end)
    """
    for b in DOCTOR_SCHEDULE["booked"]:
        if b["date"] != date:
            continue
        # simple string compare by converting to minutes since midnight
        def to_minutes(ts: str) -> int:
            hh, mm = map(int, ts.split(":"))
            return hh * 60 + mm
        s1 = to_minutes(start)
        e1 = to_minutes(end)
        s2 = to_minutes(b["start"])
        e2 = to_minutes(b["end"])
        # overlap if start < existing_end and end > existing_start
        if (s1 < e2) and (e1 > s2):
            return True
    return False

@router.get("/availability")
def availability(date: str, appointment_type: str = "consultation"):
    """
    Returns a JSON structure:
    {
      "date": "YYYY-MM-DD",
      "available_slots": [{"start_time":"09:00","end_time":"09:30","available":True}, ...]
    }
    """
    # durations (mins)
    durations = {"consultation": 30, "followup": 15, "physical": 45, "specialist": 60}
    dur = durations.get(appointment_type, 30)

    # validate date safely
    try:
        d = datetime.fromisoformat(date)
    except Exception:
        # return empty slots when invalid date provided
        return {"date": date, "available_slots": []}

    start_hour = int(DOCTOR_SCHEDULE["working_hours"]["start"].split(":")[0])
    end_hour = int(DOCTOR_SCHEDULE["working_hours"]["end"].split(":")[0])
    slots: List[Dict[str, Any]] = []
    cur = datetime.combine(d.date(), _parse_time_str(DOCTOR_SCHEDULE["working_hours"]["start"]))
    while cur.time() < _parse_time_str(DOCTOR_SCHEDULE["working_hours"]["end"]):
        st = cur.time().strftime("%H:%M")
        edt = (cur + timedelta(minutes=dur)).time().strftime("%H:%M")
        # if computed end is after working hours, stop
        if (datetime.combine(d.date(), _parse_time_str(edt)) > datetime.combine(d.date(), _parse_time_str(DOCTOR_SCHEDULE["working_hours"]["end"]))):
            break
        available = not slot_conflicts(date, st, edt)
        slots.append({"start_time": st, "end_time": edt, "available": available})
        # slide by 15-minute granularity
        cur += timedelta(minutes=15)
    return {"date": date, "available_slots": slots}

def get_availability(date: str, appointment_type: str = "consultation") -> Dict[str, Any]:
    """
    Helper function for other modules (scheduling agent) to call.
    Mirrors the behavior of the /availability route.
    """
    return availability(date=date, appointment_type=appointment_type)

@router.post("/book")
def book(req: BookingRequest):
    """
    Book route that accepts BookingRequest. Computes end time, checks conflicts,
    and appends booking to in-memory schedule.
    """
    # compute end time based on duration
    durations = {"consultation": 30, "followup": 15, "physical": 45, "specialist": 60}
    dur = durations.get(req.appointment_type, 30)
    # validate date
    try:
        st_date = datetime.fromisoformat(req.date).date()
    except Exception:
        return {"status": "failed", "reason": "invalid_date"}

    # compute start and end time
    try:
        h, m = map(int, req.start_time.split(":"))
    except Exception:
        return {"status": "failed", "reason": "invalid_start_time"}
    st_dt = datetime.combine(st_date, time(h, m))
    ed_dt = st_dt + timedelta(minutes=dur)
    st_str = st_dt.time().strftime("%H:%M")
    ed_str = ed_dt.time().strftime("%H:%M")

    if slot_conflicts(req.date, st_str, ed_str):
        return {"status": "failed", "reason": "conflict"}

    booking_id = f"APPT-{uuid.uuid4().hex[:12].upper()}"
    DOCTOR_SCHEDULE["booked"].append({
        "date": req.date,
        "start": st_str,
        "end": ed_str,
        "booking_id": booking_id,
        "patient": req.patient,
        "appointment_type": req.appointment_type,
        "reason": req.reason
    })

    return {
        "booking_id": booking_id,
        "status": "confirmed",
        "confirmation_code": booking_id[-6:],
        "details": {
            "date": req.date,
            "start_time": st_str,
            "end_time": ed_str,
            "patient": req.patient,
            "reason": req.reason
        }
    }

def create_booking(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper for other modules to create a booking. Accepts a dict similar to BookingRequest.
    Returns the same structure as `book`.
    """
    # Validate and coerce into BookingRequest by building model
    try:
        req = BookingRequest(**payload)
    except Exception as e:
        return {"status": "failed", "reason": f"invalid_payload: {e}"}
    return book(req)
