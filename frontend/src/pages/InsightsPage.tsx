import { useQuery } from "@tanstack/react-query";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Panel } from "../components/common/Panel";
import { getInsights } from "../services/emotionsService";

export function InsightsPage() {
  const query = useQuery({ queryKey: ["insights"], queryFn: getInsights });

  if (query.isPending) return <LoadingState label="Gerando insights..." />;
  if (query.isError) return <ErrorState message="Falha ao carregar insights." />;

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Insights</h1>
      <Panel>
        <p className="font-semibold">Emocoes mais frequentes:</p>
        <p>{query.data.top_emotions.join(", ") || "-"}</p>
      </Panel>
      <Panel>
        <p className="font-semibold">Padrao semanal:</p>
        <p>{query.data.weekly_pattern}</p>
      </Panel>
      <Panel>
        <p className="font-semibold">O que ajuda:</p>
        <p>{query.data.what_helps.join(", ") || "-"}</p>
      </Panel>
    </div>
  );
}
