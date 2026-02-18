from tests.helpers import register_and_login


def test_content_endpoints(client):
    _, headers = register_and_login(client, 3)

    trails = client.get("/trails?age_group=13-15")
    assert trails.status_code == 200
    assert trails.json()["items"]

    lesson = client.get("/lessons/1")
    assert lesson.status_code == 200
    assert isinstance(lesson.json().get("cards"), list)

    attempt = client.post(
        "/quizzes/1/attempt",
        headers=headers,
        json={
            "answers": [
                {"question_id": 1, "option_id": 2},
                {"question_id": 2, "option_id": 4},
                {"question_id": 3, "option_id": 8},
            ]
        },
    )
    assert attempt.status_code == 200
    payload = attempt.json()
    assert "score" in payload
    assert "xp_awarded" in payload
    assert payload["lesson_completed"] is True
    assert payload["completion_message"] == "trilha ou desafio concluido"

    second_attempt = client.post(
        "/quizzes/1/attempt",
        headers=headers,
        json={
            "answers": [
                {"question_id": 1, "option_id": 2},
                {"question_id": 2, "option_id": 4},
                {"question_id": 3, "option_id": 8},
            ]
        },
    )
    assert second_attempt.status_code == 200
    second_payload = second_attempt.json()
    assert second_payload["xp_awarded"] == 0
    assert second_payload["xp_locked"] is True

