
import json
from datetime import datetime

from ..models import (
    AgentMessage, Venue, Event, Booking,
    Ticket, WaitlistEntry
)


# MESSAGE BUS: Transfers structured JSON messages between agents
class MessageBus:

    def __init__(self, db):
        self.db = db
        self.agents = {}

    def register(self, agent):
        self.agents[agent.name] = agent
        agent.bus = self

    def send(self, sender, receiver, performative, content):

        message = {
            "sender": sender,
            "receiver": receiver,
            "performative": performative,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Persist the communication record
        log = AgentMessage(
            sender=sender,
            receiver=receiver,
            performative=performative,
            message_content=json.dumps(message)
        )

        self.db.add(log)
        self.db.commit()

        if receiver not in self.agents:
            return {
                "performative": "FAILURE",
                "content": {"reason": "Agent not found"}
            }

        response = self.agents[receiver].handle_message(message)

        return response


# BASE AGENT
class BaseAgent:

    def __init__(self, name):
        self.name = name
        self.bus = None
        self.beliefs = {}

    def handle_message(self, message):
        return {
            "performative": "REFUSE",
            "content": {"reason": "Message not supported"}
        }


# 1. VENUE AGENT
class VenueAgent(BaseAgent):

    def __init__(self):
        super().__init__("VenueAgent")

    def handle_message(self, message):
        if message["performative"] != "REQUEST":
            return super().handle_message(message)

        data = message["content"]

        venue = self.bus.db.query(Venue).filter(
            Venue.id == data["venue_id"]
        ).first()

        if not venue or not venue.is_available:
            return {
                "performative": "REFUSE",
                "content": {"reason": "Venue unavailable"}
            }

        if data["capacity"] > venue.capacity:
            return {
                "performative": "REFUSE",
                "content": {"reason": "Venue capacity exceeded"}
            }

        overlap = self.bus.db.query(Event).filter(
            Event.venue_id == venue.id,
            Event.start_time < data["end_time"],
            Event.end_time > data["start_time"]
        ).first()

        if overlap:
            return {
                "performative": "REFUSE",
                "content": {"reason": "Venue already booked"}
            }

        self.beliefs[venue.id] = "available"

        return {
            "performative": "AGREE",
            "content": {"message": "Venue is available"}
        }


# 2. BOOKING AGENT
class BookingAgent(BaseAgent):

    def __init__(self):
        super().__init__("BookingAgent")

    def handle_message(self, message):
        if message["performative"] != "REQUEST":
            return super().handle_message(message)

        data = message["content"]

        event = self.bus.db.query(Event).filter(
            Event.id == data["event_id"]
        ).first()

        if not event:
            return {
                "performative": "REFUSE",
                "content": {"reason": "Event not found"}
            }

        bookings = self.bus.db.query(Booking).filter(
            Booking.event_id == event.id,
            Booking.status == "confirmed"
        ).all()

        booked = sum(item.quantity for item in bookings)
        available = event.capacity - booked

        if data["quantity"] > available:
            return {
                "performative": "REFUSE",
                "content": {"reason": "Insufficient seats"}
            }

        self.beliefs[event.id] = available

        return {
            "performative": "AGREE",
            "content": {
                "message": "Seats available",
                "available_seats": available
            }
        }


# 3. TICKET AGENT
class TicketAgent(BaseAgent):

    def __init__(self):
        super().__init__("TicketAgent")

    def handle_message(self, message):
        if message["performative"] != "REQUEST":
            return super().handle_message(message)

        data = message["content"]

        ticket = self.bus.db.query(Ticket).filter(
            Ticket.qr_token == data["qr_token"]
        ).with_for_update().first()

        if not ticket:
            return {
                "performative": "REFUSE",
                "content": {"reason": "Invalid ticket"}
            }

        if ticket.event_id != data["event_id"]:
            return {
                "performative": "REFUSE",
                "content": {"reason": "Wrong event"}
            }

        if ticket.status != "valid" or ticket.checked_in:
            return {
                "performative": "REFUSE",
                "content": {"reason": "Ticket already used or cancelled"}
            }

        ticket.checked_in = True
        ticket.checked_in_at = datetime.utcnow()

        self.bus.db.commit()

        self.beliefs[ticket.id] = "checked_in"

        return {
            "performative": "INFORM",
            "content": {"message": "Ticket check-in successful"}
        }


# 4. NOTIFICATION AGENT
class NotificationAgent(BaseAgent):

    def __init__(self):
        super().__init__("NotificationAgent")
        self.notifications = []

    def handle_message(self, message):
        if message["performative"] not in ["REQUEST", "INFORM"]:
            return super().handle_message(message)

        notification = {
            "message": message["content"],
            "created_at": datetime.utcnow().isoformat()
        }

        self.notifications.append(notification)

        return {
            "performative": "INFORM",
            "content": {"message": "Notification processed"}
        }


# 5. WAITLIST AGENT
class WaitlistAgent(BaseAgent):

    def __init__(self):
        super().__init__("WaitlistAgent")

    def handle_message(self, message):
        if message["performative"] == "REQUEST":
            return self.expire_entries()

        return super().handle_message(message)

    def expire_entries(self):

        now = datetime.utcnow()

        expired_entries = self.bus.db.query(WaitlistEntry).filter(
            WaitlistEntry.status == "offered",
            WaitlistEntry.expires_at <= now
        ).all()

        for entry in expired_entries:
            entry.status = "expired"

            self.bus.send(
                self.name,
                "NotificationAgent",
                "INFORM",
                {
                    "attendee_id": entry.attendee_id,
                    "message": "Your waitlist offer has expired."
                }
            )

        self.bus.db.commit()

        self.beliefs["last_expiry_check"] = now.isoformat()

        return {
            "performative": "INFORM",
            "content": {
                "expired_entries": len(expired_entries)
            }
        }


# CREATE ALL FIVE AGENTS
def create_agent_system(db):

    bus = MessageBus(db)

    agents = [
        VenueAgent(),
        BookingAgent(),
        TicketAgent(),
        WaitlistAgent(),
        NotificationAgent()
    ]

    for agent in agents:
        bus.register(agent)

    return bus
