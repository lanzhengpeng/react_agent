from fastapi import APIRouter
from app.models.request import AgentRequest
from app.models.response import AgentResponse
from app.core.agent import run_agent

router = APIRouter()

@router.post("/run_agent", response_model=AgentResponse)
def run_agent_endpoint(request: AgentRequest):
    return run_agent(request)
