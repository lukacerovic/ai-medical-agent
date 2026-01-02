# 🤖 CrewAI Implementation Guide

## Overview

This branch (`CREWAI_V`) implements a sophisticated multi-agent system using the CrewAI framework for the MedCare Clinic AI receptionist.

## Architecture

### Multi-Agent System

The system consists of three specialized agents that work together:

1. **Reception Agent (Anna)**
   - Role: First point of contact
   - Responsibilities: Welcome patients, understand initial concerns, route to specialists
   - Personality: Warm, empathetic, professional

2. **Symptoms Analyzer Agent (Dr. Med)**
   - Role: Medical triage specialist
   - Responsibilities: Analyze symptoms, recommend services, provide medical guidance
   - Personality: Knowledgeable, careful, clear communicator

3. **Booking Manager Agent (Registry)**
   - Role: Appointment coordinator
   - Responsibilities: Check availability, collect patient info, confirm bookings
   - Personality: Detail-oriented, precise, organized

### Tools

The agents have access to three custom tools:

1. **ServiceLookupTool**
   - Searches services based on symptoms/keywords
   - Returns matching services with details

2. **AvailabilityCheckTool**
   - Checks appointment slots for next 7 days
   - Shows available dates and times

3. **BookingCreationTool**
   - Creates confirmed bookings
   - Updates availability automatically
   - Generates booking IDs

### Workflow

```
User Message → Intent Detection → Task Selection → Agent Execution → Response
                                        ↓
                                   Tool Usage
                                        ↓
                              Data Storage (JSON)
```

## Project Structure

```
backend/
├── app/
│   ├── crew/
│   │   ├── __init__.py
│   │   ├── agents.py          # Agent definitions
│   │   ├── tasks.py           # Task definitions
│   │   ├── tools.py           # Custom tools
│   │   ├── crew.py            # Crew orchestration
│   │   └── config/
│   │       ├── agents.yaml    # Agent configurations
│   │       └── tasks.yaml     # Task configurations
│   └── data/                  # JSON data storage
│       ├── services.json      # Medical services
│       ├── availability.json  # Appointment slots
│       └── bookings.json      # Confirmed bookings
└── requirements.txt
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Setup Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Gemma 2B model
ollama pull gemma2:2b

# Start Ollama server
ollama serve
```

### 3. Create Data Files

Create `backend/app/data/services.json`:

```json
[
  {
    "id": "cardiology_consultation",
    "name": "Cardiology Consultation",
    "price": 120,
    "duration": "45 min",
    "description": "Expert consultation for cardiac issues, heart problems, chest pain"
  },
  {
    "id": "gastroenterology",
    "name": "Gastroenterology Consultation",
    "price": 110,
    "duration": "40 min",
    "description": "Digestive system consultation for stomach, intestinal issues"
  },
  {
    "id": "blood_analysis",
    "name": "Blood Analysis",
    "price": 50,
    "duration": "20 min",
    "description": "Comprehensive blood test and health screening"
  },
  {
    "id": "dermatology",
    "name": "Dermatology Consultation",
    "price": 100,
    "duration": "30 min",
    "description": "Skin condition consultation, rashes, acne, skin problems"
  },
  {
    "id": "general_practice",
    "name": "General Practice",
    "price": 80,
    "duration": "30 min",
    "description": "General health concerns and checkups"
  }
]
```

Create `backend/app/data/availability.json`:

```json
{
  "2025-01-05": {
    "09:00": true,
    "09:30": true,
    "10:00": true,
    "10:30": true,
    "11:00": true,
    "14:00": true,
    "14:30": true,
    "15:00": true
  },
  "2025-01-06": {
    "09:00": true,
    "09:30": true,
    "10:00": true,
    "10:30": true,
    "11:00": true
  }
}
```

Create `backend/app/data/bookings.json`:

```json
[]
```

### 4. Integration with FastAPI

Update your main FastAPI application to use the crew:

```python
from fastapi import FastAPI
from app.crew import MedicalClinicCrew

app = FastAPI(title="MedCare Clinic AI")
crew = MedicalClinicCrew()

@app.post("/api/chat")
async def chat(session_id: str, message: str):
    result = crew.process_conversation(session_id, message)
    return result

@app.get("/session/new")
async def new_session():
    import uuid
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}
```

## Usage Examples

### Example 1: Symptom Analysis and Service Recommendation

