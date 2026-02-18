import { api } from "../lib/api";

export async function forgotId(email: string) {
  const { data } = await api.post("/recovery/forgot-id", { email });
  return data as { request_id: string; message: string };
}

export async function resetPasswordRequest(email: string) {
  const { data } = await api.post("/recovery/reset-password", { email });
  return data as { request_id: string; message: string };
}

export async function recoveryConfirm(payload: { request_id: string; token: string; new_password?: string }) {
  const { data } = await api.post("/recovery/confirm", payload);
  return data as { user_id?: string; message?: string };
}
