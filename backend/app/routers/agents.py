
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import User, AgentMessage
from ..dependencies import require_roles
from ..agents.system import create_agent_system

router = APIRouter(prefix="/api/agents", tags=["Agents"])


class AgentRequest(BaseModel):
    receiver: str
    performative: str
    content: dict


# SEND MESSAGE BETWEEN AGENTS (ADMIN ONLY)
@router.post("/send")
def send_agent_message(
    data: AgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    allowed_agents = [
        "VenueAgent",
        "BookingAgent",
        "TicketAgent",
        "WaitlistAgent",
        "NotificationAgent"
    ]

    if data.receiver not in allowed_agents:
        return {"error": "Unknown agent"}

    if data.performative not in [
        "REQUEST", "AGREE", "REFUSE",
        "PROPOSE", "INFORM", "FAILURE"
    ]:
        return {"error": "Invalid performative"}

    bus = create_agent_system(db)

    response = bus.send(
        sender="Admin",
        receiver=data.receiver,
        performative=data.performative,
        content=data.content
    )

    return {
        "sender": "Admin",
        "receiver": data.receiver,
        "response": response
    }


# VIEW AGENT COMMUNICATION LOGS
@router.get("/messages")
def get_agent_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    messages = (
        db.query(AgentMessage)
        .order_by(AgentMessage.created_at.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": message.id,
            "sender": message.sender,
            "receiver": message.receiver,
            "performative": message.performative,
            "content": message.message_content,
            "created_at": message.created_at
        }
        for message in messages
    ]


# VIEW REGISTERED AGENTS
@router.get("/status")
def get_agent_status(
    current_user: User = Depends(require_roles("admin"))
):
    return {
        "agents": [
            "VenueAgent",
            "BookingAgent",
            "TicketAgent",
            "WaitlistAgent",
            "NotificationAgent"
        ],
        "total_agents": 5,
        "status": "registered"
    }