```python
from app.crew import MedicalClinicCrew

crew = MedicalClinicCrew()

# Patient describes symptoms
result = crew.process_conversation(
    session_id="session-123",
    message="I'm having heart problems and chest pain"
)

print(result["response"])
# Output: "I understand you're experiencing heart problems and chest pain...
#          We offer a Cardiology Consultation (€120, 45 minutes)..."
```

### Example 2: Appointment Booking

```python
# Patient wants to book
result = crew.process_conversation(
    session_id="session-123",
    message="Yes, I'd like to book the cardiology consultation"
)

# System shows availability
# Patient selects time
result = crew.process_conversation(
    session_id="session-123",
    message="January 5th at 10:00 AM"
)

# System collects patient info
result = crew.process_conversation(
    session_id="session-123",
    message="My name is John Smith and I was born on May 15th, 1990"
)

# Booking confirmed!
```

## Key Features

### 1. Intent Detection

Automatic detection of user intent:
- `greeting`: Welcome messages
- `symptoms`: Medical concerns
- `book_appointment`: Scheduling requests
- `service_inquiry`: Service information
- `information`: General queries

### 2. Conversation Memory

Each session maintains:
- Message history
- Extracted information (service, date, time, patient details)
- Current intent
- Booking state

### 3. Dynamic Agent Selection

Agents are selected based on intent:
- Simple queries → Reception Agent only
- Symptoms → Reception + Symptoms Analyzer
- Booking → Reception + Booking Manager

### 4. Tool Integration

Agents automatically use tools when needed:
- Symptoms mentioned → ServiceLookupTool
- Booking requested → AvailabilityCheckTool
- Details confirmed → BookingCreationTool

## Configuration

### Agent Configuration

Edit `backend/app/crew/config/agents.yaml` to customize:
- Agent roles
- Goals
- Backstories

### Task Configuration

Edit `backend/app/crew/config/tasks.yaml` to customize:
- Task descriptions
- Expected outputs

### LLM Settings

Modify in `agents.py`:

```python
self.llm = Ollama(
    model="gemma2:2b",
    base_url="http://localhost:11434",
    temperature=0.7  # Adjust creativity (0.0-1.0)
)
```

## Testing

### Test Intent Detection

```python
crew = MedicalClinicCrew()

assert crew.detect_intent("I have chest pain", []) == "symptoms"
assert crew.detect_intent("I want to book", []) == "book_appointment"
assert crew.detect_intent("Hello", []) == "greeting"
```

### Test Conversation Flow

```python
session_id = "test-session"

# Greeting
result1 = crew.process_conversation(session_id, "Hello")
assert result1["intent"] == "greeting"

# Symptoms
result2 = crew.process_conversation(session_id, "I have heart problems")
assert result2["intent"] == "symptoms"
assert "cardiology" in result2["response"].lower()

# Booking
result3 = crew.process_conversation(session_id, "Yes, I want to book")
assert result3["intent"] == "book_appointment"
```

## Debugging

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Session State

```python
state = crew.get_session_state("session-123")
print(state["extracted_info"])
print(state["booking_state"])
```

## Performance Optimization

### 1. Agent Memory

```python
# Limit conversation history
history = session["messages"][-10:]  # Last 10 messages only
```

### 2. Parallel Tool Execution

CrewAI supports parallel tool execution for independent tasks.

### 3. Caching

Implement caching for frequently accessed data:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def load_services():
    # Load services once
    pass
```

## Troubleshooting

### Ollama Connection Error

```bash
# Check if Ollama is running
curl http://localhost:11434

# Restart Ollama
ollama serve
```
### Tool Execution Fails

Check data directory exists:

```bash
mkdir -p backend/app/data
```

### Agent Not Using Tools

Ensure tools are properly registered:

```python
tools = get_medical_tools()
agents = MedicalAgents(tools=tools)
```

## Future Enhancements

1. **Multi-language Support**: Add language detection and translation
2. **Voice Integration**: Connect with Whisper and TTS
3. **Advanced Memory**: Use vector database for long-term memory
4. **Analytics**: Track conversation metrics and success rates
5. **Human Handoff**: Escalate to human staff when needed
6. **Insurance Verification**: Add insurance checking agent
7. **Follow-up System**: Automated appointment reminders

## Contributing

When adding new features:

1. Create new agent in `agents.py`
2. Define tasks in `tasks.py`
3. Add tools in `tools.py`
4. Update crew orchestration in `crew.py`
5. Add tests
6. Update documentation

## License

See main repository LICENSE file.

---

**MedCare Clinic AI** - Powered by CrewAI Multi-Agent Framework
