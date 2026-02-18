from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient


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

    admin_headers = login_admin(client)
    approve = client.post(f"/admin/users/{user_id}/approve", headers=admin_headers)
    assert approve.status_code == 200, approve.text

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


def login_admin(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/auth/login",
        json={
            "user_id": "MDU-ADMIN-0001",
            "password": "Admin12345",
        },
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

