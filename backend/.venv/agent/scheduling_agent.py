# agent/scheduling_agent.py
import uuid
import re
import datetime
from typing import Dict, Any, Optional, List
from rag.faq_rag import FAQRAG

# import calendly helpers (unchanged)
from api.calendly_integration import get_availability, create_booking

# Simple session store (in-memory)
SESSIONS: Dict[str, Dict] = {}

TIME_RE = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

def classify_intent(message: str) -> str:
    """
    Very small rule-based intent classifier.
    Returns one of:
      - "book_appointment"
      - "ask_hours"
      - "ask_insurance"
      - "ask_phone"
      - "small_talk"
      - "unknown" (fallback to FAQ)
    """
    m = message.lower().strip()
    # greetings
    if any(g in m for g in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]):
        # If message is only greeting, return small_talk
        if len(m.split()) <= 2:
            return "small_talk"

    # booking keywords
    if any(k in m for k in ["book", "appointment", "schedule", "see the doctor", "i need to see", "i want to book", "reserve"]):
        return "book_appointment"

    # time or date alone could indicate booking continuation
    if TIME_RE.search(m) or ISO_DATE_RE.search(m):
        # Likely a booking flow message (time/date selection), but not forcing booking start
        return "maybe_time_or_date"

    # hours / open
    if any(k in m for k in ["hour", "open", "opening", "when open", "hours"]):
        return "ask_hours"

    # insurance
    if any(k in m for k in ["insurance", "insurer", "coverage", "copay", "billing"]):
        return "ask_insurance"

    # phone/contact
    if any(k in m for k in ["phone", "call", "contact", "number", "clinic phone"]):
        return "ask_phone"

    # ask location / address
    if any(k in m for k in ["address", "location", "where are you", "directions"]):
        return "ask_location"

    # fallback to unknown -> use RAG/FAQ
    return "unknown"

def parse_time(text: str) -> Optional[str]:
    """Return HH:MM if found, else None"""
    m = TIME_RE.search(text)
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2))
    return f"{hh:02d}:{mm:02d}"

def parse_date(text: str) -> Optional[str]:
    """Return ISO date if found and valid"""
    m = ISO_DATE_RE.search(text)
    if not m:
        return None
    try:
        datetime.date.fromisoformat(m.group(1))
        return m.group(1)
    except Exception:
        return None

