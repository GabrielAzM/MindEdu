import { z } from "zod";

export const trailsQuerySchema = z.object({
  age_group: z.enum(["10-12", "13-15", "16-17", "all"]).optional(),
});

export const quizAttemptSchema = z.object({
  answers: z.array(
    z.object({
      question_id: z.number().int().positive(),
      option_id: z.number().int().positive(),
    })
  ).min(1),
});

export type TrailsQueryInput = z.infer<typeof trailsQuerySchema>;
export type QuizAttemptInput = z.infer<typeof quizAttemptSchema>;
