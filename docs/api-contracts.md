# API Contracts MindEdu

Base URL local: `http://localhost:8000`
Formato: JSON
Auth: `Authorization: Bearer <access_token>`

## Auth

### POST /auth/register
Request:
```json
{ "email": "ana@example.com", "username": "AnaLuz", "password": "SenhaForte123" }
```
Response:
```json
{ "user_id": "MDU-A7K9-4P2M", "message": "Cadastro concluido. Guarde seu user_id para login." }
```

### POST /auth/login
Request:
```json
{ "user_id": "MDU-A7K9-4P2M", "password": "SenhaForte123" }
```
Response:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": { "user_id": "MDU-A7K9-4P2M", "username": "AnaLuz", "role": "user", "status": "active" }
}
```

### POST /auth/refresh
Request:
```json
{ "refresh_token": "..." }
```

## Recovery

### POST /recovery/forgot-id
Request:
```json
{ "email": "ana@example.com" }
```

### POST /recovery/reset-password
Request:
```json
{ "email": "ana@example.com" }
```

### POST /recovery/confirm
Request:
```json
{ "request_id": "req_01J...", "token": "845221", "new_password": "NovaSenha123" }
```
Response forgot-id:
```json
{ "user_id": "MDU-A7K9-4P2M" }
```
Response reset-password:
```json
{ "message": "Senha redefinida com sucesso." }
```

## Content

### GET /trails?age_group=10-12
### GET /lessons/{id}
### GET /challenges
Returns active challenges for the signed-in student, including each challenge's lesson, first active quiz, safety notes, XP reward, and completion status.

```json
{
  "items": [
    {
      "id": 1,
      "title": "Mapa de 3 emoções",
      "xp_reward": 20,
      "safety_notes": ["Sem compartilhar dados pessoais"],
      "lesson_id": 1,
      "lesson_title": "Reconhecendo emoções",
      "quiz_id": 1,
      "status": "pending",
      "completed_at": null,
      "completed": false
    }
  ]
}
```

### POST /quizzes/{id}/attempt
Request:
```json
{ "answers": [{ "question_id": 1, "option_id": 2 }] }
```
Response:
```json
{ "score": 80, "max_score": 100, "passed": true, "feedback": [], "xp_awarded": 20 }
```

## Emotions

### POST /checkins
Request:
```json
{
  "emotion": "ansiedade",
  "intensity": 3,
  "context_tags": ["escola", "prova"],
  "need_tags": ["acalmar", "organizar_passos"]
}
```

### GET /checkins?range=week|month
### GET /insights

## UxU

### POST /missions
Request:
```json
{
  "category": "ansiedade",
  "intensity": 3,
  "context_tags": ["escola", "apresentacao"],
  "want_now": "organizar_passos"
}
```

### GET /missions/feed
### POST /missions/{id}/respond
Request:
```json
{ "card_id": 17, "guided_actions_selected": ["respirar_1_min", "listar_3_passos"] }
```

### POST /missions/{id}/feedback
Request:
```json
{ "response_id": 3002, "useful": true, "best_response": true }
```

## Moderation

### POST /reports
Request:
```json
{ "target_type": "mission_response", "target_id": "3002", "reason": "bullying", "details": {"note": "tom agressivo"} }
```

### POST /block/{user_id}
Request body: `{}`

## Admin

- CRUD: `/admin/trails`, `/admin/lessons`, `/admin/quizzes`, `/admin/challenges`
- GET `/admin/moderation/reports`
- POST `/admin/moderation/reports/{id}/resolve`
- POST `/admin/users/{id}/action`
- GET `/admin/users/{id}/progress` (educational progress summary; each view is audited)
- GET `/admin/audit`
- GET `/admin/metrics`

## Exports

### POST /exports/report
Request:
```json
{ "period_start": "2026-02-01", "period_end": "2026-02-15" }
```

### GET /exports/report/{id}
### GET /exports/report/{id}/download

## Validacao

- Frontend: Zod (`shared/schemas`)
- Backend: JSON Schema (`shared/generated`) + Pydantic em runtime
