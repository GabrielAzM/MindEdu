import { z } from "zod";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { zodResolver } from "../lib/zodResolver";
import { createCheckin } from "../services/emotionsService";
import { Panel } from "../components/common/Panel";
import { Link } from "react-router-dom";

function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) return response.data.detail;
  }
  return "Falha ao registrar check-in.";
}

const schema = z.object({
  emotion: z.enum(["alegria", "tristeza", "raiva", "medo", "ansiedade", "frustracao", "calma", "orgulho", "confusao"]),
  intensity: z.coerce.number().min(1).max(5),
  context_tags: z.string().min(1),
  need_tags: z.string().min(1),
});

type FormData = z.infer<typeof schema>;

export function CheckinPage() {
  const queryClient = useQueryClient();
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      emotion: "ansiedade",
      intensity: 3,
      context_tags: "escola,prova",
      need_tags: "acalmar,organizar_passos",
    },
  });

  const mutation = useMutation({
    mutationFn: (values: FormData) =>
      createCheckin({
        emotion: values.emotion,
        intensity: values.intensity,
        context_tags: values.context_tags.split(",").map((v) => v.trim()),
        need_tags: values.need_tags.split(",").map((v) => v.trim()),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["home-dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["my-profile"] });
    },
  });

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Check-in emocional</h1>
      <Panel>
        <form className="grid gap-3 md:grid-cols-2" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
          <select className="rounded border p-2" {...form.register("emotion")}>
            <option value="ansiedade">Ansiedade</option>
            <option value="frustracao">Frustração</option>
            <option value="calma">Calma</option>
            <option value="alegria">Alegria</option>
          </select>
          <input className="rounded border p-2" type="number" min={1} max={5} {...form.register("intensity")} />
          <input className="rounded border p-2" placeholder="context_tags" {...form.register("context_tags")} />
          <input className="rounded border p-2" placeholder="need_tags" {...form.register("need_tags")} />
          <button className="rounded bg-ink px-4 py-2 text-white md:col-span-2" type="submit">
            Registrar
          </button>
          {mutation.error ? <p className="text-sm text-red-700 md:col-span-2">{getErrorMessage(mutation.error)}</p> : null}
        </form>
      </Panel>
      {mutation.data ? (
        <Panel className="border-2 border-emerald-200 bg-emerald-50">
          <p className="font-semibold">Check-in registrado com sucesso.</p>
          <p className="text-sm text-ink/80">
            XP hoje: {mutation.data.xp_awarded} ({mutation.data.xp_reason}).
          </p>
          {mutation.data.daily_cap_reached ? <p className="text-sm text-amber-800">Limite diário de XP do check-in já utilizado.</p> : null}
          <div className="mt-2">
            <Link to="/coop" className="rounded bg-ink px-3 py-1 text-sm text-white">
              {mutation.data.suggestion.cta}
            </Link>
          </div>
        </Panel>
      ) : null}
    </div>
  );
}
