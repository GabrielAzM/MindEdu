import { describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { QuizPlayerPage } from "../src/pages/QuizPlayerPage";

vi.mock("../src/services/contentService", () => ({
  getQuiz: vi.fn().mockResolvedValue({
    id: 1,
    slug: "quiz-emocoes-01",
    title: "Quiz de Emocoes",
    passing_score: 70,
    lesson_id: 1,
    trail_id: 1,
    lesson_title: "Reconhecendo emocoes",
    trail_title: "Trilha de Emocoes",
    lesson_context: ["Toda emocao traz um sinal", "Nomear emocao ajuda a escolher melhor o proximo passo."],
    questions: [
      {
        id: 1,
        position: 1,
        prompt: "Qual escala de intensidade?",
        explanation: "Escala de 1 a 5 no MindEdu.",
        options: [
          { id: 1, position: 1, text: "1 a 5" },
          { id: 2, position: 2, text: "1 a 10" },
        ],
      },
    ],
  }),
  submitQuizAttempt: vi.fn().mockResolvedValue({
    score: 100,
    max_score: 100,
    passed: true,
    feedback: [],
    xp_awarded: 20,
    xp_reason: "primeira tentativa no quiz",
    attempt_number: 1,
    best_score: 100,
    xp_locked: false,
    lesson_completed: true,
    lesson_xp_awarded: 12,
    challenge_completed: true,
    challenge_xp_awarded: 20,
    trail_completed: false,
    next_lesson_id: 2,
    completion_message: "trilha ou desafio concluido",
  }),
}));

describe("quiz player", () => {
  it("hides questions and shows success panel after submit", async () => {
    const qc = new QueryClient();
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={["/quizzes/1"]}>
          <Routes>
            <Route path="/quizzes/:id" element={<QuizPlayerPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(await screen.findByText("Quiz de Emocoes")).toBeInTheDocument();
    await user.click(screen.getByRole("radio", { name: /1 a 5/i }));
    await user.click(screen.getByRole("button", { name: /Enviar tentativa/i }));

    expect(await screen.findByText(/Tentativa enviada com sucesso/i)).toBeInTheDocument();
    expect(screen.queryByText(/Qual escala de intensidade/i)).not.toBeInTheDocument();
    expect(screen.getByText(/XP ganho: 20/i)).toBeInTheDocument();
  });
});
