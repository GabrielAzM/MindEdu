import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { Panel } from "../../components/common/Panel";
import {
  approveUserSignup,
  getAdminReports,
  getPendingApprovals,
  rejectUserSignup,
  resolveAdminReport,
} from "../../services/adminService";

export function AdminModerationPage() {
  const queryClient = useQueryClient();
  const [rejectReason, setRejectReason] = useState("Dados inconsistentes");

  const reportsQuery = useQuery({ queryKey: ["admin-reports"], queryFn: getAdminReports });
  const approvalsQuery = useQuery({ queryKey: ["admin-approvals"], queryFn: () => getPendingApprovals("pending") });

  const resolveMutation = useMutation({
    mutationFn: (reportId: number) => resolveAdminReport(reportId, { resolution: "action_taken", note: "conteúdo removido" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-reports"] }),
  });

  const approveMutation = useMutation({
    mutationFn: (userId: string) => approveUserSignup(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-approvals"] });
      queryClient.invalidateQueries({ queryKey: ["admin-metrics"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ userId, reason }: { userId: string; reason: string }) => rejectUserSignup(userId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-approvals"] });
      queryClient.invalidateQueries({ queryKey: ["admin-metrics"] });
    },
  });

  if (reportsQuery.isPending || approvalsQuery.isPending) return <LoadingState label="Carregando moderação..." />;
  if (reportsQuery.isError || approvalsQuery.isError) return <ErrorState message="Falha ao carregar moderação." />;

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Administração - Moderação</h1>

      <Panel className="border-2 border-amber-200 bg-amber-50">
        <h2 className="font-semibold">Aprovação de novos cadastros</h2>
        <p className="mt-1 text-sm text-ink/70">Usuários padrão não acessam o app até serem aprovados.</p>
        <div className="mt-3 space-y-2">
          {approvalsQuery.data.items.length === 0 ? <p className="text-sm">Nenhum cadastro pendente.</p> : null}
          {approvalsQuery.data.items.map((user) => (
            <div key={user.id} className="rounded border border-amber-200 bg-white p-3">
              <p className="font-semibold">{user.username}</p>
              <p className="text-sm text-ink/70">
                {user.user_id} | {user.email}
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <button className="rounded bg-emerald-700 px-3 py-1 text-sm text-white" onClick={() => approveMutation.mutate(user.user_id)} type="button">
                  Aprovar
                </button>
                <button
                  className="rounded border border-red-300 px-3 py-1 text-sm text-red-700"
                  onClick={() => rejectMutation.mutate({ userId: user.user_id, reason: rejectReason })}
                  type="button"
                >
                  Rejeitar
                </button>
                <input
                  className="rounded border p-1 text-sm"
                  value={rejectReason}
                  onChange={(event) => setRejectReason(event.target.value)}
                  placeholder="Motivo da rejeição"
                />
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel>
        <h2 className="font-semibold">Denúncias</h2>
        <div className="mt-3 space-y-2">
          {reportsQuery.data.items.map((item: any) => (
            <div key={item.id} className="rounded border border-sky-100 p-3">
              <p>
                #{item.id} {item.target_type} - {item.reason} ({item.status})
              </p>
              {item.status === "open" ? (
                <button className="mt-2 rounded bg-ink px-3 py-1 text-white" onClick={() => resolveMutation.mutate(item.id)} type="button">
                  Resolver
                </button>
              ) : null}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
