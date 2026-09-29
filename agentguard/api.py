from fastapi import FastAPI
from pydantic import BaseModel
from agentguard.firewall.guarded_agent import run_guarded_agent

app = FastAPI(title="AgentGuard Demo API")

class Query(BaseModel):
    message: str

@app.get("/")
def health():
    return {"status": "ok", "service": "AgentGuard"}

@app.post("/chat")
def chat(q: Query):
    return {"response": run_guarded_agent(q.message)}