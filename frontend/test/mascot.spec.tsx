import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { MascotPage } from "../src/pages/MascotPage";
import { useMascotStore } from "../src/store/mascotStore";

vi.mock("../src/components/pixi/MascotStage", () => ({
  MascotStage: () => <div data-testid="mock-mascot-stage">stage</div>,
}));

vi.mock("../src/services/progressService", () => ({
  getMyProfile: vi.fn().mockResolvedValue({
    user: { user_id: "MDU-TEST-0001", username: "Teste", role: "user", status: "active" },
    xp: { total: 12, tier: "Iniciante", level: 1, current_level_xp: 12, next_level_xp: 100, xp_to_next: 88 },
    progress: { trails_completed: 0, lessons_completed: 0, quizzes_passed: 0, missions_created: 0, helpful_responses: 0, coop_pairs_active: 0 },
    skills: { empatia: 1, calma: 1, comunicacao: 1, coragem: 1, autocuidado: 1 },
    recent_xp: [{ day: "2026-02-17", xp: 5 }],
    mascot: { stage: 1, max_stage: 4, evolution_name: "Evolucao 1", next_stage_at: 30 },
    cosmetics: {
      reward_pool_total: 7,
      inventory: [
        {
          id: "it_01",
          name: "Cachecol Solar",
          rarity: "common",
          slot: "neck",
          obtained_from: "levelup",
          obtained_at: "2026-02-17T00:00:00Z",
          effect_multiplier: 1,
        },
      ],
      equipped: { fox: null, owl: null },
      rarity_effect_multiplier: { common: 1, rare: 2, epic: 3 },
      new_rewards: [],
      duplicate_xp_converted: 0,
    },
  }),
  equipMascotItem: vi.fn().mockResolvedValue({
    mascot_id: "fox",
    equipped_item: { id: "it_01", name: "Cachecol Solar", rarity: "common", slot: "neck" },
    effect_multiplier: 1,
  }),
}));

describe("mascot inventory", () => {
  it("equips an item when clicked", async () => {
    const user = userEvent.setup();
    const qc = new QueryClient();

    render(
      <QueryClientProvider client={qc}>
        <MascotPage />
      </QueryClientProvider>
    );

    const item = await screen.findByRole("button", { name: /Equipar neste mascote/i });
    await user.click(item);

    expect(useMascotStore.getState().equippedByMascot.fox).toBe("it_01");
  });
});
