import { z } from "zod";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";

import { zodResolver } from "../lib/zodResolver";
import { recoveryConfirm } from "../services/recoveryService";

const schema = z.object({
  request_id: z.string().min(3),
  token: z.string().min(4),
  new_password: z.string().min(8).optional(),
});

type FormData = z.infer<typeof schema>;

export function RecoveryConfirmPage() {
  const form = useForm<FormData>({ resolver: zodResolver(schema) });
  const mutation = useMutation({ mutationFn: (values: FormData) => recoveryConfirm(values) });

  return (
    <div className="mx-auto mt-16 max-w-md rounded-xl border bg-white p-6">
      <h1 className="font-heading text-xl font-bold">Confirmar recuperacao</h1>
      <form className="mt-4 space-y-3" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
        <input className="w-full rounded border p-2" placeholder="request_id" {...form.register("request_id")} />
        <input className="w-full rounded border p-2" placeholder="token" {...form.register("token")} />
        <input
          className="w-full rounded border p-2"
          placeholder="nova senha (apenas reset de senha)"
          type="password"
          {...form.register("new_password")}
        />
        <button className="rounded bg-ink px-4 py-2 text-white" type="submit">
          Confirmar
        </button>
      </form>
      {mutation.data ? (
        <pre className="mt-3 rounded bg-sky-50 p-3 text-xs">{JSON.stringify(mutation.data, null, 2)}</pre>
      ) : null}
    </div>
  );
}
