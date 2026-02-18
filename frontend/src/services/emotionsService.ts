import { api } from "../lib/api";

export async function createCheckin(payload: {
  emotion: string;
  intensity: number;
  context_tags: string[];
  need_tags: string[];
}) {
  const { data } = await api.post("/checkins", payload);
  return data as {
    id: number;
    xp_awarded: number;
    xp_reason: string;
    daily_cap_reached: boolean;
    checkin_date_utc: string;
    suggestion: { type: string; lesson_slug: string; cta: string };
  };
}

export async function getCheckins(range: "week" | "month") {
  const { data } = await api.get("/checkins", { params: { range } });
  return data as { range: string; items: Array<{ date: string; emotion: string; intensity: number }> };
}

export async function getInsights() {
  const { data } = await api.get("/insights");
  return data as { top_emotions: string[]; weekly_pattern: string; what_helps: string[] };
}
