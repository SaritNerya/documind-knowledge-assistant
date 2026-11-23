from datetime import datetime, timezone

import pytest
from jose import jwt

from tests.conftest import requires_db

pytestmark = requires_db


def token_lifetime_hours(client, remember):
    from app.core.config import settings
    from app.core.security import ALGORITHM

    data = {"username": "r@test.dev", "password": "password123"}
    if remember is not None:
        data["remember"] = str(remember).lower()
    token = client.post("/auth/login", data=data).json()["access_token"]
    exp = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])["exp"]
    return (datetime.fromtimestamp(exp, timezone.utc) - datetime.now(timezone.utc)).total_seconds() / 3600


@pytest.mark.parametrize("remember, expected_hours", [(None, 1), (False, 1), (True, 30 * 24)])
def test_remember_me_controls_token_lifetime(db, remember, expected_hours):
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    client.post("/auth/register", json={"email": "r@test.dev", "password": "password123"})
    assert token_lifetime_hours(client, remember) == pytest.approx(expected_hours, abs=0.1)
