from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from ..db import get_session
from ..lib.security import get_password_hash, verify_password
from ..models.user import User

class UserService:
    def __init__(self, session: Annotated[Session, Depends(get_session)]):
        self.session = session

    def create_user(self, email: str, password: str) -> User:
        user = self.session.exec(select(User).where(User.email == email)).first()
        if user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        hashed_password = get_password_hash(password)
        user = User(email=email, hashed_password=hashed_password)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.session.exec(select(User).where(User.email == email)).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
