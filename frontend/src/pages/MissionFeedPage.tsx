import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useState } from "react";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Panel } from "../components/common/Panel";
import { confirmCoopPair, createCoopPair, createMission, listCoopPairs } from "../services/uxuService";

type CoopForm = {
  category: string;
  intensity: number;
  context_tags: string;
  want_now: string;
  partner_invite_user_id: string;
  mission_partner_user_id: string;
};

export function MissionFeedPage() {
  const queryClient = useQueryClient();
  const [formError, setFormError] = useState<string | null>(null);

  const form = useForm<CoopForm>({
    defaultValues: {
      category: "ansiedade",
      intensity: 3,
      context_tags: "escola,apresentacao",
      want_now: "organizar_passos",
      partner_invite_user_id: "",
      mission_partner_user_id: "",
    },
  });

  const pairsQuery = useQuery({ queryKey: ["coop-pairs"], queryFn: listCoopPairs });

  const createMutation = useMutation({
    mutationFn: createMission,
    onSuccess: () => {
      setFormError(null);
      queryClient.invalidateQueries({ queryKey: ["mission-inbox"] });
      queryClient.invalidateQueries({ queryKey: ["my-trails"] });
    },
    onError: () => {
      setFormError("Nao foi possivel criar a missao. Verifique o user_id e a amizade ativa.");
    },
  });

  const createPairMutation = useMutation({
    mutationFn: (partnerUserId: string) => createCoopPair(partnerUserId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["coop-pairs"] }),
  });

  const confirmPairMutation = useMutation({
    mutationFn: ({ pairId, accept }: { pairId: number; accept: boolean }) => confirmCoopPair(pairId, accept),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["coop-pairs"] });
      queryClient.invalidateQueries({ queryKey: ["home-dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["my-profile"] });
    },
  });

  const submitCreate = form.handleSubmit((values) => {
    setFormError(null);
    const partnerUserId = values.mission_partner_user_id.trim();
    const activePartnerIds = new Set((pairsQuery.data?.items ?? []).filter((pair) => pair.status === "active").map((pair) => pair.partner_user_id));
    if (!partnerUserId) {
      setFormError("Informe o user_id do amigo para direcionar a missao.");
      return;
    }
    if (!activePartnerIds.has(partnerUserId)) {
      setFormError("Esse user_id ainda nao esta com amizade ativa. Envie convite e aguarde confirmacao.");
      return;
    }

    const contextTags = values.context_tags
      .split(",")
      .map((v) => v.trim())
      .filter(Boolean);

    createMutation.mutate({
      category: values.category,
      intensity: Number(values.intensity),
      context_tags: contextTags,
      want_now: values.want_now,
      partner_user_id: partnerUserId,
    });
  });

  const submitPair = form.handleSubmit((values) => {
    const partner = values.partner_invite_user_id.trim();
    if (!partner) return;
    createPairMutation.mutate(partner);
  });

  if (pairsQuery.isPending) return <LoadingState label="Carregando sistema de amizade..." />;
  if (pairsQuery.isError) return <ErrorState message="Falha ao carregar cooperacao." />;

  const activePairs = pairsQuery.data.items.filter((pair) => pair.status === "active");

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Cooperacao por amizade</h1>

      <Panel className="border-2 border-emerald-200 bg-emerald-50">
        <h2 className="font-semibold">Convite de amizade por user_id</h2>
        <form className="mt-3 grid gap-2 md:grid-cols-[1fr_auto]" onSubmit={submitPair}>
          <input className="rounded border p-2" placeholder="Digite o user_id do parceiro" {...form.register("partner_invite_user_id")} />
          <button className="rounded bg-ink px-4 py-2 text-white" type="submit" disabled={createPairMutation.isPending}>
            {createPairMutation.isPending ? "Enviando..." : "Enviar convite"}
          </button>
        </form>
        <p className="mt-2 text-xs text-ink/70">
          XP de amizade por marcos: 1, 10, 30, 50, 100, 200, 300, 500, 700 e 1000 amigos ativos.
        </p>

        <div className="mt-3 space-y-2 text-sm">
          {pairsQuery.data.items.length === 0 ? <p className="text-ink/70">Sem amizades ainda.</p> : null}
          {pairsQuery.data.items.map((pair) => (
            <div key={pair.id} className="rounded border border-emerald-200 bg-white p-2">
              <p>
                Amigo: <span className="font-semibold">{pair.partner_name}</span> ({pair.partner_user_id}) - status: {pair.status}
              </p>
              {pair.can_confirm ? (
                <div className="mt-2 flex gap-2">
                  <button
                    className="rounded bg-emerald-700 px-3 py-1 text-white"
                    type="button"
                    onClick={() => confirmPairMutation.mutate({ pairId: pair.id, accept: true })}
                  >
                    Aceitar convite
                  </button>
                  <button
                    className="rounded border border-red-300 px-3 py-1 text-red-700"
                    type="button"
                    onClick={() => confirmPairMutation.mutate({ pairId: pair.id, accept: false })}
                  >
                    Rejeitar
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </Panel>

      <Panel>
        <h2 className="font-semibold">Criar missao direcionada por user_id</h2>
        <form className="mt-3 grid gap-2 md:grid-cols-2" onSubmit={submitCreate}>
          <input
            className="rounded border p-2 md:col-span-2"
            placeholder="user_id do amigo que vai receber a missao"
            {...form.register("mission_partner_user_id")}
          />
          <select className="rounded border p-2" {...form.register("category")}>
            <option value="ansiedade">Ansiedade</option>
            <option value="frustracao">Frustracao</option>
            <option value="autoestima">Autoestima</option>
            <option value="conflitos">Conflitos</option>
            <option value="foco_rotina">Foco/Rotina</option>
          </select>
          <input className="rounded border p-2" type="number" min={1} max={5} {...form.register("intensity")} />
          <input className="rounded border p-2" {...form.register("context_tags")} />
          <select className="rounded border p-2" {...form.register("want_now")}>
            <option value="escuta">Escuta</option>
            <option value="ideias_praticas">Ideias praticas</option>
            <option value="motivacao">Motivacao</option>
            <option value="acalmar">Acalmar</option>
            <option value="organizar_passos">Organizar passos</option>
          </select>
          <button className="rounded bg-ink px-4 py-2 text-white md:col-span-2" type="submit">
            Criar missao direcionada
          </button>
          {formError ? <p className="text-sm text-red-700 md:col-span-2">{formError}</p> : null}
        </form>
      </Panel>

      {createMutation.data ? (
        <Panel className="border-2 border-emerald-200 bg-emerald-50">
          <p className="font-medium text-emerald-800">
            Missao criada e enviada para {createMutation.data.target_user_id ?? "parceiro"}.
          </p>
          <p className="text-sm text-ink/80">ID da missao: #{createMutation.data.id}</p>
        </Panel>
      ) : null}

      {activePairs.length ? <p className="text-sm text-ink/70">Amizades ativas: {activePairs.length}</p> : null}
    </div>
  );
}