class SchedulingAgent:
    def __init__(self):
        self.rag = FAQRAG()

    def new_session(self):
        sid = uuid.uuid4().hex
        SESSIONS[sid] = {"state": "idle", "context": {}, "messages": []}
        return sid

    def _ensure_session(self, session_id: Optional[str]) -> str:
        if not session_id:
            session_id = self.new_session()
        if session_id not in SESSIONS:
            SESSIONS[session_id] = {"state": "idle", "context": {}, "messages": []}
        return session_id

    def handle_message(self, session_id: Optional[str], message: str):
        # ensure session
        session_id = self._ensure_session(session_id)
        sess = SESSIONS[session_id]

        # record incoming message
        sess.setdefault("messages", []).append({"from": "user", "text": message, "ts": datetime.datetime.utcnow().isoformat()})

        msg = message.strip()
        lower = msg.lower()

        # quick parse for time/date/patient-csv to allow "out of order" inputs
        time_val = parse_time(msg)
        date_val = parse_date(msg)

        # Recognize CSV-like patient info: "Name, phone, email"
        parts = [p.strip() for p in msg.split(",")]
        looks_like_patient = False
        if len(parts) >= 3:
            # basic email check for last part
            if "@" in parts[-1] and len(parts[0].split()) >= 1:
                looks_like_patient = True

        # classify intent (rule-based)
        intent = classify_intent(msg)

        # ---------- If we're mid-booking state, prefer that flow ----------
        state = sess.get("state", "idle")
        ctx = sess.setdefault("context", {})

        # If currently in flow where we expect date/time/etc, continue that
        if state == "booking_needs" and ctx.get("asked_type"):
            # user should answer appointment type
            appt_type = "consultation"
            if "follow" in lower: appt_type = "followup"
            if "physical" in lower: appt_type = "physical"
            if "special" in lower: appt_type = "specialist"
            ctx["appointment_type"] = appt_type
            ctx["asked_type"] = False
            ctx["asked_pref"] = True
            sess["state"] = "asking_pref"
            SESSIONS[session_id] = sess
            return {"session_id": session_id, "type": "question", "question": "Do you have a preferred date? (YYYY-MM-DD) or preference like 'this week' / 'tomorrow' / 'no preference'"}

        if state == "asking_pref" and ctx.get("asked_pref"):
            pref = msg.lower()
            target_date = None
            if pref == "tomorrow":
                target_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
            elif pref == "this week":
                target_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
            elif pref in ("no preference", "any", "whenever"):
                target_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
            else:
                # if user provided an ISO date anywhere, use it
                if date_val:
                    target_date = date_val
                else:
                    # try to parse plain text date words? Not implemented; fallback to tomorrow
                    try:
                        # attempt ISO parse of the whole message
                        datetime.date.fromisoformat(pref)
                        target_date = pref
                    except Exception:
                        target_date = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()

            ctx["target_date"] = target_date
            sess["state"] = "suggesting_slots"
            # get availability
            avail = get_availability(date=target_date, appointment_type=ctx.get("appointment_type", "consultation"))
            slots = [s for s in avail.get("available_slots", []) if s.get("available")]
            suggested = slots[:5] if len(slots) > 0 else []
            if not suggested:
                sess["state"] = "idle"
                SESSIONS[session_id] = sess
                return {"session_id": session_id, "type": "no_slots", "message": "No slots available on that date. Would you like alternatives?"}
            ctx["suggested_slots"] = suggested
            SESSIONS[session_id] = sess
            return {"session_id": session_id, "type": "suggest_slots", "slots": suggested}

        if state == "suggesting_slots":
            # user picks a time like '10:00' or 'none'
            if "none" in lower or lower in ("no", "not now"):
                sess["state"] = "idle"
                SESSIONS[session_id] = sess
                return {"session_id": session_id, "type": "question", "question": "Okay — would you like me to check other dates? (yes/no)"}
            # If the message contains a HH:MM, use it
            if time_val:
                chosen = time_val
            else:
                # some frontends send just e.g. "09:00" or a word; fallback to first token
                chosen = msg.split()[0] if msg.split() else ""
            # validate chosen is in suggested slots
            for s in ctx.get("suggested_slots", []):
                if s.get("start_time") == chosen:
                    ctx["chosen_slot"] = s
                    sess["state"] = "collect_info"
                    SESSIONS[session_id] = sess
                    return {"session_id": session_id, "type": "question", "question": "Please provide your full name, phone, and email (comma separated)."}
            # If user typed a time not in suggestions, handle gracefully
            return {"session_id": session_id, "type": "error", "message": "Time not recognized. Reply with HH:MM from the suggested list."}

        if state == "collect_info":
            # Accept patient CSV
            if looks_like_patient:
                patient = {"name": parts[0], "phone": parts[1], "email": parts[2]}
                ctx["patient"] = patient
                # perform booking via create_booking helper
                payload = {
                    "appointment_type": ctx.get("appointment_type", "consultation"),
                    "date": ctx.get("target_date"),
                    "start_time": ctx.get("chosen_slot", {}).get("start_time"),
                    "patient": patient,
                    "reason": "Booked via agent"
                }
                br = create_booking(payload)
                sess["state"] = "idle"
                SESSIONS[session_id] = sess
                return {"session_id": session_id, "type": "booking_conf", "booking": br}
            else:
                # ask again
                return {"session_id": session_id, "type": "question", "question": "Please provide name, phone, email separated by commas."}

        # ---------- Not currently in booking flow ----------
        # If the classifier strongly indicates booking, start booking flow
        if intent == "book_appointment":
            sess["state"] = "booking_needs"
            sess["context"] = sess.get("context", {})
            sess["context"]["asked_type"] = True
            SESSIONS[session_id] = sess
            return {"session_id": session_id, "type": "question", "question": "Sure — what type of appointment? (consultation, followup, physical, specialist)"}

        # If message looks like a time and the session has suggested slots, accept it even if we weren't in suggesting_slots
        if time_val and ctx.get("suggested_slots"):
            chosen = time_val
            for s in ctx.get("suggested_slots", []):
                if s.get("start_time") == chosen:
                    ctx["chosen_slot"] = s
                    sess["state"] = "collect_info"
                    SESSIONS[session_id] = sess
                    return {"session_id": session_id, "type": "question", "question": "Please provide your full name, phone, and email (comma separated)."}
            return {"session_id": session_id, "type": "error", "message": "Time not recognized. Reply with HH:MM from the suggested list."}

        # If message looks like patient CSV but we already have a chosen slot (maybe user pasted CSV first), handle that
        if looks_like_patient and ctx.get("chosen_slot"):
            patient = {"name": parts[0], "phone": parts[1], "email": parts[2]}
            ctx["patient"] = patient
            payload = {
                "appointment_type": ctx.get("appointment_type", "consultation"),
                "date": ctx.get("target_date"),
                "start_time": ctx.get("chosen_slot", {}).get("start_time"),
                "patient": patient,
                "reason": "Booked via agent"
            }
            br = create_booking(payload)
            sess["state"] = "idle"
            SESSIONS[session_id] = sess
            return {"session_id": session_id, "type": "booking_conf", "booking": br}

        # yes/no handling for alternative prompts when idle
        if state == "idle" and lower in ("yes", "y", "sure", "ok", "please"):
            # if there were no suggested slots but user said yes to alternatives, ask for date preference
            sess["state"] = "asking_pref"
            sess["context"]["asked_pref"] = True
            SESSIONS[session_id] = sess
            return {"session_id": session_id, "type": "question", "question": "Which date would you like me to check? (YYYY-MM-DD / tomorrow / this week / no preference)"}
        if state == "idle" and lower in ("no", "n", "nah"):
            return {"session_id": session_id, "type": "question", "question": "Okay — anything else I can help with?"}

        # mapped intents to quick replies / FAQ
        if intent == "ask_hours":
            ans = self.rag.query("hours")
            return {"session_id": session_id, "type": "faq", "answer": ans}
        if intent == "ask_insurance":
            ans = self.rag.query("insurance")
            return {"session_id": session_id, "type": "faq", "answer": ans}
        if intent == "ask_phone":
            # return phone as faq-like response
            ans = f"Our clinic phone is {ctx.get('clinic_phone','(unknown)')}."
            return {"session_id": session_id, "type": "faq", "answer": ans}
        if intent == "ask_location":
            ans = self.rag.query("location")
            return {"session_id": session_id, "type": "faq", "answer": ans}
        if intent == "small_talk":
            return {"session_id": session_id, "type": "question", "question": "Hi! How can I help you today? You can say 'Book an appointment' or ask about hours, insurance, or location."}

        # fallback to RAG/FAQ for unknown intent
        ans = self.rag.query(message)
        return {"session_id": session_id, "type": "faq", "answer": ans}
