import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "../lib/zodResolver";
import { useMutation } from "@tanstack/react-query";
import { useNavigate, Link } from "react-router-dom";

import { register } from "../services/authService";
import { useAuthStore } from "../store/authStore";

const schema = z.object({
  email: z.string().email(),
  username: z.string().min(2),
  password: z.string().min(8),
});

type FormData = z.infer<typeof schema>;

function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) return response.data.detail;
  }
  return "Falha ao cadastrar.";
}

export function RegisterPage() {
  const navigate = useNavigate();
  const setPendingUserId = useAuthStore((s) => s.setPendingUserId);

  const form = useForm<FormData>({ resolver: zodResolver(schema) });
  const mutation = useMutation({
    mutationFn: register,
    onSuccess: (data) => {
      setPendingUserId(data.user_id);
      navigate("/onboarding/user-id");
    },
  });

  return (
    <div className="mx-auto mt-16 max-w-md rounded-xl border border-sky-100 bg-white p-6 shadow">
      <h1 className="font-heading text-2xl font-bold">Criar conta</h1>
      <p className="mt-1 text-sm text-ink/70">Login sera com user_id + senha.</p>
      <form className="mt-4 space-y-3" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
        <input className="w-full rounded border p-2" placeholder="Email" {...form.register("email")} />
        <input className="w-full rounded border p-2" placeholder="Username" {...form.register("username")} />
        <input className="w-full rounded border p-2" placeholder="Senha" type="password" {...form.register("password")} />
        {mutation.error ? <p className="text-sm text-red-600">{getErrorMessage(mutation.error)}</p> : null}
        <button className="w-full rounded bg-ink px-4 py-2 text-white" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Criando..." : "Cadastrar"}
        </button>
      </form>
      <Link className="mt-3 block text-sm text-blue-700" to="/login">
        Ja tenho conta
      </Link>
    </div>
  );
}
