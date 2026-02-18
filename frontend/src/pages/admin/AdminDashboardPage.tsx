import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { Panel } from "../../components/common/Panel";
import { adminUserAction, deleteAdminUser, getMetrics, getPendingApprovals } from "../../services/adminService";

export function AdminDashboardPage() {
  const queryClient = useQueryClient();
  const [searchUser, setSearchUser] = useState("");
  const [actionReason, setActionReason] = useState("Solicitacao administrativa");
  const [actionResultByUser, setActionResultByUser] = useState<Record<string, string>>({});

  const metricsQuery = useQuery({ queryKey: ["admin-metrics"], queryFn: getMetrics });
  const approvalsQuery = useQuery({ queryKey: ["admin-approvals-dashboard"], queryFn: () => getPendingApprovals("pending") });
  const usersQuery = useQuery({ queryKey: ["admin-users-all"], queryFn: () => getPendingApprovals("all") });

  const refreshUsers = () => {
    queryClient.invalidateQueries({ queryKey: ["admin-approvals"] });
    queryClient.invalidateQueries({ queryKey: ["admin-approvals-dashboard"] });
    queryClient.invalidateQueries({ queryKey: ["admin-users-all"] });
    queryClient.invalidateQueries({ queryKey: ["admin-metrics"] });
  };

  const resetPasswordMutation = useMutation({
    mutationFn: (userId: string) =>
      adminUserAction(userId, {
        action: "reset_password",
        reason: actionReason,
      }),
    onSuccess: (result, userId) => {
      const message = result.temporary_password
        ? `Senha provisoria: ${result.temporary_password}`
        : "Senha redefinida.";
      setActionResultByUser((prev) => ({ ...prev, [userId]: message }));
      refreshUsers();
    },
  });

  const resetUserIdMutation = useMutation({
    mutationFn: (userId: string) =>
      adminUserAction(userId, {
        action: "reset_user_id",
        reason: actionReason,
      }),
    onSuccess: (result, userId) => {
      const message = result.new_user_id
        ? `Novo user_id: ${result.new_user_id}`
        : "ID redefinido.";
      setActionResultByUser((prev) => ({ ...prev, [userId]: message }));
      refreshUsers();
    },
  });

  const deleteUserMutation = useMutation({
    mutationFn: (userId: string) => deleteAdminUser(userId, actionReason),
    onSuccess: (result, userId) => {
      setActionResultByUser((prev) => ({
        ...prev,
        [userId]: `Usuario ${result.deleted_user_id} excluido.`,
      }));
      refreshUsers();
    },
  });

  if (metricsQuery.isPending || approvalsQuery.isPending || usersQuery.isPending) {
    return <LoadingState label="Carregando painel admin..." />;
  }
  if (metricsQuery.isError || approvalsQuery.isError || usersQuery.isError) {
    return <ErrorState message="Falha ao carregar dashboard admin." />;
  }

  const pending = approvalsQuery.data.items;
  const metrics = metricsQuery.data;
  const managedUsers = usersQuery.data.items
    .filter((user) => {
      const haystack = `${user.user_id} ${user.username} ${user.email}`.toLowerCase();
      return haystack.includes(searchUser.toLowerCase());
    })
    .slice(0, 20);

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Admin - Dashboard</h1>

      <div className="grid gap-3 md:grid-cols-5">
        <Panel>
          <p className="text-xs uppercase text-ink/60">Usuarios</p>
          <p className="text-2xl font-bold">{metrics.users_total}</p>
        </Panel>
        <Panel>
          <p className="text-xs uppercase text-ink/60">Ativos 7d</p>
          <p className="text-2xl font-bold">{metrics.active_7d}</p>
        </Panel>
        <Panel>
          <p className="text-xs uppercase text-ink/60">Aprovacoes pend.</p>
          <p className="text-2xl font-bold">{metrics.approvals_pending}</p>
        </Panel>
        <Panel>
          <p className="text-xs uppercase text-ink/60">Denuncias abertas</p>
          <p className="text-2xl font-bold">{metrics.reports_open}</p>
        </Panel>
        <Panel>
          <p className="text-xs uppercase text-ink/60">Feedback util</p>
          <p className="text-2xl font-bold">{metrics.useful_feedback}</p>
        </Panel>
      </div>

      <Panel className="border-2 border-amber-200 bg-amber-50">
        <h2 className="font-semibold">Fila de aprovacao de usuarios</h2>
        {pending.length === 0 ? <p className="mt-2 text-sm">Sem usuarios pendentes.</p> : null}
        <div className="mt-2 space-y-2">
          {pending.slice(0, 8).map((user) => (
            <div key={user.id} className="rounded border border-amber-200 bg-white p-2">
              <p className="font-medium">
                {user.username} ({user.user_id})
              </p>
              <p className="text-xs text-ink/70">{user.email}</p>
            </div>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link to="/admin/moderation" className="rounded bg-ink px-3 py-2 text-sm text-white">
            Abrir painel de aprovacao/moderacao
          </Link>
          <Link to="/admin/metrics" className="rounded border border-ink px-3 py-2 text-sm text-ink">
            Ver metricas detalhadas
          </Link>
        </div>
      </Panel>

      <Panel>
        <h2 className="font-semibold">Acesso rapido de gerenciamento</h2>
        <p className="mt-1 text-sm text-ink/70">Todos os processos administrativos em um unico card.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link to="/admin/moderation" className="rounded bg-ink px-3 py-2 text-sm text-white">
            Aprovacoes e moderacao
          </Link>
          <Link to="/admin/content" className="rounded border border-ink px-3 py-2 text-sm text-ink">
            Conteudo (trilhas/quizzes)
          </Link>
          <Link to="/admin/metrics" className="rounded border border-ink px-3 py-2 text-sm text-ink">
            Metricas
          </Link>
          <Link to="/admin/audit" className="rounded border border-ink px-3 py-2 text-sm text-ink">
            Auditoria
          </Link>
        </div>
      </Panel>

      <Panel className="border-2 border-sky-200 bg-sky-50">
        <h2 className="font-semibold">Gestao de contas de usuarios</h2>
        <p className="mt-1 text-sm text-ink/70">Acoes disponiveis: excluir usuario, redefinir senha e redefinir user_id.</p>
        <div className="mt-3 grid gap-2 md:grid-cols-[2fr_1fr]">
          <input
            value={searchUser}
            onChange={(event) => setSearchUser(event.target.value)}
            className="rounded border p-2"
            placeholder="Buscar por user_id, username ou email"
          />
          <input
            value={actionReason}
            onChange={(event) => setActionReason(event.target.value)}
            className="rounded border p-2"
            placeholder="Motivo da acao"
          />
        </div>

        <div className="mt-3 space-y-2">
          {managedUsers.length === 0 ? <p className="text-sm text-ink/70">Nenhum usuario encontrado.</p> : null}
          {managedUsers.map((user) => {
            const busy =
              resetPasswordMutation.isPending || resetUserIdMutation.isPending || deleteUserMutation.isPending;
            return (
              <div key={user.id} className="rounded border border-sky-200 bg-white p-3">
                <p className="font-semibold">
                  {user.username} ({user.user_id})
                </p>
                <p className="text-xs text-ink/70">
                  {user.email} | aprovacao: {user.approval_status} | status: {user.account_status}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    className="rounded bg-ink px-3 py-1 text-sm text-white"
                    type="button"
                    onClick={() => resetPasswordMutation.mutate(user.user_id)}
                    disabled={busy}
                  >
                    Redefinir senha
                  </button>
                  <button
                    className="rounded border border-ink px-3 py-1 text-sm text-ink"
                    type="button"
                    onClick={() => resetUserIdMutation.mutate(user.user_id)}
                    disabled={busy}
                  >
                    Redefinir user_id
                  </button>
                  <button
                    className="rounded border border-red-300 px-3 py-1 text-sm text-red-700"
                    type="button"
                    onClick={() => {
                      const confirmed = window.confirm(
                        `Excluir o usuario ${user.user_id}? Essa acao remove dados vinculados.`
                      );
                      if (confirmed) deleteUserMutation.mutate(user.user_id);
                    }}
                    disabled={busy}
                  >
                    Excluir usuario
                  </button>
                </div>
                {actionResultByUser[user.user_id] ? (
                  <p className="mt-2 text-xs font-medium text-emerald-800">{actionResultByUser[user.user_id]}</p>
                ) : null}
              </div>
            );
          })}
        </div>
      </Panel>
    </div>
  );
}
