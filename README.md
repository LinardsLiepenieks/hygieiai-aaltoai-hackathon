# 🏥 Futuuri Hygiei AI

**Your AI-Powered Personal Nurse** — Intelligent outbound patient calling and health check-ins for continuous care beyond the clinic.

## 🎯 What It Does

Futuuri Hygiei AI enables healthcare providers to maintain continuous contact with patients through AI-driven voice interactions. Perfect for post-operative care, chronic condition monitoring, and routine wellness checks.

## ✨ Core Features

- **🩺 Personal AI Nurse**: Schedule automated follow-ups or call on-demand for health concerns
- **📅 Smart Scheduling**: Automated appointment booking linked to specific doctor visits and medical databases
- **🎤 Voice-First Experience**: Natural conversation using advanced speech-to-text and text-to-speech
- **🧠 Context-Aware Memory**: Remembers patient history and emotional state across interactions

## 🛠️ Tech Stack

**Frontend**

- Next.js 16 (React 19)
- TypeScript
- Tailwind CSS

**Backend & Agents**

- FastAPI (Python)
- Docker Compose orchestration
- Deployed on Datacrunch

**AI & Voice**

- LLM: **Meta Llama 3.1 70B** (via OpenRouter)
- TTS/STT: **ElevenLabs API**

## 🏗️ Architecture

```
┌─────────────┐
│  Frontend   │  (Next.js - User Interface)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Backend   │  (FastAPI - Request Router)
└──────┬──────┘
       │
       ├──────────────────┬──────────────────┬──────────────────┐
       ▼                  ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Extraction  │───▶│  Summary    │───▶│  Response   │    │ Scheduling  │
│   Agent     │    │   Agent     │    │   Agent     │    │   Agent     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     (Analyst)        (Librarian)       (Communicator)     (Coordinator)
```

**Flow**:

1. **Frontend** → User speaks/types to the system
2. **Backend** → Routes request to agents
3. **Extraction Agent** → Analyzes message intent & medical relevance, retrieves context from Summary Agent
4. **Response Agent** → Generates empathetic, medically-appropriate response
5. **Summary Agent** → Updates patient memory with emotional & clinical data
6. **Scheduling Agent** → Independently manages doctor appointments via medical database access

## 🤖 The Agentic Network

### 🔍 Extraction Agent

**The Clinical Analyst** — Employs keyword sieves and emergency pattern detection to classify message intent (emergency, medical, smalltalk, routine). Surfaces critical information using OLD CARTS medical framework, ensuring no symptom goes unnoticed.

### 💬 Response Agent

**The Compassionate Communicator** — Crafts context-aware responses tailored to intent. Provides urgent care instructions for emergencies, asks focused follow-up questions for medical concerns, and maintains warm conversation for routine check-ins.

### 📚 Summary Agent

**The Medical Librarian** — Maintains comprehensive patient records by analyzing conversations for medical relevance, emotional states, and safety concerns. Creates structured summaries for clinical review while flagging emergencies.

### 📆 Scheduling Agent

**The Autonomous Coordinator** — Initiates outbound calls based on medical database triggers (post-surgery follow-ups, chronic disease check-ins). Manages appointment booking with natural conversation flow, respecting available time slots.

## 🚀 Quick Start

```bash
# Build and run all services
docker-compose up --build

# Access the application
Frontend: http://localhost:3000
Backend:  http://localhost:8000
```

## 📝 Environment Setup

Create `frontend/.env.local`:

```
NEXT_PUBLIC_ELEVENLABS_API_KEY=your_api_key_here
```

---

**Built for healthcare's future** 🏥✨
