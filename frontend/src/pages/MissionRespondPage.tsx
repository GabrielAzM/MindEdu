import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Panel } from "../components/common/Panel";
import { feedbackMission, getMission, getSupportCards, respondMission } from "../services/uxuService";
import { formatMindEduLabel } from "../lib/mindEduLabels";

function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) return response.data.detail;
  }
  return "Falha na operação.";
}

export function MissionRespondPage() {
  const { id } = useParams();
  const missionId = Number(id ?? 1);
  const queryClient = useQueryClient();

  const missionQuery = useQuery({ queryKey: ["mission", missionId], queryFn: () => getMission(missionId) });
  const cardsQuery = useQuery({
    queryKey: ["support-cards", missionQuery.data?.category, missionQuery.data?.want_now],
    queryFn: () => getSupportCards(missionQuery.data!.category, missionQuery.data!.want_now),
    enabled: !!missionQuery.data,
  });

  const [selectedCard, setSelectedCard] = useState<number | null>(null);
  const [selectedActions, setSelectedActions] = useState<string[]>([]);
  const [responseId, setResponseId] = useState<number | null>(null);

  const respond = useMutation({
    mutationFn: () =>
      respondMission(missionId, {
        card_id: selectedCard ?? 0,
        guided_actions_selected: selectedActions,
      }),
    onSuccess: (data) => {
      setResponseId(data.response_id);
      queryClient.invalidateQueries({ queryKey: ["mission-inbox"] });
      queryClient.invalidateQueries({ queryKey: ["my-trails"] });
    },
  });

  const feedback = useMutation({
    mutationFn: ({ useful, best_response }: { useful: boolean; best_response: boolean }) =>
      feedbackMission(missionId, { response_id: responseId ?? 0, useful, best_response }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["home-dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["my-profile"] });
    },
  });

  const selectedCardData = useMemo(
    () => cardsQuery.data?.items.find((item) => item.id === selectedCard) ?? null,
    [cardsQuery.data, selectedCard]
  );

  if (missionQuery.isPending) return <LoadingState label="Carregando missão..." />;
  if (missionQuery.isError) return <ErrorState message="Falha ao carregar missão." />;

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Responder missão #{missionId}</h1>
      <Panel>
        <p className="font-semibold">
          Categoria: {formatMindEduLabel(missionQuery.data.category)} | intensidade: {missionQuery.data.intensity}/5
        </p>
        <p className="text-sm text-ink/70">
          Contexto: {missionQuery.data.context_tags.map(formatMindEduLabel).join(", ")} | precisa agora: {formatMindEduLabel(missionQuery.data.want_now)}
        </p>
        {missionQuery.data.is_targeted && missionQuery.data.target_user_id ? (
          <p className="mt-1 text-xs font-medium text-emerald-700">Missão cooperativa direcionada para: {missionQuery.data.target_user_id}</p>
        ) : null}
      </Panel>

      {missionQuery.data.is_mine ? (
        <Panel className="border-2 border-amber-200 bg-amber-50">
          <p className="font-medium text-amber-900">Esta missão foi criada por você.</p>
          <p className="text-sm text-ink/80">No MVP, o próprio autor não pode responder a própria missão.</p>
        </Panel>
      ) : null}

      {cardsQuery.isPending ? <LoadingState label="Carregando cartas aprovadas..." /> : null}
      {cardsQuery.isError ? <ErrorState message="Falha ao carregar cartas." /> : null}
      {cardsQuery.data && !missionQuery.data.is_mine ? (
        <Panel>
          <h2 className="font-semibold">Escolha uma Carta de Apoio</h2>
          <div className="mt-3 space-y-2">
            {cardsQuery.data.items.map((card) => (
              <button
                key={card.id}
                type="button"
                onClick={() => {
                  setSelectedCard(card.id);
                  setSelectedActions([]);
                }}
                className={`w-full rounded border p-3 text-left ${selectedCard === card.id ? "border-ink bg-sky-50" : "border-sky-100"}`}
              >
                <p className="font-semibold">{card.title}</p>
                <p className="text-sm text-ink/70">{card.body}</p>
              </button>
            ))}
          </div>
        </Panel>
      ) : null}

      {selectedCardData && !missionQuery.data.is_mine ? (
        <Panel>
          <h2 className="font-semibold">Ações guiadas da carta</h2>
          <div className="mt-2 space-y-2">
            {selectedCardData.guided_actions.map((action) => {
              const active = selectedActions.includes(action);
              return (
                <label key={action} className="flex items-center gap-2 rounded border border-sky-100 p-2">
                  <input
                    type="checkbox"
                    checked={active}
                    onChange={(event) => {
                      setSelectedActions((prev) => {
                        if (event.target.checked) return [...prev, action];
                        return prev.filter((item) => item !== action);
                      });
                    }}
                  />
                  {formatMindEduLabel(action)}
                </label>
              );
            })}
          </div>
          <button
            className="mt-3 rounded bg-ink px-4 py-2 text-white"
            onClick={() => respond.mutate()}
            type="button"
            disabled={!selectedCard || selectedActions.length === 0 || respond.isPending}
          >
            {respond.isPending ? "Enviando..." : "Enviar carta"}
          </button>
          {respond.error ? <p className="mt-2 text-sm text-red-700">{getErrorMessage(respond.error)}</p> : null}
        </Panel>
      ) : null}

      {respond.data ? (
        <Panel className="border-2 border-emerald-200 bg-emerald-50">
          <p className="font-medium text-emerald-800">Carta enviada com sucesso.</p>
          <p className="text-sm text-ink/80">Resposta registrada: #{respond.data.response_id}</p>
        </Panel>
      ) : null}

      {responseId ? (
        <Panel>
          <h2 className="font-semibold">Validar cooperação</h2>
          <p className="text-sm text-ink/70">Quem criou a missão confirma se ajudou. Em parceria ativa, XP vem em dobro.</p>
          <div className="mt-3 flex gap-2">
            <button className="rounded bg-emerald-700 px-4 py-2 text-white" onClick={() => feedback.mutate({ useful: true, best_response: true })} type="button">
              Marcar como útil e melhor resposta
            </button>
            <button className="rounded border border-red-300 px-4 py-2 text-red-700" onClick={() => feedback.mutate({ useful: false, best_response: false })} type="button">
              Não ajudou
            </button>
          </div>
        </Panel>
      ) : null}
      {feedback.error ? <p className="text-sm text-red-700">{getErrorMessage(feedback.error)}</p> : null}
      {feedback.data ? (
        <Panel className="border-2 border-emerald-200 bg-emerald-50">
          <p className="font-medium text-emerald-800">{feedback.data.message}</p>
          <p className="text-sm text-ink/80">
            XP concedido ao respondente: {feedback.data.xp_awarded_to_responder}
            {feedback.data.coop_bonus_applied ? " (bonus coop aplicado)" : ""}
          </p>
        </Panel>
      ) : null}
    </div>
  );
}
