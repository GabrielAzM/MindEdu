from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

MissionCategory = Literal[
    "ansiedade",
    "frustracao",
    "autoestima",
    "conflitos",
    "foco_rotina",
    "social",
    "familia",
    "escola",
]

WantNow = Literal["escuta", "ideias_praticas", "motivacao", "acalmar", "organizar_passos"]
EmotionKey = Literal[
    "alegria",
    "tristeza",
    "raiva",
    "medo",
    "ansiedade",
    "frustracao",
    "calma",
    "orgulho",
    "confusao",
]
ReportReason = Literal["assedio", "dados_pessoais", "improprio", "bullying", "spam", "outro"]
ReportTargetType = Literal["mission", "mission_response", "user", "coop_challenge"]


class RegisterIn(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    user_id: str = Field(min_length=6, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=10)


class ForgotIn(BaseModel):
    email: EmailStr


class RecoveryConfirmIn(BaseModel):
    request_id: str = Field(min_length=3)
    token: str = Field(min_length=4, max_length=16)
    new_password: str | None = Field(default=None, min_length=8, max_length=128)


class QuizAnswerIn(BaseModel):
    question_id: int = Field(gt=0)
    option_id: int = Field(gt=0)


class QuizAttemptIn(BaseModel):
    answers: list[QuizAnswerIn]


class CheckinIn(BaseModel):
    emotion: EmotionKey
    intensity: int = Field(ge=1, le=5)
    context_tags: list[str] = Field(min_length=1, max_length=8)
    need_tags: list[WantNow] = Field(min_length=1, max_length=5)


class MissionCreateIn(BaseModel):
    category: MissionCategory
    intensity: int = Field(ge=1, le=5)
    context_tags: list[str] = Field(min_length=1, max_length=8)
    want_now: WantNow
    partner_user_id: str = Field(min_length=6, max_length=32)


class MissionRespondIn(BaseModel):
    card_id: int = Field(gt=0)
    guided_actions_selected: list[str] = Field(min_length=1, max_length=5)


class MissionFeedbackIn(BaseModel):
    response_id: int = Field(gt=0)
    useful: bool
    best_response: bool = False


class ReportIn(BaseModel):
    target_type: ReportTargetType
    target_id: str = Field(min_length=1, max_length=64)
    reason: ReportReason
    details: dict[str, Any] = Field(default_factory=dict)


class AdminUserActionIn(BaseModel):
    action: Literal["warn", "mute", "ban", "unban", "reset_password", "reset_user_id"]
    reason: str = Field(min_length=3, max_length=500)
    duration_minutes: int | None = Field(default=None, ge=1)


class ReportResolveIn(BaseModel):
    resolution: Literal["action_taken", "dismissed"]
    note: str = Field(min_length=3, max_length=500)


class ExportReportIn(BaseModel):
    period_start: date
    period_end: date


class MascotEquipIn(BaseModel):
    mascot_id: Literal["fox", "owl"]
    item_id: str | None = Field(default=None, min_length=3, max_length=64)


class AdminQuizOptionIn(BaseModel):
    option_text: str = Field(min_length=1, max_length=400)
    is_correct: bool
    position: int = Field(ge=1)


class AdminQuizQuestionCreateIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=600)
    explanation: str = Field(min_length=1, max_length=1200)
    position: int = Field(ge=1)
    options: list[AdminQuizOptionIn] = Field(min_length=2, max_length=6)


class AdminQuizQuestionUpdateIn(BaseModel):
    prompt: str | None = Field(default=None, min_length=1, max_length=600)
    explanation: str | None = Field(default=None, min_length=1, max_length=1200)
    position: int | None = Field(default=None, ge=1)


class AdminQuizOptionCreateIn(BaseModel):
    option_text: str = Field(min_length=1, max_length=400)
    is_correct: bool
    position: int = Field(ge=1)


class AdminQuizOptionUpdateIn(BaseModel):
    option_text: str | None = Field(default=None, min_length=1, max_length=400)
    is_correct: bool | None = None
    position: int | None = Field(default=None, ge=1)


class UserCtx(BaseModel):
    model_config = ConfigDict(extra="ignore")
    pk: int
    user_id: str
    username: str
    role: str
    status: str
