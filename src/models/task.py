# task.py
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    completed: bool = False

    owner_id: Optional[int] = Field(default=None, foreign_key="users.id")
    owner: Optional["User"] = Relationship(back_populates="tasks")
