# src/models/user.py
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from pydantic import ConfigDict
from .task import Task

class User(SQLModel, table=True):
    __tablename__ = "users"  # 👈 safe table name for Postgres
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str

    tasks: List["Task"] = Relationship(back_populates="owner")
