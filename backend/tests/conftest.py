from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "mindedu-test.db"
    outbox_file = Path("data/recovery_outbox.log")
    if outbox_file.exists():
        outbox_file.unlink()

    monkeypatch.setenv("MINDEDU_DB_FILE", str(db_file).replace("\\", "/"))

    from app.core import config as config_mod

    config_mod.get_settings.cache_clear()

    import app.db.session as session_mod
    import app.main as main_mod

    importlib.reload(session_mod)
    importlib.reload(main_mod)

    with TestClient(main_mod.app) as test_client:
        yield test_client


def register_and_login(client: TestClient, idx: int = 1) -> tuple[str, dict[str, str]]:
    reg = client.post(
        "/auth/register",
        json={
            "email": f"user{idx}@example.com",
            "username": f"User{idx}",
            "password": "SenhaForte123",
        },
    )
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["user_id"]

    login = client.post(
        "/auth/login",
        json={
            "user_id": user_id,
            "password": "SenhaForte123",
        },
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return user_id, headers


def read_recovery_token(request_id: str) -> str:
    outbox_file = Path("data/recovery_outbox.log")
    assert outbox_file.exists()
    lines = outbox_file.read_text(encoding="utf-8").strip().splitlines()
    for line in reversed(lines):
        payload = json.loads(line)
        if payload["request_id"] == request_id:
            return payload["token"]
    raise AssertionError("token not found")

