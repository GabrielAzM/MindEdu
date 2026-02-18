import { z } from "zod";
import { adminActions } from "./common";

export const adminUserActionSchema = z.object({
  action: z.enum(adminActions),
  reason: z.string().min(3).max(500),
  duration_minutes: z.number().int().positive().optional(),
});

export const reportResolveSchema = z.object({
  resolution: z.enum(["action_taken", "dismissed"]),
  note: z.string().min(3).max(500),
});

export type AdminUserActionInput = z.infer<typeof adminUserActionSchema>;
export type ReportResolveInput = z.infer<typeof reportResolveSchema>;
