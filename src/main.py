from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from .db import engine, create_db_and_tables
from .routes import auth # Placeholder for auth routes
from .routes import tasks # Placeholder for tasks routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables...")
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Setup CORS
origins = [
    "http://localhost",
    "http://localhost:3000", # Frontend URL
    "https://todos-umber.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
