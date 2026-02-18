import { useQuery } from "@tanstack/react-query";

import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { Panel } from "../../components/common/Panel";
import { getAudit } from "../../services/adminService";

export function AdminAuditPage() {
  const query = useQuery({ queryKey: ["admin-audit"], queryFn: getAudit });

  if (query.isPending) return <LoadingState label="Carregando auditoria..." />;
  if (query.isError) return <ErrorState message="Falha ao carregar auditoria." />;

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Admin - Auditoria</h1>
      {query.data.items.map((item: any) => (
        <Panel key={item.id}>
          <p className="text-sm">
            {item.created_at} - {item.action} ({item.entity_type}:{item.entity_id})
          </p>
        </Panel>
      ))}
    </div>
  );
}
