import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { LoadingState } from "../components/common/LoadingState";
import { ErrorState } from "../components/common/ErrorState";
import { getCheckins } from "../services/emotionsService";
import { Panel } from "../components/common/Panel";
import { formatMindEduLabel } from "../lib/mindEduLabels";

export function CheckinHistoryPage() {
  const [range, setRange] = useState<"week" | "month">("week");
  const query = useQuery({ queryKey: ["checkins", range], queryFn: () => getCheckins(range) });

  if (query.isPending) return <LoadingState label="Carregando histórico..." />;
  if (query.isError) return <ErrorState message="Falha ao carregar histórico" />;

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Histórico de check-ins</h1>
      <div className="flex gap-2">
        <button className="rounded border px-3 py-1" onClick={() => setRange("week")} type="button">
          Semana
        </button>
        <button className="rounded border px-3 py-1" onClick={() => setRange("month")} type="button">
          Mês
        </button>
      </div>
      {query.data.items.map((item, idx) => (
        <Panel key={`${item.date}-${idx}`}>
          <p>
            {item.date} - {formatMindEduLabel(item.emotion)} ({item.intensity}/5)
          </p>
        </Panel>
      ))}
    </div>
  );
}
