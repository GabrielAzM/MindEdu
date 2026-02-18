import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { LessonPlayerPage } from "../src/pages/LessonPlayerPage";

vi.mock("../src/services/contentService", () => ({
  getLesson: vi.fn().mockResolvedValue({
    id: 1,
    slug: "emocoes-01",
    title: "Respiracao de 1 minuto",
    duration_min: 3,
    quiz_id: 1,
    cards: [
      { type: "title", text: "Pausa rapida" },
      { type: "content", text: "Inspire 4" },
    ],
  }),
  completeLesson: vi.fn().mockResolvedValue({ status: "completed", xp_awarded: 12 }),
}));

describe("lesson player", () => {
  it("renders lesson cards", async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={["/lessons/1"]}>
          <Routes>
            <Route path="/lessons/:id" element={<LessonPlayerPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(await screen.findByText("Respiracao de 1 minuto")).toBeInTheDocument();
    expect(await screen.findByText("Pausa rapida")).toBeInTheDocument();
  });
});
