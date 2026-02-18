import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Panel } from "../components/common/Panel";
import { getMyTrails } from "../services/progressService";
import { getMissionInbox } from "../services/uxuService";

export function TrailsPage() {
  const trailsQuery = useQuery({ queryKey: ["my-trails"], queryFn: getMyTrails });
  const missionInboxQuery = useQuery({ queryKey: ["mission-inbox"], queryFn: getMissionInbox });

  if (trailsQuery.isPending) return <LoadingState label="Carregando trilhas..." />;
  if (trailsQuery.isError) return <ErrorState message="Falha ao carregar trilhas." />;

  const baseTrails = trailsQuery.data.items.filter((trail) => !trail.is_generated);
  const generatedTrails = trailsQuery.data.items.filter((trail) => trail.is_generated);

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Trilhas</h1>

      {missionInboxQuery.data?.items.length ? (
        <Panel className="border-2 border-emerald-200 bg-emerald-50">
          <h2 className="text-lg font-semibold">Missoes de cooperacao recebidas</h2>
          <div className="mt-2 space-y-2">
            {missionInboxQuery.data.items.map((mission) => (
              <div key={`inbox-${mission.id}`} className="rounded border border-emerald-200 bg-white p-3">
                <p className="font-medium">{mission.message}</p>
                <p className="text-sm text-ink/70">
                  #{mission.id} - {mission.category} ({mission.intensity}/5) | precisa de: {mission.want_now}
                </p>
                <Link to={`/coop/missions/${mission.id}`} className="mt-2 inline-block rounded bg-ink px-3 py-1 text-sm text-white">
                  Abrir missao coop
                </Link>
              </div>
            ))}
          </div>
        </Panel>
      ) : null}
      {missionInboxQuery.isError ? <ErrorState message="Falha ao carregar missoes de cooperacao." /> : null}

      {baseTrails.map((trail) => (
        <Panel key={`base-${trail.id}`}>
          <h2 className="text-lg font-semibold">{trail.title}</h2>
          <p className="mt-1 text-sm text-ink/70">{trail.description}</p>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <span>{trail.lesson_count} licoes</span>
            {trail.first_lesson_id ? (
              <Link to={`/lessons/${trail.first_lesson_id}`} className="rounded bg-ink px-3 py-1 text-white">
                Abrir primeira licao
              </Link>
            ) : null}
          </div>
        </Panel>
      ))}

      <h2 className="pt-2 text-xl font-semibold">Trilhas geradas pelo seu XP</h2>
      {generatedTrails.length === 0 ? (
        <Panel>
          <p className="text-sm text-ink/70">Ganhe XP em quizzes, check-ins e cooperacao para desbloquear trilhas dinamicas.</p>
        </Panel>
      ) : null}
      {generatedTrails.map((trail) => (
        <Panel key={`generated-${trail.id}`} className="border-2 border-amber-200 bg-amber-50">
          <p className="text-xs font-semibold uppercase text-amber-900">Gerada automaticamente</p>
          <h3 className="mt-1 text-lg font-bold">{trail.title}</h3>
          <p className="text-sm text-ink/70">{trail.description}</p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="rounded-full bg-white px-2 py-1">dificuldade: {trail.difficulty}</span>
            {trail.focus_tags.map((tag) => (
              <span key={`${trail.id}-${tag}`} className="rounded-full bg-white px-2 py-1">
                {tag}
              </span>
            ))}
          </div>
          {trail.lessons_preview?.length ? (
            <div className="mt-3 space-y-1 rounded border border-amber-200 bg-white p-2 text-sm">
              <p className="font-medium">Roteiro desta trilha:</p>
              {trail.lessons_preview.map((lesson, idx) => (
                <p key={`${trail.id}-${lesson.id}`}>
                  {idx + 1}. {lesson.title}
                </p>
              ))}
              {trail.mission_suggestion ? <p className="text-xs text-ink/70">Missao sugerida: {trail.mission_suggestion}</p> : null}
            </div>
          ) : null}
          <div className="mt-3">
            {trail.first_lesson_id ? (
              <Link to={`/lessons/${trail.first_lesson_id}`} className="rounded bg-ink px-3 py-1 text-sm text-white">
                Iniciar trilha gerada
              </Link>
            ) : (
              <p className="text-xs text-ink/70">Esta trilha sera liberada na proxima atualizacao de XP.</p>
            )}
          </div>
        </Panel>
      ))}
    </div>
  );
}
