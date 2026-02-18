from tests.helpers import register_and_login


def test_reports_and_block(client):
    user_a, headers_a = register_and_login(client, 7)
    user_b, headers_b = register_and_login(client, 8)

    report = client.post(
        "/reports",
        headers=headers_a,
        json={
            "target_type": "user",
            "target_id": user_b,
            "reason": "spam",
            "details": {"note": "mensagens repetidas"},
        },
    )
    assert report.status_code == 200
    assert report.json()["status"] == "open"

    block = client.post(f"/block/{user_b}", headers=headers_a, json={})
    assert block.status_code == 200
    assert "bloqueado" in block.json()["message"].lower()

