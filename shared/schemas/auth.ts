import { z } from "zod";

export const authRegisterSchema = z.object({
  email: z.string().email(),
  username: z.string().min(2).max(32),
  password: z.string().min(8).max(128),
});

export const authLoginSchema = z.object({
  user_id: z.string().min(6).max(32),
  password: z.string().min(8).max(128),
});

export const authRefreshSchema = z.object({
  refresh_token: z.string().min(10),
});

export type AuthRegisterInput = z.infer<typeof authRegisterSchema>;
export type AuthLoginInput = z.infer<typeof authLoginSchema>;
export type AuthRefreshInput = z.infer<typeof authRefreshSchema>;
