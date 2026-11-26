
"""
HTTP integration tests for JWT authentication and protected APIs.

Tests:
- Signup and login
- Invalid credentials
- Protected profile
- Refresh token rotation
- Logout and refresh revocation
- Unauthorized RAG/document access
- Authenticated document listing and retrieval

Uses an isolated SQLite database.
Does not modify production user accounts.
"""

import importlib
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.database import AuthDatabase
from app.auth.router import get_current_user
from app.main import app


auth_module = importlib.import_module(
    "app.auth.router"
)

documents_module = importlib.import_module(
    "app.api.documents"
)

questions_module = importlib.import_module(
    "app.api.questions"
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Use a temporary SQLite authentication database.

    Each test receives an isolated database and client.
    """
    test_database = AuthDatabase(
        db_path=str(tmp_path / "auth_test.db")
    )

    monkeypatch.setattr(
        auth_module,
        "auth_database",
        test_database,
    )

    app.dependency_overrides.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def signup_user(client):
    """Register a new test account."""
    email = f"user-{uuid4().hex}@example.com"

    response = client.post(
        "/auth/signup",
        json={
            "email": email,
            "password": "SecureTest123!",
        },
    )

    assert response.status_code == 201

    return {
        "email": email,
        "password": "SecureTest123!",
        "access_token": response.json()[
            "access_token"
        ],
        "user_id": response.json()["user"]["id"],
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def test_signup_success(client):
    user = signup_user(client)

    response = client.get(
        "/auth/me",
        headers=auth_headers(
            user["access_token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["email"] == user["email"]
    assert response.json()["id"] == user["user_id"]


def test_duplicate_signup_rejected(client):
    user = signup_user(client)

    response = client.post(
        "/auth/signup",
        json={
            "email": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 409


def test_login_success(client):
    user = signup_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900


def test_invalid_login_rejected(client):
    user = signup_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": user["email"],
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_profile_requires_jwt(client):
    response = client.get(
        "/auth/me"
    )

    assert response.status_code == 401


def test_invalid_access_token_rejected(client):
    response = client.get(
        "/auth/me",
        headers=auth_headers(
            "invalid.jwt.token"
        ),
    )

    assert response.status_code == 401


def test_refresh_token_rotation(client):
    signup_user(client)

    old_refresh_token = client.cookies.get(
        "rag_refresh_token"
    )

    assert old_refresh_token

    response = client.post(
        "/auth/refresh"
    )

    assert response.status_code == 200
    assert response.json()["access_token"]

    new_refresh_token = client.cookies.get(
        "rag_refresh_token"
    )

    assert new_refresh_token
    assert old_refresh_token != new_refresh_token

    # Reusing the previous refresh token must fail.
    with TestClient(app) as replay_client:
        replay_client.cookies.set(
            "rag_refresh_token",
            old_refresh_token,
        )

        replay = replay_client.post(
            "/auth/refresh"
        )

    assert replay.status_code == 401


def test_logout_revokes_refresh_session(client):
    signup_user(client)

    response = client.post(
        "/auth/logout"
    )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "Logged out successfully."
    )

    refresh_response = client.post(
        "/auth/refresh"
    )

    assert refresh_response.status_code == 401


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/documents"),
        ("DELETE", "/documents/test-document"),
        ("POST", "/questions/ask"),
    ],
)
def test_protected_apis_require_jwt(
    client,
    method,
    path,
):
    if method == "POST":
        response = client.post(
            path,
            json={
                "question": "What is annual leave?",
                "top_k": 5,
                "threshold": 0.0,
            },
        )
    else:
        response = client.request(
            method,
            path,
        )

    assert response.status_code == 401


def test_upload_requires_jwt(client):
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "policy.pdf",
                b"%PDF-1.4 fake test document",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 401


def test_authenticated_document_listing(
    client,
    monkeypatch,
):
    user = signup_user(client)

    captured_user_ids = []

    def fake_list_documents(user_id):
        captured_user_ids.append(user_id)
        return []

    monkeypatch.setattr(
        documents_module.document_service,
        "list_documents",
        fake_list_documents,
    )

    response = client.get(
        "/documents",
        headers=auth_headers(
            user["access_token"]
        ),
    )

    assert response.status_code == 200
    assert response.json() == []
    assert captured_user_ids == [
        user["user_id"]
    ]


def test_authenticated_rag_uses_user_identity(
    client,
    monkeypatch,
):
    user = signup_user(client)

    captured_user_ids = []

    def fake_retrieve(
        question,
        top_k,
        threshold,
        user_id,
    ):
        captured_user_ids.append(user_id)
        return []

    monkeypatch.setattr(
        questions_module.retrieval_service,
        "retrieve",
        fake_retrieve,
    )

    response = client.post(
        "/questions/ask",
        headers=auth_headers(
            user["access_token"]
        ),
        json={
            "question": "What is annual leave?",
            "top_k": 5,
            "threshold": 0.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["retrieved_count"] == 0
    assert captured_user_ids == [
        user["user_id"]
    ]
