import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { MissionFeedPage } from "../src/pages/MissionFeedPage";

vi.mock("../src/services/uxuService", () => ({
  createMission: vi.fn().mockResolvedValue({ id: 100, status: "open", expires_at: "2026-02-20", target_user_id: "MDU-X1", is_targeted: true }),
  listCoopPairs: vi.fn().mockResolvedValue({ items: [] }),
  createCoopPair: vi.fn().mockResolvedValue({ pair_id: 1, status: "pending", partner_user_id: "MDU-X1" }),
  confirmCoopPair: vi.fn().mockResolvedValue({
    status: "active",
    friendship_xp: {
      user_low_pk: { active_friends: 1, awarded_now: [{ milestone: 1, xp_awarded: 1 }], xp_awarded_total: 1 },
      user_high_pk: { active_friends: 1, awarded_now: [{ milestone: 1, xp_awarded: 1 }], xp_awarded_total: 1 },
    },
  }),
}));

describe("mission flow", () => {
  it("submits mission creation form", async () => {
    const qc = new QueryClient();
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={qc}>
        <MissionFeedPage />
      </QueryClientProvider>
    );

    const button = await screen.findByRole("button", { name: /Criar missao/i });
    await user.click(button);

    await waitFor(() => {
      expect(screen.getByText("Cooperacao por amizade")).toBeInTheDocument();
    });
  });
});
