from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, SQLModel # Added SQLModel import

from ..db import get_session
from ..middleware.jwt import get_current_user
from ..models.user import User
from ..services.task_service import TaskService
from ..models.task import Task

router = APIRouter()

class TaskCreate(SQLModel):
    title: str
    description: Optional[str] = None

class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

@router.post("/users/{user_id}/tasks", response_model=Task)
def create_user_task(
    user_id: int,
    task_data: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends()]
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create tasks for this user")
    
    return task_service.create_task(task_data.title, task_data.description, current_user.id)

@router.get("/users/{user_id}/tasks", response_model=List[Task])
def get_user_tasks(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends()]
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view tasks for this user")
    
    return task_service.get_tasks(current_user.id)

@router.get("/users/{user_id}/tasks/{task_id}", response_model=Task)
def get_user_task(
    user_id: int,
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends()]
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view tasks for this user")
    
    task = task_service.get_task(task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task

@router.put("/users/{user_id}/tasks/{task_id}", response_model=Task)
def update_user_task(
    user_id: int,
    task_id: int,
    task_data: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends()]
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update tasks for this user")
    
    # Fetch current task to get existing title, description, completed status
    existing_task = task_service.get_task(task_id, current_user.id)
    if not existing_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    updated_title = task_data.title if task_data.title is not None else existing_task.title
    updated_description = task_data.description if task_data.description is not None else existing_task.description
    updated_completed = task_data.completed if task_data.completed is not None else existing_task.completed

    return task_service.update_task(
        task_id, 
        current_user.id, 
        updated_title, 
        updated_description, 
        updated_completed
    )

@router.patch("/users/{user_id}/tasks/{task_id}/complete", response_model=Task)
def toggle_task_completion(
    user_id: int,
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends()]
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update tasks for this user")
    
    return task_service.toggle_task_completion(task_id, current_user.id)

@router.delete("/users/{user_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_task(
    user_id: int,
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends()]
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete tasks for this user")
    
    task_service.delete_task(task_id, current_user.id)
    return
