import { z } from "zod";
import { reportReasons, reportTargetTypes } from "./common";

export const reportCreateSchema = z.object({
  target_type: z.enum(reportTargetTypes),
  target_id: z.string().min(1).max(64),
  reason: z.enum(reportReasons),
  details: z.record(z.unknown()).optional(),
});

export const blockCreateSchema = z.object({});

export type ReportCreateInput = z.infer<typeof reportCreateSchema>;
