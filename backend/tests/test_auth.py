from tests.helpers import login_admin, register_and_login


def test_register_and_login_with_user_id(client):
    reg = client.post(
        "/auth/register",
        json={"email": "ana@example.com", "username": "AnaLuz", "password": "SenhaForte123"},
    )
    assert reg.status_code == 200
    user_id = reg.json()["user_id"]
    assert user_id.startswith("MDU-")

    login = client.post("/auth/login", json={"user_id": user_id, "password": "SenhaForte123"})
    assert login.status_code == 403

    admin_headers = login_admin(client)
    approve = client.post(f"/admin/users/{user_id}/approve", headers=admin_headers)
    assert approve.status_code == 200

    login = client.post("/auth/login", json={"user_id": user_id, "password": "SenhaForte123"})
    assert login.status_code == 200
    assert "access_token" in login.json()

    wrong = client.post("/auth/login", json={"user_id": "ana@example.com", "password": "SenhaForte123"})
    assert wrong.status_code == 401


def test_refresh_token_flow(client):
    _, _ = register_and_login(client, 2)
    reg = client.post(
        "/auth/register",
        json={"email": "beto@example.com", "username": "Beto", "password": "SenhaForte123"},
    )
    user_id = reg.json()["user_id"]

    admin_headers = login_admin(client)
    approve = client.post(f"/admin/users/{user_id}/approve", headers=admin_headers)
    assert approve.status_code == 200

    login = client.post("/auth/login", json={"user_id": user_id, "password": "SenhaForte123"})
    refresh_token = login.json()["refresh_token"]

    refreshed = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    assert "access_token" in refreshed.json()

