import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Panel } from "../components/common/Panel";
import { getMyChallenges } from "../services/contentService";

export function ChallengesPage() {
  const query = useQuery({ queryKey: ["my-challenges"], queryFn: getMyChallenges });

  if (query.isPending) return <LoadingState label="Carregando desafios..." />;
  if (query.isError) return <ErrorState message="Falha ao carregar desafios." />;

  const completedCount = query.data.items.filter((challenge) => challenge.completed).length;

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Desafios de aprendizagem</h1>
      <Panel className="border-2 border-sky-100 bg-white">
        <p>
          Cada desafio acompanha uma lição. Leia o conteúdo e conclua o quiz para registrar o desafio e receber XP uma vez.
        </p>
        <p className="mt-2 text-sm text-ink/70">
          Progresso: {completedCount} de {query.data.items.length} desafios concluídos.
        </p>
      </Panel>

      {query.data.items.length === 0 ? (
        <Panel>
          <p className="text-sm text-ink/70">Ainda não há desafios disponíveis.</p>
        </Panel>
      ) : null}

      {query.data.items.map((challenge) => (
        <Panel key={challenge.id} className={challenge.completed ? "border-2 border-emerald-200 bg-emerald-50" : ""}>
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="font-semibold">{challenge.title}</h2>
              <p className="mt-1 text-sm text-ink/70">Lição: {challenge.lesson_title}</p>
            </div>
            <span className="rounded-full bg-sky-50 px-3 py-1 text-sm">
              {challenge.completed ? "Concluído" : "Ainda não concluído"}
            </span>
          </div>

          <p className="mt-2 text-sm">Recompensa: {challenge.xp_reward} XP</p>
          {challenge.safety_notes.length ? (
            <ul className="mt-2 list-inside list-disc text-sm text-ink/70">
              {challenge.safety_notes.map((note) => <li key={note}>{note}</li>)}
            </ul>
          ) : null}

          {!challenge.completed ? (
            <Link
              to={challenge.quiz_id ? `/quizzes/${challenge.quiz_id}` : `/lessons/${challenge.lesson_id}`}
              className="mt-3 inline-block rounded bg-ink px-4 py-2 text-sm text-white"
            >
              Continuar lição
            </Link>
          ) : null}
        </Panel>
      ))}
    </div>
  );
}
