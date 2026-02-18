import { z } from "zod";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";

import { zodResolver } from "../lib/zodResolver";
import { resetPasswordRequest } from "../services/recoveryService";

const schema = z.object({ email: z.string().email() });
type FormData = z.infer<typeof schema>;

export function ResetPasswordPage() {
  const form = useForm<FormData>({ resolver: zodResolver(schema) });
  const mutation = useMutation({ mutationFn: (values: FormData) => resetPasswordRequest(values.email) });

  return (
    <div className="mx-auto mt-16 max-w-md rounded-xl border bg-white p-6">
      <h1 className="font-heading text-xl font-bold">Esqueci minha senha</h1>
      <form className="mt-4 space-y-3" onSubmit={form.handleSubmit((v) => mutation.mutate(v))}>
        <input className="w-full rounded border p-2" placeholder="Email" {...form.register("email")} />
        <button className="rounded bg-ink px-4 py-2 text-white" type="submit">
          Solicitar
        </button>
      </form>
      {mutation.data ? (
        <div className="mt-3 rounded bg-sky-50 p-3 text-sm">
          <p>{mutation.data.message}</p>
          <p className="font-mono">request_id: {mutation.data.request_id}</p>
        </div>
      ) : null}
    </div>
  );
}
