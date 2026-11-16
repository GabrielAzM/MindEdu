import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from "recharts";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Panel } from "../components/common/Panel";
import { getDashboard } from "../services/progressService";
import { useAuthStore } from "../store/authStore";

export function HomePage() {
  const user = useAuthStore((s) => s.user);
  const dashboardQuery = useQuery({ queryKey: ["home-dashboard"], queryFn: getDashboard });

  if (dashboardQuery.isPending) return <LoadingState label="Preparando dashboard gamificado..." />;
  if (dashboardQuery.isError) return <ErrorState message="Falha ao carregar dashboard." />;

  const dashboard = dashboardQuery.data;
  const xpPercent = Math.min(100, Math.round((dashboard.headline.xp_total % 100) * 1));

  const skillData = Object.entries(dashboard.skills).map(([name, value]) => ({
    name,
    value,
  }));

  const cardClass =
    "rounded-2xl border border-sky-100 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow";

  return (
    <div className="space-y-5">
      <Panel className="border-0 bg-gradient-to-r from-amber-100 via-lime-100 to-cyan-100 p-6">
        <h1 className="font-heading text-3xl font-bold">Bem-vindo(a), {user?.username}</h1>
        <p className="mt-2 text-sm text-ink/70">
          O MindEdu é educativo e não oferece diagnóstico clínico. Use-o com o acompanhamento de um educador ou adulto de confiança. Hoje você está no nível {dashboard.headline.level} ({dashboard.headline.tier}).
        </p>
        <div className="mt-4">
          <div className="mb-1 flex items-center justify-between text-sm font-medium">
            <span>XP Total: {dashboard.headline.xp_total}</span>
            <span>Faltam {dashboard.headline.xp_to_next} XP para o próximo nível</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-white/70">
            <div className="h-full rounded-full bg-ink" style={{ width: `${xpPercent}%` }} />
          </div>
        </div>
      </Panel>

      <div className="grid gap-4 md:grid-cols-4">
        <Link to="/trails" className={cardClass}>
          <p className="text-xs uppercase text-ink/60">Trilhas concluídas</p>
          <p className="mt-1 text-2xl font-bold">{dashboard.stats.trails_completed}</p>
        </Link>
        <Link to="/checkin" className={cardClass}>
          <p className="text-xs uppercase text-ink/60">Lições concluídas</p>
          <p className="mt-1 text-2xl font-bold">{dashboard.stats.lessons_completed}</p>
        </Link>
        <Link to="/coop" className={cardClass}>
          <p className="text-xs uppercase text-ink/60">Ajudas úteis</p>
          <p className="mt-1 text-2xl font-bold">{dashboard.stats.helpful_responses}</p>
        </Link>
        <Link to="/mascot" className={cardClass}>
          <p className="text-xs uppercase text-ink/60">Evolução mascote</p>
          <p className="mt-1 text-2xl font-bold">{dashboard.mascot.stage}/4</p>
          <p className="mt-1 text-xs text-ink/70">4/4 e atingido com 70 XP totais.</p>
        </Link>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-semibold">XP da semana</h2>
          <div className="mt-3 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dashboard.recent_xp}>
                <defs>
                  <linearGradient id="xpFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1d4ed8" stopOpacity={0.45} />
                    <stop offset="95%" stopColor="#1d4ed8" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Area type="monotone" dataKey="xp" stroke="#1d4ed8" fill="url(#xpFill)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel>
          <h2 className="font-semibold">Habilidades do mascote</h2>
          <div className="mt-3 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={skillData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="name" />
                <PolarRadiusAxis />
                <Radar name="skills" dataKey="value" stroke="#0f766e" fill="#14b8a6" fillOpacity={0.35} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      {dashboard.next_generated_trail ? (
        <Panel className="border-2 border-amber-200 bg-amber-50">
          <p className="text-xs font-semibold uppercase text-amber-900">Nova trilha gerada pelo seu XP</p>
          <h2 className="mt-1 text-xl font-bold">{dashboard.next_generated_trail.title}</h2>
          <p className="mt-1 text-sm text-ink/70">{dashboard.next_generated_trail.description}</p>
          <div className="mt-3 flex gap-2">
            <Link to="/trails" className="rounded-lg border border-ink px-3 py-2 text-sm text-ink">
              Ver trilhas
            </Link>
            {dashboard.next_generated_trail.first_lesson_id ? (
              <Link
                to={`/lessons/${dashboard.next_generated_trail.first_lesson_id}`}
                className="rounded-lg bg-ink px-3 py-2 text-sm text-white"
              >
                Iniciar agora
              </Link>
            ) : null}
          </div>
        </Panel>
      ) : null}
    </div>
  );
}
