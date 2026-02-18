import { z } from "zod";

export const exportReportCreateSchema = z.object({
  period_start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  period_end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
});

export type ExportReportCreateInput = z.infer<typeof exportReportCreateSchema>;
