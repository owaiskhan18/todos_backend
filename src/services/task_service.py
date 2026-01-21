from typing import Annotated, List, Optional

from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from ..db import get_session
from ..models.task import Task
from ..models.user import User

class TaskService:
    def __init__(self, session: Annotated[Session, Depends(get_session)]):
        self.session = session

    def create_task(self, title: str, description: Optional[str], owner_id: int) -> Task:
        task = Task(title=title, description=description, owner_id=owner_id)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_tasks(self, owner_id: int) -> List[Task]:
        tasks = self.session.exec(select(Task).where(Task.owner_id == owner_id)).all()
        return tasks

    def get_task(self, task_id: int, owner_id: int) -> Optional[Task]:
        task = self.session.exec(select(Task).where(Task.id == task_id, Task.owner_id == owner_id)).first()
        return task

    def update_task(self, task_id: int, owner_id: int, title: str, description: Optional[str], completed: bool) -> Task:
        task = self.get_task(task_id, owner_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
        task.title = title
        task.description = description
        task.completed = completed
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def toggle_task_completion(self, task_id: int, owner_id: int) -> Task:
        task = self.get_task(task_id, owner_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
        task.completed = not task.completed
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def delete_task(self, task_id: int, owner_id: int):
        task = self.get_task(task_id, owner_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
        self.session.delete(task)
        self.session.commit()
