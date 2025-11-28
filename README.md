# 🏥 Appointment Scheduling Agent

A fully conversational **AI-powered appointment scheduling system** with:

* 🧠 Smart intent detection
* 📅 Calendly-style availability + booking
* 💬 React widget for interactive chat
* 🗄️ Session persistence (localStorage + backend)
* 📚 FAQ / RAG using ChromaDB
* ⚡ FastAPI backend with clean APIs

Users can seamlessly talk to the chatbot to book appointments, check availability, get confirmation, and ask clinic-related questions.

---

## 🚀 Features

### 🤖 Conversational Assistant

* Detects booking intent (“I want to book”, “schedule”, etc.)
* Understands date preferences (“tomorrow”, “next week”, “Jan 15”)
* Maintains context across messages
* Handles FAQs when no booking intent is detected

### 🗓️ Scheduling Engine

* Real availability returned from backend
* Computes slot durations automatically
* Prevents overlapping bookings
* Generates a confirmation code

### 🧩 Frontend Chat Widget

* Built using **React + Vite**
* Floating button + popup chat window
* Clean chat interface with:

  * agent messages
  * user messages
  * slot picker
  * confirmation modal
* Embeddable anywhere with one `<ChatWidget />` component

### 📦 Backend APIs

* `POST /api/chat` — conversation handler
* `GET /api/calendly/availability` — check available slots
* `POST /api/calendly/book` — confirm a booking
* Includes health check endpoint `/`

### 💾 Local Session Persistence

* `session_id` stored in:

  * backend memory &
  * browser `localStorage`
* User can close widget, reload page, and continue the same chat

### 🧠 RAG / FAQ Engine

* Knowledge base (`clinic_info.json`)
* Embeddings + ChromaDB vector search
* Falls back to keyword match when needed

---

## 🛠️ Tech Stack

### Backend

* **FastAPI**
* **Python 3.10**
* **Uvicorn**
* **LangChain**
* **ChromaDB**
* **pydantic**
* **python-dotenv**

### Frontend

* **React**
* **Vite**
* **JavaScript**
* **localStorage session persistence**

---

## 📁 Project Structure

```plaintext
backend/
  main.py
  api/
    chat.py
    calendly_integration.py
  agent/
    scheduling_agent.py
  rag/
    faq_rag.py
  data/
    clinic_info.json
frontend/
  src/
    ChatWidget.jsx
    ChatInterface.jsx
    SlotPicker.jsx
    ConfirmationModal.jsx
.env
requirements.txt
README.md
```

---

# ⚙️ Environment Setup

## 1️⃣ Clone the project

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

---

# 🐍 Backend Setup (FastAPI)

## 2️⃣ Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3️⃣ Install backend dependencies

```bash
pip install -r requirements.txt
```

## 4️⃣ Add environment variables

Create `.env` in the project root:

```env
# Clinic Info
CLINIC_NAME=HealthCare Plus Clinic
CLINIC_PHONE=+1-555-123-4567
TIMEZONE=America/New_York

# App Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000

# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key

# Scheduling DB
VECTOR_DB=chromadb
VECTOR_DB_PATH=./data/vectordb
VECTOR_DB_PERSIST_DIR=./data/vectordb

# Calendly-like mock
CALENDLY_API_KEY=demo
CALENDLY_USER_URL=https://calendly.com/
```

## 5️⃣ Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Backend is now available at:

```
http://localhost:8000
```

---

# 🌐 Frontend Setup (Vite + React)

## 1️⃣ Install frontend deps

```bash
cd frontend
npm install
```

## 2️⃣ Create `.env` for frontend:

```
VITE_BACKEND_URL=http://localhost:8000
```

## 3️⃣ Run the dev server

```bash
npm run dev
```

Frontend runs at:

```
http://localhost:3000
```

---

# 🧩 Embedding the Chat Widget

Inside your web app:

```jsx
import ChatWidget from "./ChatWidget";

function App() {
  return (
    <>
      <ChatWidget />
    </>
  );
}

export default App;
```

This renders:

* A floating chat button
* A popup “Paramedic” chatbot window
* Persistent session even after reload

---

# 🔌 Backend API Overview

### `GET /`

Health check.

---

### `POST /api/chat`

Main conversational endpoint:

* Detects intent
* Routes to scheduling
* Returns:

  * `question`
  * `suggest_slots`
  * `booking_conf`
  * `faq`
  * `no_slots`
  * `error`

---

### `GET /api/calendly/availability`

Returns available time slots for a given date + appointment type.

---

### `POST /api/calendly/book`

Creates a booking and returns:

* booking ID
* times
* confirmation code

---

# 📸 Screenshots (Optional)

<video controls src="Screen Recording 2025-11-27 at 10.26.42.mov" title="Title"></video>

---


