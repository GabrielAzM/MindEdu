import { api } from "../lib/api";

export async function createMission(payload: {
  category: string;
  intensity: number;
  context_tags: string[];
  want_now: string;
  partner_user_id: string;
}) {
  const { data } = await api.post("/missions", payload);
  return data as { id: number; status: string; expires_at: string; target_user_id?: string | null; is_targeted: boolean };
}

export async function getMissionInbox() {
  const { data } = await api.get("/missions/inbox");
  return data as {
    items: Array<{
      id: number;
      category: string;
      intensity: number;
      context_tags: string[];
      want_now: string;
      expires_at: string | null;
      created_at: string;
      creator_user_id: string;
      creator_username: string;
      message: string;
    }>;
  };
}

export async function getMission(missionId: number) {
  const { data } = await api.get(`/missions/${missionId}`);
  return data as {
    id: number;
    creator_user_pk: number;
    category: string;
    intensity: number;
    context_tags: string[];
    want_now: string;
    status: string;
    expires_at: string | null;
    response_count: number;
    target_user_id?: string | null;
    creator_user_id: string;
    is_targeted: boolean;
    is_mine: boolean;
  };
}

export async function getSupportCards(category: string, tone: string) {
  const { data } = await api.get("/missions/support-cards", { params: { category, tone } });
  return data as {
    items: Array<{
      id: number;
      card_key: string;
      category: string;
      tone: string;
      title: string;
      body: string;
      guided_actions: string[];
    }>;
  };
}

export async function respondMission(missionId: number, payload: { card_id: number; guided_actions_selected: string[] }) {
  const { data } = await api.post(`/missions/${missionId}/respond`, payload);
  return data as { response_id: number; status: string };
}

export async function feedbackMission(
  missionId: number,
  payload: { response_id: number; useful: boolean; best_response: boolean }
) {
  const { data } = await api.post(`/missions/${missionId}/feedback`, payload);
  return data as { message: string; xp_awarded_to_responder: number; coop_bonus_applied: boolean };
}

export async function reportTarget(payload: {
  target_type: "mission" | "mission_response" | "user" | "coop_challenge";
  target_id: string;
  reason: string;
  details?: Record<string, unknown>;
}) {
  const { data } = await api.post("/reports", payload);
  return data as { report_id: number; status: string };
}

export async function blockUser(userId: string) {
  const { data } = await api.post(`/block/${userId}`, {});
  return data as { message: string };
}

export async function createCoopPair(partner_user_id: string) {
  const { data } = await api.post("/coop/pairs", { partner_user_id });
  return data as { pair_id: number; status: "pending" | "active"; partner_user_id: string };
}

export async function listCoopPairs() {
  const { data } = await api.get("/coop/pairs");
  return data as {
    items: Array<{
      id: number;
      status: "pending" | "active" | "rejected";
      created_at: string;
      confirmed_at: string | null;
      partner_user_pk: number;
      partner_user_id: string;
      partner_name: string;
      can_confirm: boolean;
    }>;
  };
}

export async function confirmCoopPair(pairId: number, accept: boolean) {
  const { data } = await api.post(`/coop/pairs/${pairId}/confirm`, { accept });
  return data as {
    status: "active" | "rejected";
    friendship_xp?: {
      user_low_pk: { active_friends: number; awarded_now: Array<{ milestone: number; xp_awarded: number }>; xp_awarded_total: number };
      user_high_pk: { active_friends: number; awarded_now: Array<{ milestone: number; xp_awarded: number }>; xp_awarded_total: number };
    };
  };
}
