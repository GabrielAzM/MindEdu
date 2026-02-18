from tests.helpers import register_and_login


def test_uxu_mission_flow(client):
    _, headers_a = register_and_login(client, 5)
    user_b_id, headers_b = register_and_login(client, 6)

    pair = client.post(
        "/coop/pairs",
        headers=headers_a,
        json={"partner_user_id": user_b_id},
    )
    assert pair.status_code == 200
    pair_id = pair.json()["pair_id"]

    pair_confirm = client.post(
        f"/coop/pairs/{pair_id}/confirm",
        headers=headers_b,
        json={"accept": True},
    )
    assert pair_confirm.status_code == 200

    mission = client.post(
        "/missions",
        headers=headers_a,
        json={
            "category": "ansiedade",
            "intensity": 3,
            "context_tags": ["escola", "apresentacao"],
            "want_now": "escuta",
            "partner_user_id": user_b_id,
        },
    )
    assert mission.status_code == 200
    mission_id = mission.json()["id"]

    inbox = client.get("/missions/inbox", headers=headers_b)
    assert inbox.status_code == 200
    assert any(item["id"] == mission_id for item in inbox.json()["items"])

    response = client.post(
        f"/missions/{mission_id}/respond",
        headers=headers_b,
        json={"card_id": 1, "guided_actions_selected": ["respirar_1_min"]},
    )
    assert response.status_code == 200
    response_id = response.json()["response_id"]

    feedback = client.post(
        f"/missions/{mission_id}/feedback",
        headers=headers_a,
        json={"response_id": response_id, "useful": True, "best_response": True},
    )
    assert feedback.status_code == 200
    assert feedback.json()["xp_awarded_to_responder"] == 30


def test_mission_requires_partner_user_id(client):
    _, headers_a = register_and_login(client, 50)
    mission = client.post(
        "/missions",
        headers=headers_a,
        json={
            "category": "ansiedade",
            "intensity": 3,
            "context_tags": ["escola"],
            "want_now": "escuta",
        },
    )
    assert mission.status_code == 422

