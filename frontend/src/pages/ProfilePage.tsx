import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Panel } from "../components/common/Panel";
import { useMascotAssets } from "../components/pixi/useMascotAssets";
import { getMyProfile } from "../services/progressService";
import { mascotCatalog, useMascotStore } from "../store/mascotStore";

export function ProfilePage() {
  const mascotId = useMascotStore((s) => s.mascotId);
  const mascotName = mascotCatalog[mascotId].name;
  const assets = useMascotAssets(mascotId);
  const profileQuery = useQuery({ queryKey: ["my-profile"], queryFn: getMyProfile });

  if (profileQuery.isPending) return <LoadingState label="Carregando perfil..." />;
  if (profileQuery.isError) return <ErrorState message="Falha ao carregar perfil." />;

  const profile = profileQuery.data;
  const stage = Math.max(1, Math.min(4, profile.mascot.stage)) as 1 | 2 | 3 | 4;
  const mascotMaxReached = profile.xp.total >= 70 || stage >= 4;

  const bars = [
    { name: "Trilhas", value: profile.progress.trails_completed },
    { name: "Licoes", value: profile.progress.lessons_completed },
    { name: "Quizzes", value: profile.progress.quizzes_passed },
    { name: "Ajudas", value: profile.progress.helpful_responses },
    { name: "Coop", value: profile.progress.coop_pairs_active },
  ];

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Perfil</h1>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <Panel>
          <div className="grid gap-2 md:grid-cols-2">
            <p>
              <span className="font-semibold">user_id:</span> {profile.user.user_id}
            </p>
            <p>
              <span className="font-semibold">username:</span> {profile.user.username}
            </p>
            <p>
              <span className="font-semibold">status:</span> {profile.user.status}
            </p>
            <p>
              <span className="font-semibold">faixa:</span> {profile.xp.tier}
            </p>
          </div>
          <div className="mt-4 h-3 overflow-hidden rounded-full bg-sky-100">
            <div className="h-full rounded-full bg-ink" style={{ width: `${Math.min(100, (profile.xp.current_level_xp / profile.xp.next_level_xp) * 100)}%` }} />
          </div>
          <p className="mt-2 text-sm text-ink/70">
            Nivel {profile.xp.level} - XP {profile.xp.total} (faltam {profile.xp.xp_to_next} XP para o proximo nivel)
          </p>
        </Panel>

        <Panel>
          <p className="text-xs uppercase text-ink/60">Mascote atual ({mascotName})</p>
          <img
            src={assets.evolutions[stage]}
            alt={`Evolucao ${stage} do mascote ${mascotId}`}
            className="mt-2 h-48 w-full rounded-xl border border-sky-100 object-contain"
          />
          <p className="mt-2 text-sm font-medium">Evolucao {stage}/4</p>
          <p className="text-xs text-ink/70">Regra de evolucao: 10, 30, 50 e 70 XP.</p>
          <p className="text-xs text-ink/70">
            XP atual: {profile.xp.total} {mascotMaxReached ? "| maximo 4/4 atingido" : ""}
          </p>
        </Panel>
      </div>

      <Panel>
        <h2 className="font-semibold">Progresso geral</h2>
        <div className="mt-3 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bars}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#0f766e" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </div>
  );
}
