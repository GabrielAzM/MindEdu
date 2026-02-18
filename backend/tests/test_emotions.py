from tests.helpers import register_and_login


def test_checkins_and_insights(client):
    _, headers = register_and_login(client, 4)

    checkin = client.post(
        "/checkins",
        headers=headers,
        json={
            "emotion": "ansiedade",
            "intensity": 3,
            "context_tags": ["escola", "prova"],
            "need_tags": ["acalmar", "organizar_passos"],
        },
    )
    assert checkin.status_code == 200
    assert "suggestion" in checkin.json()
    assert checkin.json()["xp_awarded"] == 3

    second_same_day = client.post(
        "/checkins",
        headers=headers,
        json={
            "emotion": "ansiedade",
            "intensity": 2,
            "context_tags": ["escola"],
            "need_tags": ["acalmar"],
        },
    )
    assert second_same_day.status_code == 200
    assert second_same_day.json()["xp_awarded"] == 0
    assert second_same_day.json()["daily_cap_reached"] is True

    week = client.get("/checkins?range=week", headers=headers)
    assert week.status_code == 200
    assert isinstance(week.json()["items"], list)

    insights = client.get("/insights", headers=headers)
    assert insights.status_code == 200
    assert "top_emotions" in insights.json()

