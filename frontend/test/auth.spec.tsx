import { describe, expect, it } from "vitest";

import { useAuthStore } from "../src/store/authStore";

describe("auth store", () => {
  it("stores session after login", () => {
    useAuthStore.setState({ accessToken: null, refreshToken: null, user: null });
    useAuthStore.getState().setSession({
      accessToken: "token-a",
      refreshToken: "token-r",
      user: { user_id: "MDU-ABCD-1234", username: "Ana", role: "user", status: "active" },
    });

    const state = useAuthStore.getState();
    expect(state.accessToken).toBe("token-a");
    expect(state.user?.user_id).toBe("MDU-ABCD-1234");
  });
});
