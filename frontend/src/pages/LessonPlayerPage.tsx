import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Panel } from "../components/common/Panel";
import { getLesson } from "../services/contentService";

export function LessonPlayerPage() {
  const { id } = useParams();
  const lessonId = Number(id ?? 1);

  const lessonQuery = useQuery({ queryKey: ["lesson", lessonId], queryFn: () => getLesson(lessonId) });

  if (lessonQuery.isPending) return <LoadingState label="Carregando lição..." />;
  if (lessonQuery.isError) return <ErrorState message="Falha ao carregar lição." />;

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">{lessonQuery.data.title}</h1>
      {lessonQuery.data.cards.map((card, idx) => (
        <Panel key={`${card.type}-${idx}`}>
          <p className="text-xs uppercase text-ink/50">{card.type}</p>
          <p className="mt-1">{card.text}</p>
        </Panel>
      ))}
      <div className="flex flex-wrap gap-2">
        {lessonQuery.data.quiz_id ? (
          <Link to={`/quizzes/${lessonQuery.data.quiz_id}`} className="inline-block rounded bg-ink px-4 py-2 text-white">
            Ir para quiz
          </Link>
        ) : null}
      </div>
      <p className="text-sm text-ink/70">A conclusão e automática ao enviar o quiz desta lição.</p>
    </div>
  );
}
