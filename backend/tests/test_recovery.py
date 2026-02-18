from tests.helpers import login_admin, read_recovery_token


def test_forgot_id_and_confirm(client):
    reg = client.post(
        "/auth/register",
        json={"email": "recover@example.com", "username": "Recover", "password": "SenhaForte123"},
    )
    user_id = reg.json()["user_id"]

    req = client.post("/recovery/forgot-id", json={"email": "recover@example.com"})
    assert req.status_code == 200
    request_id = req.json()["request_id"]

    token = read_recovery_token(request_id)
    confirm = client.post("/recovery/confirm", json={"request_id": request_id, "token": token})
    assert confirm.status_code == 200
    assert confirm.json()["user_id"] == user_id


def test_reset_password_confirm(client):
    reg = client.post(
        "/auth/register",
        json={"email": "reset@example.com", "username": "Reset", "password": "SenhaForte123"},
    )
    user_id = reg.json()["user_id"]
    admin_headers = login_admin(client)
    approve = client.post(f"/admin/users/{user_id}/approve", headers=admin_headers)
    assert approve.status_code == 200

    req = client.post("/recovery/reset-password", json={"email": "reset@example.com"})
    request_id = req.json()["request_id"]
    token = read_recovery_token(request_id)

    confirm = client.post(
        "/recovery/confirm",
        json={"request_id": request_id, "token": token, "new_password": "NovaSenha456"},
    )
    assert confirm.status_code == 200

    login = client.post("/auth/login", json={"user_id": user_id, "password": "NovaSenha456"})
    assert login.status_code == 200

