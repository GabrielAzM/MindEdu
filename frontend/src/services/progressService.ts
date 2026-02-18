import { api } from "../lib/api";

export type DashboardPayload = {
  headline: {
    xp_total: number;
    level: number;
    tier: string;
    xp_to_next: number;
  };
  stats: {
    trails_completed: number;
    lessons_completed: number;
    quizzes_passed: number;
    missions_created: number;
    helpful_responses: number;
    coop_pairs_active: number;
  };
  skills: {
    empatia: number;
    calma: number;
    comunicacao: number;
    coragem: number;
    autocuidado: number;
  };
  mascot: {
    stage: number;
    max_stage: number;
    evolution_name: string;
    next_stage_at: number | null;
  };
  recent_xp: Array<{ day: string; xp: number }>;
  next_generated_trail?: {
    id: number;
    title: string;
    description: string;
    difficulty: string;
    first_lesson_id: number | null;
  } | null;
};

export type ProfilePayload = {
  user: {
    user_id: string;
    username: string;
    role: "user" | "admin";
    status: "active" | "muted" | "banned";
  };
  xp: {
    total: number;
    level: number;
    current_level_xp: number;
    next_level_xp: number;
    xp_to_next: number;
    tier: string;
  };
  progress: {
    trails_completed: number;
    lessons_completed: number;
    quizzes_passed: number;
    missions_created: number;
    helpful_responses: number;
    coop_pairs_active: number;
  };
  skills: {
    empatia: number;
    calma: number;
    comunicacao: number;
    coragem: number;
    autocuidado: number;
  };
  mascot: {
    stage: number;
    max_stage: number;
    evolution_name: string;
    next_stage_at: number | null;
  };
  cosmetics: {
    reward_pool_total: number;
    inventory: Array<{
      id: string;
      name: string;
      rarity: "common" | "rare" | "epic";
      slot: "head" | "face" | "neck" | "back" | "effect" | "hand" | "chest";
      obtained_from: "seed" | "levelup";
      obtained_at: string;
      effect_multiplier: number;
    }>;
    equipped: {
      fox: string | null;
      owl: string | null;
    };
    rarity_effect_multiplier: {
      common: number;
      rare: number;
      epic: number;
    };
    new_rewards: Array<{
      level: number;
      id: string;
      name: string;
      rarity: "common" | "rare" | "epic";
      slot: string;
      effect_multiplier: number;
    }>;
    duplicate_xp_converted: number;
  };
  recent_xp: Array<{ day: string; xp: number }>;
};

export async function getDashboard() {
  const { data } = await api.get("/me/dashboard");
  return data as DashboardPayload;
}

export async function getMyProfile() {
  const { data } = await api.get("/me/profile");
  return data as ProfilePayload;
}

export async function getMyTrails() {
  const { data } = await api.get("/me/trails");
  return data as {
    items: Array<{
      id: number;
      slug: string;
      title: string;
      description: string;
      age_group: string;
      lesson_count: number;
      first_lesson_id: number | null;
      is_generated: boolean;
      difficulty: string;
      focus_tags: string[];
      recommended_xp?: number;
      status?: string;
      lesson_ids?: number[];
      lessons_preview?: Array<{ id: number; title: string; slug: string }>;
      mission_suggestion?: string | null;
    }>;
  };
}

export async function equipMascotItem(mascotId: "fox" | "owl", itemId: string | null) {
  const { data } = await api.post("/me/mascot/equip", { mascot_id: mascotId, item_id: itemId });
  return data as {
    mascot_id: "fox" | "owl";
    equipped_item: { id: string; name: string; rarity: "common" | "rare" | "epic"; slot: string } | null;
    effect_multiplier: number;
  };
}
