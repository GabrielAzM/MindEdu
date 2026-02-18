import { z } from "zod";
import { missionCategories, missionTones } from "./common";

export const missionCreateSchema = z.object({
  category: z.enum(missionCategories),
  intensity: z.number().int().min(1).max(5),
  context_tags: z.array(z.string().min(1).max(32)).min(1).max(8),
  want_now: z.enum(missionTones),
  partner_user_id: z.string().min(6).max(32),
});

export const missionRespondSchema = z.object({
  card_id: z.number().int().positive(),
  guided_actions_selected: z.array(z.string().min(1).max(64)).min(1).max(5),
});

export const missionFeedbackSchema = z.object({
  response_id: z.number().int().positive(),
  useful: z.boolean(),
  best_response: z.boolean().default(false),
});

export type MissionCreateInput = z.infer<typeof missionCreateSchema>;
export type MissionRespondInput = z.infer<typeof missionRespondSchema>;
export type MissionFeedbackInput = z.infer<typeof missionFeedbackSchema>;
