import { z } from "zod";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { zodResolver } from "../lib/zodResolver";
import { login } from "../services/authService";
import { useAuthStore } from "../store/authStore";

const schema = z.object({
  user_id: z.string().min(6),
  password: z.string().min(8),
});

type FormData = z.infer<typeof schema>;

function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) return response.data.detail;
  }
  return "Credenciais invalidas.";
}

export function LoginPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((s) => s.setSession);

  const form = useForm<FormData>({ resolver: zodResolver(schema) });
  const mutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      setSession({ accessToken: data.access_token, refreshToken: data.refresh_token, user: data.user });
      navigate("/home");
    },
  });

  return (
    <div className="mx-auto mt-16 max-w-md rounded-xl border border-sky-100 bg-white p-6 shadow">
      <h1 className="font-heading text-2xl font-bold">Entrar</h1>
      <p className="mt-1 text-sm text-ink/70">Use user_id e senha.</p>
      <form className="mt-4 space-y-3" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
        <input className="w-full rounded border p-2" placeholder="user_id" {...form.register("user_id")} />
        <input className="w-full rounded border p-2" type="password" placeholder="Senha" {...form.register("password")} />
        {mutation.error ? <p className="text-sm text-red-600">{getErrorMessage(mutation.error)}</p> : null}
        <button className="w-full rounded bg-ink px-4 py-2 text-white" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Entrando..." : "Entrar"}
        </button>
      </form>
      <div className="mt-4 flex justify-between text-sm text-blue-700">
        <Link to="/recovery/forgot-id">Esqueci meu ID</Link>
        <Link to="/recovery/reset-password">Esqueci minha senha</Link>
      </div>
      <Link to="/register" className="mt-2 block text-sm text-ink/70">
        Não tenho conta
      </Link>
    </div>
  );
}
