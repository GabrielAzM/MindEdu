from tests.helpers import login_admin


def test_admin_quiz_question_option_crud(client):
    admin_headers = login_admin(client)

    create_question = client.post(
        "/admin/quizzes/1/questions",
        headers=admin_headers,
        json={
            "position": 99,
            "prompt": "Pergunta admin teste",
            "explanation": "Explicacao admin teste",
            "options": [
                {"position": 1, "option_text": "Opcao A", "is_correct": True},
                {"position": 2, "option_text": "Opcao B", "is_correct": False},
            ],
        },
    )
    assert create_question.status_code == 200, create_question.text
    question_id = create_question.json()["id"]

    list_questions = client.get("/admin/quizzes/1/questions", headers=admin_headers)
    assert list_questions.status_code == 200
    assert any(q["id"] == question_id for q in list_questions.json()["items"])

    patch_question = client.patch(
        f"/admin/quiz-questions/{question_id}",
        headers=admin_headers,
        json={"prompt": "Pergunta atualizada"},
    )
    assert patch_question.status_code == 200

    create_option = client.post(
        f"/admin/quiz-questions/{question_id}/options",
        headers=admin_headers,
        json={"position": 3, "option_text": "Opcao C", "is_correct": False},
    )
    assert create_option.status_code == 200
    option_id = create_option.json()["id"]

    patch_option = client.patch(
        f"/admin/quiz-options/{option_id}",
        headers=admin_headers,
        json={"is_correct": True},
    )
    assert patch_option.status_code == 200

    delete_option = client.delete(f"/admin/quiz-options/{option_id}", headers=admin_headers)
    assert delete_option.status_code == 200

    delete_question = client.delete(f"/admin/quiz-questions/{question_id}", headers=admin_headers)
    assert delete_question.status_code == 200
