import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel

from backend.src.main import app, get_session
from backend.src.models.user import User
from backend.src.models.task import Task
from backend.src.lib.security import get_password_hash

# Setup in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def drop_db_and_tables():
    SQLModel.metadata.drop_all(engine)

def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

@pytest.fixture(name="client")
def client_fixture():
    drop_db_and_tables()
    create_db_and_tables()
    with TestClient(app) as client:
        yield client
    drop_db_and_tables()

@pytest.fixture(name="test_user")
def test_user_fixture(client: TestClient, session: Session):
    user = User(email="test@example.com", hashed_password=get_password_hash("testpassword"))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def get_auth_token(client: TestClient, email: str, password: str):
    response = client.post(
        "/api/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return response.json()["access_token"]

def test_signup():
    client = TestClient(app)
    response = client.post(
        "/api/signup",
        json={"email": "newuser@example.com", "password": "newpassword"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User created successfully"}

def test_signup_existing_email():
    client = TestClient(app)
    client.post("/api/signup", json={"email": "existing@example.com", "password": "password"})
    response = client.post("/api/signup", json={"email": "existing@example.com", "password": "anotherpassword"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login():
    client = TestClient(app)
    client.post("/api/signup", json={"email": "user@example.com", "password": "password"})
    response = client.post(
        "/api/login",
        data={"username": "user@example.com", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials():
    client = TestClient(app)
    response = client.post(
        "/api/login",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_create_task(client: TestClient, test_user: User):
    token = get_auth_token(client, test_user.email, "testpassword")
    response = client.post(
        f"/api/users/{test_user.id}/tasks",
        json={"title": "Test Task", "description": "Description for test task"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test Task"
    assert response.json()["owner_id"] == test_user.id

def test_get_tasks(client: TestClient, test_user: User):
    token = get_auth_token(client, test_user.email, "testpassword")
    client.post(
        f"/api/users/{test_user.id}/tasks",
        json={"title": "Task 1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        f"/api/users/{test_user.id}/tasks",
        json={"title": "Task 2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get(
        f"/api/users/{test_user.id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["title"] == "Task 1"

def test_get_task_by_id(client: TestClient, test_user: User):
    token = get_auth_token(client, test_user.email, "testpassword")
    create_response = client.post(
        f"/api/users/{test_user.id}/tasks",
        json={"title": "Single Task"},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create_response.json()["id"]

    response = client.get(
        f"/api/users/{test_user.id}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Single Task"

def test_update_task(client: TestClient, test_user: User):
    token = get_auth_token(client, test_user.email, "testpassword")
    create_response = client.post(
        f"/api/users/{test_user.id}/tasks",
        json={"title": "Old Title", "description": "Old Description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create_response.json()["id"]

    update_data = {"title": "New Title", "description": "New Description", "completed": True}
    response = client.put(
        f"/api/users/{test_user.id}/tasks/{task_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["description"] == "New Description"
    assert response.json()["completed"] is True

def test_toggle_task_completion(client: TestClient, test_user: User):
    token = get_auth_token(client, test_user.email, "testpassword")
    create_response = client.post(
        f"/api/users/{test_user.id}/tasks",
        json={"title": "Toggle Task", "completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create_response.json()["id"]

    response = client.patch(
        f"/api/users/{test_user.id}/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["completed"] is True

    response = client.patch(
        f"/api/users/{test_user.id}/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["completed"] is False

def test_delete_task(client: TestClient, test_user: User):
    token = get_auth_token(client, test_user.email, "testpassword")
    create_response = client.post(
        f"/api/users/{test_user.id}/tasks",
        json={"title": "Task to Delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create_response.json()["id"]

    response = client.delete(
        f"/api/users/{test_user.id}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    get_response = client.get(
        f"/api/users/{test_user.id}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404

def test_task_ownership_create(client: TestClient, test_user: User):
    token = get_auth_token(client, test_user.email, "testpassword")
    another_user_id = test_user.id + 1 # Assuming another user ID

    response = client.post(
        f"/api/users/{another_user_id}/tasks",
        json={"title": "Forbidden Task"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to create tasks for this user"

def test_task_ownership_get(client: TestClient, test_user: User):
    # Create a task for test_user
    token = get_auth_token(client, test_user.email, "testpassword")
    client.post(
        f"/api/users/{test_user.id}/tasks",
        json={"title": "My Task"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Try to get tasks for another user
    another_user_id = test_user.id + 1
    response = client.get(
        f"/api/users/{another_user_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to view tasks for this user"
