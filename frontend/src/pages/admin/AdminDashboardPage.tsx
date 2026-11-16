import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { Panel } from "../../components/common/Panel";
import { adminUserAction, deleteAdminUser, getAdminUserProgress, getMetrics, getPendingApprovals } from "../../services/adminService";
import { formatMindEduLabel } from "../../lib/mindEduLabels";

export function AdminDashboardPage() {
  const queryClient = useQueryClient();
  const [searchUser, setSearchUser] = useState("");
  const [selectedProgressUserId, setSelectedProgressUserId] = useState<string | null>(null);
  const [actionReason, setActionReason] = useState("Solicitação administrativa");
  const [actionResultByUser, setActionResultByUser] = useState<Record<string, string>>({});

  const metricsQuery = useQuery({ queryKey: ["admin-metrics"], queryFn: getMetrics });
  const approvalsQuery = useQuery({ queryKey: ["admin-approvals-dashboard"], queryFn: () => getPendingApprovals("pending") });
  const usersQuery = useQuery({ queryKey: ["admin-users-all"], queryFn: () => getPendingApprovals("all") });
  const progressQuery = useQuery({
    queryKey: ["admin-user-progress", selectedProgressUserId],
    queryFn: () => getAdminUserProgress(selectedProgressUserId as string),
    enabled: Boolean(selectedProgressUserId),
  });

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
        [userId]: `Usuário ${result.deleted_user_id} excluído.`,
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
          <p className="text-xs uppercase text-ink/60">Usuários</p>
          <p className="text-2xl font-bold">{metrics.users_total}</p>
        </Panel>
        <Panel>
          <p className="text-xs uppercase text-ink/60">Ativos 7d</p>
          <p className="text-2xl font-bold">{metrics.active_7d}</p>
        </Panel>
        <Panel>
          <p className="text-xs uppercase text-ink/60">Aprovações pend.</p>
          <p className="text-2xl font-bold">{metrics.approvals_pending}</p>
        </Panel>
        <Panel>
          <p className="text-xs uppercase text-ink/60">Denúncias abertas</p>
          <p className="text-2xl font-bold">{metrics.reports_open}</p>
        </Panel>
        <Panel>
          <p className="text-xs uppercase text-ink/60">Feedback útil</p>
          <p className="text-2xl font-bold">{metrics.useful_feedback}</p>
        </Panel>
      </div>

      <Panel className="border-2 border-amber-200 bg-amber-50">
        <h2 className="font-semibold">Fila de aprovação de usuários</h2>
        {pending.length === 0 ? <p className="mt-2 text-sm">Sem usuários pendentes.</p> : null}
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
            Abrir painel de aprovação/moderação
          </Link>
          <Link to="/admin/metrics" className="rounded border border-ink px-3 py-2 text-sm text-ink">
            Ver métricas detalhadas
          </Link>
        </div>
      </Panel>

      <Panel>
        <h2 className="font-semibold">Acesso rápido de gerenciamento</h2>
        <p className="mt-1 text-sm text-ink/70">Todos os processos administrativos em um único card.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link to="/admin/moderation" className="rounded bg-ink px-3 py-2 text-sm text-white">
            Aprovações e moderação
          </Link>
          <Link to="/admin/content" className="rounded border border-ink px-3 py-2 text-sm text-ink">
            Conteúdo (trilhas/quizzes)
          </Link>
          <Link to="/admin/metrics" className="rounded border border-ink px-3 py-2 text-sm text-ink">
            Métricas
          </Link>
          <Link to="/admin/audit" className="rounded border border-ink px-3 py-2 text-sm text-ink">
            Auditoria
          </Link>
        </div>
      </Panel>

      <Panel className="border-2 border-sky-200 bg-sky-50">
        <h2 className="font-semibold">Gestão de contas de usuários</h2>
        <p className="mt-1 text-sm text-ink/70">Ações disponíveis: excluir usuário, redefinir senha e redefinir user_id.</p>
        <p className="mt-1 text-xs text-ink/70">O acompanhamento exibe progresso educativo e não mostra o conteúdo dos check-ins.</p>
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
            placeholder="Motivo da ação"
          />
        </div>

        <div className="mt-3 space-y-2">
          {managedUsers.length === 0 ? <p className="text-sm text-ink/70">Nenhum usuário encontrado.</p> : null}
          {managedUsers.map((user) => {
            const busy =
              resetPasswordMutation.isPending || resetUserIdMutation.isPending || deleteUserMutation.isPending;
            return (
              <div key={user.id} className="rounded border border-sky-200 bg-white p-3">
                <p className="font-semibold">
                  {user.username} ({user.user_id})
                </p>
                <p className="text-xs text-ink/70">
                  {user.email} | aprovação: {user.approval_status} | status: {user.account_status}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    className="rounded border border-emerald-700 px-3 py-1 text-sm text-emerald-800"
                    type="button"
                    onClick={() => setSelectedProgressUserId((current) => current === user.user_id ? null : user.user_id)}
                  >
                    {selectedProgressUserId === user.user_id ? "Ocultar progresso" : "Acompanhar progresso"}
                  </button>
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
                        `Excluir o usuário ${user.user_id}? Essa ação remove dados vinculados.`
                      );
                      if (confirmed) deleteUserMutation.mutate(user.user_id);
                    }}
                    disabled={busy}
                  >
                    Excluir usuário
                  </button>
                </div>
                {selectedProgressUserId === user.user_id ? (
                  <div className="mt-3 rounded border border-emerald-200 bg-emerald-50 p-3">
                    {progressQuery.isPending ? <p className="text-sm">Carregando progresso educativo...</p> : null}
                    {progressQuery.isError ? <p className="text-sm text-red-700">Falha ao carregar o progresso educativo.</p> : null}
                    {progressQuery.data ? (
                      <>
                        <p className="font-semibold">
                          Nível {progressQuery.data.xp.level} · {progressQuery.data.xp.total} XP · Mascote {progressQuery.data.mascot.stage}/{progressQuery.data.mascot.max_stage}
                        </p>
                        <div className="mt-2 grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
                          <p>Lições concluídas: {progressQuery.data.progress.lessons_completed}</p>
                          <p>Quizzes aprovados: {progressQuery.data.progress.quizzes_passed}</p>
                          <p>Desafios concluídos: {progressQuery.data.progress.challenges_completed}</p>
                          <p>Missões criadas: {progressQuery.data.progress.missions_created}</p>
                          <p>Respostas úteis: {progressQuery.data.progress.helpful_responses}</p>
                        </div>
                        <p className="mt-2 text-sm">
                          Habilidades: {Object.entries(progressQuery.data.skills)
                            .map(([skill, value]) => `${formatMindEduLabel(skill)} ${value}`)
                            .join(" · ")}
                        </p>
                        <p className="mt-2 text-xs text-ink/70">
                          XP recente: {progressQuery.data.recent_xp.filter((entry) => entry.xp > 0)
                            .map((entry) => `${entry.day}: ${entry.xp}`)
                            .join(" · ") || "sem ganhos nesta semana"}
                        </p>
                      </>
                    ) : null}
                  </div>
                ) : null}
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
