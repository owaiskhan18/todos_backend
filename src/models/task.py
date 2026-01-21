# src/models/task.py
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel
from .user import User

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    completed: bool = False

    owner_id: Optional[int] = Field(default=None, foreign_key="users.id")  # 👈 note "users.id"
    owner: Optional["User"] = Relationship(back_populates="tasks")
