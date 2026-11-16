import { useQuery } from "@tanstack/react-query";

import { MetricsBarChart } from "../../components/charts/MetricsBarChart";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { getMetrics } from "../../services/adminService";

export function AdminMetricsPage() {
  const query = useQuery({ queryKey: ["admin-metrics"], queryFn: getMetrics });

  if (query.isPending) return <LoadingState label="Carregando métricas..." />;
  if (query.isError) return <ErrorState message="Falha ao carregar métricas." />;

  const chartData = [
    { name: "Usuários", value: query.data.users_total },
    { name: "Ativos 7d", value: query.data.active_7d },
    { name: "Aprovações pend.", value: query.data.approvals_pending },
    { name: "Denúncias abertas", value: query.data.reports_open },
    { name: "Feedback útil", value: query.data.useful_feedback },
  ];

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Admin - Métricas</h1>
      <MetricsBarChart data={chartData} />
    </div>
  );
}
