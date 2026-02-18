import { api } from "../lib/api";

export type RegisterInput = {
  email: string;
  username: string;
  password: string;
};

export type LoginInput = {
  user_id: string;
  password: string;
};

export async function register(input: RegisterInput) {
  const { data } = await api.post("/auth/register", input);
  return data as { user_id: string; message: string };
}

export async function login(input: LoginInput) {
  const { data } = await api.post("/auth/login", input);
  return data as {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
    user: {
      user_id: string;
      username: string;
      role: "user" | "admin";
      status: "active" | "muted" | "banned" | "pending";
    };
  };
}

export async function refresh(refresh_token: string) {
  const { data } = await api.post("/auth/refresh", { refresh_token });
  return data as { access_token: string; refresh_token: string; token_type: string; expires_in: number };
}
