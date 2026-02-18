import { z } from "zod";
import { checkinRange, emotions, missionTones } from "./common";

export const checkinCreateSchema = z.object({
  emotion: z.enum(emotions),
  intensity: z.number().int().min(1).max(5),
  context_tags: z.array(z.string().min(1).max(32)).min(1).max(8),
  need_tags: z.array(z.enum(missionTones)).min(1).max(5),
});

export const checkinRangeQuerySchema = z.object({
  range: z.enum(checkinRange).default("week"),
});

export type CheckinCreateInput = z.infer<typeof checkinCreateSchema>;
export type CheckinRangeQueryInput = z.infer<typeof checkinRangeQuerySchema>;
