import { api } from "../lib/api";

export async function getTrails(age_group?: string) {
  const { data } = await api.get("/trails", { params: { age_group } });
  return data as {
    items: Array<{
      id: number;
      slug: string;
      title: string;
      description: string;
      age_group: string;
      lesson_count: number;
      first_lesson_id: number | null;
    }>;
  };
}

export async function getLesson(id: number) {
  const { data } = await api.get(`/lessons/${id}`);
  return data as {
    id: number;
    slug: string;
    title: string;
    duration_min: number;
    quiz_id: number | null;
    cards: Array<{ type: string; text: string }>;
  };
}

export async function completeLesson(id: number, seconds_spent: number) {
  const { data } = await api.post(`/lessons/${id}/complete`, { seconds_spent });
  return data as { status: string; xp_awarded: number };
}

export async function getQuiz(id: number) {
  const { data } = await api.get(`/quizzes/${id}`);
  return data as {
    id: number;
    slug: string;
    title: string;
    passing_score: number;
    lesson_id: number | null;
    trail_id: number | null;
    lesson_title: string | null;
    trail_title: string | null;
    lesson_context: string[];
    questions: Array<{
      id: number;
      position: number;
      prompt: string;
      explanation: string;
      options: Array<{ id: number; position: number; text: string }>;
    }>;
  };
}

export async function submitQuizAttempt(id: number, answers: Array<{ question_id: number; option_id: number }>) {
  const { data } = await api.post(`/quizzes/${id}/attempt`, { answers });
  return data as {
    score: number;
    max_score: number;
    passed: boolean;
    feedback: Array<{ question_id: number; is_correct: boolean; explanation: string }>;
    xp_awarded: number;
    xp_reason: string;
    attempt_number: number;
    best_score: number;
    xp_locked: boolean;
    lesson_completed: boolean;
    lesson_xp_awarded: number;
    challenge_completed: boolean;
    challenge_xp_awarded: number;
    trail_completed: boolean;
    next_lesson_id: number | null;
    completion_message: string | null;
  };
}
