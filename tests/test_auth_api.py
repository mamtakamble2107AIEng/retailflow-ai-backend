from datetime import datetime, timezone
from types import SimpleNamespace
from app.auth import create_access_token
import jwt  
from fastapi.testclient import TestClient

from app.main import app
from app.auth import get_current_user

client = TestClient(app)



def test_auth_me_without_token():
    previous_override = app.dependency_overrides.get(
        get_current_user
    )

    # Remove the fake user so real authentication is checked
    app.dependency_overrides.pop(get_current_user, None)

    try:
        response = client.get("/auth/me")
        assert response.status_code == 401

    finally:
        # Restore the previous override
        if previous_override is not None:
            app.dependency_overrides[get_current_user] = previous_override



def test_auth_me_with_valid_user_override():

    test_customer = SimpleNamespace(
    id=1,
    full_name="Test Customer",
    email="test@example.com",
    role="customer",
    is_active=True,
    created_at=datetime.now(timezone.utc)
)

    
    previous_override = app.dependency_overrides.get(
        get_current_user
    )

    app.dependency_overrides[get_current_user] = (
        lambda: test_customer
    )

    try:
        response = client.get("/auth/me")
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    finally:
        if previous_override is not None:
            app.dependency_overrides[get_current_user] = previous_override
        else:
            app.dependency_overrides.pop(get_current_user, None)



def test_create_access_token():
    token = create_access_token({"sub": "1"})

    payload = jwt.decode(
        token,
        algorithms=["HS256"],
        options={"verify_signature": False}
    )

    assert payload["sub"] == "1"
    assert "exp" in payload


from app.auth import SECRET_KEY, ALGORITHM


def test_jwt_signature_verification():
    token = create_access_token({"sub": "1"})

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )

    assert payload["sub"] == "1"

import pytest
import jwt

from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app

def test_tampered_jwt_token():
    token = create_access_token({"sub": "1"})

    tampered_token = token[:-5] + "abcde"

    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(
            tampered_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )


from datetime import datetime, timedelta, timezone


def test_expired_jwt_token():
    expired_payload = {
        "sub": "1",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1)
    }

    expired_token = jwt.encode(
        expired_payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(
            expired_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
