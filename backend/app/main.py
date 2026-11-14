
from fastapi import FastAPI

from .database import Base, engine
from . import models
from .routers.auth import router as auth_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EventSphere",
    description="University Event and Venue Booking Platform",
    version="1.0.0"
)

# Register authentication routes
app.include_router(auth_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to EventSphere!",
        "status": "Application is running successfully"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
