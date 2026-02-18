import { z } from "zod";

export const forgotIdSchema = z.object({
  email: z.string().email(),
});

export const resetPasswordSchema = z.object({
  email: z.string().email(),
});

export const recoveryConfirmSchema = z.object({
  request_id: z.string().min(3),
  token: z.string().min(4).max(16),
  new_password: z.string().min(8).max(128).optional(),
});

export type ForgotIdInput = z.infer<typeof forgotIdSchema>;
export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>;
export type RecoveryConfirmInput = z.infer<typeof recoveryConfirmSchema>;
