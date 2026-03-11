from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.infrastructure.llm import explain_recommendation
from app.infrastructure.data import CARS
from app.domain.engine import recommend_cars
from app.infrastructure.memory import reset_session
from app.services.agent import run_agent
from app.services.nlp import parse_message_to_agent_input
from app.models.preferences import profile_to_agent_prefs

app = FastAPI()
app.mount("/ui", StaticFiles(directory="ui"), name="ui")

class AgentInput(BaseModel):
    session_id: Optional[str] = None
    fuel: Optional[str] = None
    body: Optional[str] = None
    gearbox: Optional[str] = None
    reliability_priority: Optional[int] = None
    comfort_priority: Optional[int] = None
    year: Optional[int] = None

class Preferences(BaseModel):
    session_id: str | None = None  # NEW
    fuel: str | None = None
    body: str | None = None
    gearbox: str | None = None
    reliability_priority: int = 5
    comfort_priority: int = 3

class ChatInput(BaseModel):
    session_id: Optional[str] = None
    message: str

@app.get("/")
def root():
    return FileResponse("ui/index.html")


@app.post("/recommend")
def recommend(prefs: Preferences):
    return recommend_cars(CARS, prefs.model_dump())

@app.post("/explain")
def explain(prefs: Preferences):
    result = recommend_cars(CARS, prefs.model_dump())
    explanation = explain_recommendation(prefs.model_dump(), result)
    return {
        "result": result,
        "explanation": explanation

    }

@app.post("/agent")
def agent(prefs: AgentInput):
    return run_agent(prefs.model_dump())

@app.post("/session/reset")
def session_reset(payload: dict):
    sid = payload.get("session_id")
    if not sid:
        return {"status": "error", "message": "session_id required"}
    reset_session(sid)
    return {"status": "ok", "message": f"reset {sid}"}

@app.post("/chat")
def chat(inp: ChatInput):
    profile = parse_message_to_agent_input(inp.message)
    payload = profile_to_agent_prefs(profile)
    payload["session_id"] = inp.session_id
    payload["raw_message"] = inp.message
    return run_agent(payload)