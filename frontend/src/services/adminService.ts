import { api } from "../lib/api";

export type AdminTrail = {
  id: number;
  slug: string;
  title: string;
  description: string;
  age_group: string;
  is_active: number;
};

export type AdminQuiz = {
  id: number;
  trail_id: number;
  lesson_id: number | null;
  slug: string;
  title: string;
  passing_score: number;
  is_active: number;
};

export type AdminQuizOption = {
  id: number;
  question_id: number;
  position: number;
  option_text: string;
  is_correct: boolean;
};

export type AdminQuizQuestion = {
  id: number;
  quiz_id: number;
  position: number;
  prompt: string;
  explanation: string;
  options: AdminQuizOption[];
};

export async function getAdminTrails() {
  const { data } = await api.get("/admin/trails");
  return data as { items: AdminTrail[] };
}

export async function getAdminQuizzes() {
  const { data } = await api.get("/admin/quizzes");
  return data as { items: AdminQuiz[] };
}

export async function createAdminQuiz(payload: {
  trail_id: number;
  lesson_id?: number | null;
  slug: string;
  title: string;
  passing_score?: number;
  is_active?: boolean;
}) {
  const { data } = await api.post("/admin/quizzes", payload);
  return data as { id: number };
}

export async function updateAdminQuiz(
  quizId: number,
  payload: Partial<{ trail_id: number; lesson_id: number | null; slug: string; title: string; passing_score: number; is_active: boolean }>
) {
  const { data } = await api.patch(`/admin/quizzes/${quizId}`, payload);
  return data as { status: string };
}

export async function deleteAdminQuiz(quizId: number) {
  const { data } = await api.delete(`/admin/quizzes/${quizId}`);
  return data as { status: string };
}

export async function getAdminQuizQuestions(quizId: number) {
  const { data } = await api.get(`/admin/quizzes/${quizId}/questions`);
  return data as { items: AdminQuizQuestion[] };
}

export async function createAdminQuizQuestion(
  quizId: number,
  payload: {
    position: number;
    prompt: string;
    explanation: string;
    options: Array<{ position: number; option_text: string; is_correct: boolean }>;
  }
) {
  const { data } = await api.post(`/admin/quizzes/${quizId}/questions`, payload);
  return data as { id: number };
}

export async function updateAdminQuizQuestion(
  questionId: number,
  payload: Partial<{ position: number; prompt: string; explanation: string }>
) {
  const { data } = await api.patch(`/admin/quiz-questions/${questionId}`, payload);
  return data as { status: string };
}

export async function deleteAdminQuizQuestion(questionId: number) {
  const { data } = await api.delete(`/admin/quiz-questions/${questionId}`);
  return data as { status: string };
}

export async function createAdminQuizOption(
  questionId: number,
  payload: { position: number; option_text: string; is_correct: boolean }
) {
  const { data } = await api.post(`/admin/quiz-questions/${questionId}/options`, payload);
  return data as { id: number };
}

export async function updateAdminQuizOption(
  optionId: number,
  payload: Partial<{ position: number; option_text: string; is_correct: boolean }>
) {
  const { data } = await api.patch(`/admin/quiz-options/${optionId}`, payload);
  return data as { status: string };
}

export async function deleteAdminQuizOption(optionId: number) {
  const { data } = await api.delete(`/admin/quiz-options/${optionId}`);
  return data as { status: string };
}

export async function getAdminReports() {
  const { data } = await api.get("/admin/moderation/reports");
  return data as { items: Array<Record<string, unknown>> };
}

export async function getPendingApprovals(status: "pending" | "approved" | "rejected" | "all" = "pending") {
  const { data } = await api.get("/admin/users/approvals", { params: { status } });
  return data as {
    items: Array<{
      id: number;
      user_id: string;
      email: string;
      username: string;
      account_status: string;
      approval_status: "pending" | "approved" | "rejected";
      created_at: string;
      approved_at: string | null;
      rejected_reason: string | null;
    }>;
  };
}

export async function approveUserSignup(userId: string) {
  const { data } = await api.post(`/admin/users/${userId}/approve`);
  return data as { status: string; audit_id?: number };
}

export async function rejectUserSignup(userId: string, reason: string) {
  const { data } = await api.post(`/admin/users/${userId}/reject`, { reason });
  return data as { status: string; audit_id?: number };
}

export async function resolveAdminReport(reportId: number, payload: { resolution: string; note: string }) {
  const { data } = await api.post(`/admin/moderation/reports/${reportId}/resolve`, payload);
  return data as { status: string; audit_id: number };
}

export async function adminUserAction(
  userId: string,
  payload: { action: string; reason: string; duration_minutes?: number }
) {
  const { data } = await api.post(`/admin/users/${userId}/action`, payload);
  return data as {
    status: string;
    audit_id: number;
    action_id?: number;
    temporary_password?: string;
    new_user_id?: string;
  };
}

export async function deleteAdminUser(userId: string, reason: string) {
  const { data } = await api.delete(`/admin/users/${userId}`, { data: { reason } });
  return data as {
    status: string;
    audit_id: number;
    deleted_user_id: string;
    reason: string;
  };
}

export async function getAudit() {
  const { data } = await api.get("/admin/audit");
  return data as { items: Array<Record<string, unknown>> };
}

export async function getMetrics() {
  const { data } = await api.get("/admin/metrics");
  return data as {
    users_total: number;
    active_7d: number;
    reports_open: number;
    useful_feedback: number;
    approvals_pending: number;
  };
}
