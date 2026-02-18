from tests.helpers import login_admin


def test_admin_approval_and_coop_bonus(client):
    reg1 = client.post(
        "/auth/register",
        json={"email": "pair1@example.com", "username": "Pair1", "password": "SenhaForte123"},
    )
    reg2 = client.post(
        "/auth/register",
        json={"email": "pair2@example.com", "username": "Pair2", "password": "SenhaForte123"},
    )
    user1 = reg1.json()["user_id"]
    user2 = reg2.json()["user_id"]

    pending_login = client.post("/auth/login", json={"user_id": user1, "password": "SenhaForte123"})
    assert pending_login.status_code == 403

    admin_headers = login_admin(client)
    pending = client.get("/admin/users/approvals", headers=admin_headers)
    assert pending.status_code == 200
    pending_ids = [item["user_id"] for item in pending.json()["items"]]
    assert user1 in pending_ids
    assert user2 in pending_ids

    approve1 = client.post(f"/admin/users/{user1}/approve", headers=admin_headers)
    approve2 = client.post(f"/admin/users/{user2}/approve", headers=admin_headers)
    assert approve1.status_code == 200
    assert approve2.status_code == 200

    login1 = client.post("/auth/login", json={"user_id": user1, "password": "SenhaForte123"})
    login2 = client.post("/auth/login", json={"user_id": user2, "password": "SenhaForte123"})
    assert login1.status_code == 200
    assert login2.status_code == 200

    h1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    pair_req = client.post("/coop/pairs", headers=h1, json={"partner_user_id": user2})
    assert pair_req.status_code == 200
    pair_id = pair_req.json()["pair_id"]

    pair_confirm = client.post(f"/coop/pairs/{pair_id}/confirm", headers=h2, json={"accept": True})
    assert pair_confirm.status_code == 200
    assert pair_confirm.json()["status"] == "active"
    assert pair_confirm.json()["friendship_xp"]["user_low_pk"]["active_friends"] >= 1
    assert pair_confirm.json()["friendship_xp"]["user_high_pk"]["active_friends"] >= 1

    mission = client.post(
        "/missions",
        headers=h1,
        json={
            "category": "ansiedade",
            "intensity": 3,
            "context_tags": ["escola"],
            "want_now": "escuta",
            "partner_user_id": user2,
        },
    )
    assert mission.status_code == 200
    mission_id = mission.json()["id"]

    response = client.post(
        f"/missions/{mission_id}/respond",
        headers=h2,
        json={"card_id": 1, "guided_actions_selected": ["respirar_1_min"]},
    )
    assert response.status_code == 200
    response_id = response.json()["response_id"]

    feedback = client.post(
        f"/missions/{mission_id}/feedback",
        headers=h1,
        json={"response_id": response_id, "useful": True, "best_response": True},
    )
    assert feedback.status_code == 200
    assert feedback.json()["coop_bonus_applied"] is True
    assert feedback.json()["xp_awarded_to_responder"] == 30


def test_targeted_coop_mission_only_for_invited_partner(client):
    reg1 = client.post(
        "/auth/register",
        json={"email": "target1@example.com", "username": "Target1", "password": "SenhaForte123"},
    )
    reg2 = client.post(
        "/auth/register",
        json={"email": "target2@example.com", "username": "Target2", "password": "SenhaForte123"},
    )
    reg3 = client.post(
        "/auth/register",
        json={"email": "target3@example.com", "username": "Target3", "password": "SenhaForte123"},
    )
    user1 = reg1.json()["user_id"]
    user2 = reg2.json()["user_id"]
    user3 = reg3.json()["user_id"]

    admin_headers = login_admin(client)
    assert client.post(f"/admin/users/{user1}/approve", headers=admin_headers).status_code == 200
    assert client.post(f"/admin/users/{user2}/approve", headers=admin_headers).status_code == 200
    assert client.post(f"/admin/users/{user3}/approve", headers=admin_headers).status_code == 200

    login1 = client.post("/auth/login", json={"user_id": user1, "password": "SenhaForte123"})
    login2 = client.post("/auth/login", json={"user_id": user2, "password": "SenhaForte123"})
    login3 = client.post("/auth/login", json={"user_id": user3, "password": "SenhaForte123"})
    assert login1.status_code == 200
    assert login2.status_code == 200
    assert login3.status_code == 200

    h1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}
    h3 = {"Authorization": f"Bearer {login3.json()['access_token']}"}

    pair_req = client.post("/coop/pairs", headers=h1, json={"partner_user_id": user2})
    assert pair_req.status_code == 200
    pair_id = pair_req.json()["pair_id"]
    pair_confirm = client.post(f"/coop/pairs/{pair_id}/confirm", headers=h2, json={"accept": True})
    assert pair_confirm.status_code == 200
    assert pair_confirm.json()["status"] == "active"

    mission = client.post(
        "/missions",
        headers=h1,
        json={
            "category": "ansiedade",
            "intensity": 3,
            "context_tags": ["escola"],
            "want_now": "escuta",
            "partner_user_id": user2,
        },
    )
    assert mission.status_code == 200
    mission_id = mission.json()["id"]

    inbox2 = client.get("/missions/inbox", headers=h2)
    inbox3 = client.get("/missions/inbox", headers=h3)
    assert any(item["id"] == mission_id for item in inbox2.json()["items"])
    assert any("voce recebeu uma missao de (" in item["message"] for item in inbox2.json()["items"])
    assert all(item["id"] != mission_id for item in inbox3.json()["items"])

    outsider_response = client.post(
        f"/missions/{mission_id}/respond",
        headers=h3,
        json={"card_id": 1, "guided_actions_selected": ["respirar_1_min"]},
    )
    assert outsider_response.status_code == 403
