import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";

import { AuthGuard, AdminGuard, MutedGuard } from "../src/app/guards";
import { useAuthStore } from "../src/store/authStore";

describe("route guards", () => {
  it("AuthGuard blocks when no token", () => {
    useAuthStore.setState({ accessToken: null, user: null });
    render(
      <MemoryRouter>
        <AuthGuard>
          <div>private-content</div>
        </AuthGuard>
      </MemoryRouter>
    );

    expect(screen.queryByText("private-content")).not.toBeInTheDocument();
  });

  it("AdminGuard allows admin", () => {
    useAuthStore.setState({
      accessToken: "x",
      user: { user_id: "MDU-1", username: "Admin", role: "admin", status: "active" },
    });

    render(
      <MemoryRouter>
        <AdminGuard>
          <div>admin-content</div>
        </AdminGuard>
      </MemoryRouter>
    );

    expect(screen.getByText("admin-content")).toBeInTheDocument();
  });

  it("MutedGuard blocks muted user", () => {
    useAuthStore.setState({
      accessToken: "x",
      user: { user_id: "MDU-2", username: "Muted", role: "user", status: "muted" },
    });

    render(
      <MemoryRouter>
        <MutedGuard>
          <div>social-content</div>
        </MutedGuard>
      </MemoryRouter>
    );

    expect(screen.queryByText("social-content")).not.toBeInTheDocument();
  });
});
