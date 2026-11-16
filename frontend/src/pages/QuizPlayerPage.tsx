import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Panel } from "../components/common/Panel";
import { getQuiz, submitQuizAttempt } from "../services/contentService";

export function QuizPlayerPage() {
  const { id } = useParams();
  const quizId = Number(id ?? 1);
  const queryClient = useQueryClient();

  const quizQuery = useQuery({ queryKey: ["quiz", quizId], queryFn: () => getQuiz(quizId) });
  const [answers, setAnswers] = useState<Record<number, number>>({});

  const mutation = useMutation({
    mutationFn: (payload: Array<{ question_id: number; option_id: number }>) => submitQuizAttempt(quizId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["home-dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["my-profile"] });
    },
  });

  const payloadAnswers = useMemo(
    () => Object.entries(answers).map(([questionId, optionId]) => ({ question_id: Number(questionId), option_id: Number(optionId) })),
    [answers]
  );

  if (quizQuery.isPending) return <LoadingState label="Carregando quiz..." />;
  if (quizQuery.isError) return <ErrorState message="Falha ao carregar quiz." />;

  const hasSubmitted = Boolean(mutation.data);
  const feedbackMap = new Map<number, string>();
  mutation.data?.feedback.forEach((item) => feedbackMap.set(item.question_id, item.explanation));

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">{quizQuery.data.title}</h1>
      {quizQuery.data.lesson_context.length > 0 ? (
        <Panel className="border-2 border-sky-200 bg-sky-50">
          <p className="text-xs uppercase text-ink/60">Resumo da lição antes do quiz</p>
          <h2 className="mt-1 font-semibold">{quizQuery.data.lesson_title ?? "Lição"}</h2>
          <div className="mt-2 space-y-1 text-sm text-ink/80">
            {quizQuery.data.lesson_context.map((line, idx) => (
              <p key={`ctx-${idx}`}>{line}</p>
            ))}
          </div>
        </Panel>
      ) : null}
      {!hasSubmitted ? (
        <>
          {quizQuery.data.questions.map((question, index) => (
            <Panel key={question.id}>
              <p className="font-semibold">
                {index + 1}. {question.prompt}
              </p>
              <div className="mt-2 space-y-2">
                {question.options.map((option) => (
                  <label key={option.id} className="flex cursor-pointer items-center gap-2 rounded border border-sky-100 p-2 hover:bg-sky-50">
                    <input
                      type="radio"
                      name={`q-${question.id}`}
                      checked={answers[question.id] === option.id}
                      onChange={() => setAnswers((prev) => ({ ...prev, [question.id]: option.id }))}
                    />
                    <span>{option.text}</span>
                  </label>
                ))}
              </div>
            </Panel>
          ))}
          <Panel>
            <button
              className="rounded bg-ink px-4 py-2 text-white"
              onClick={() => mutation.mutate(payloadAnswers)}
              type="button"
              disabled={mutation.isPending || payloadAnswers.length !== quizQuery.data.questions.length}
            >
              {mutation.isPending ? "Enviando..." : "Enviar tentativa"}
            </button>
            {payloadAnswers.length !== quizQuery.data.questions.length ? (
              <p className="mt-2 text-sm text-ink/70">Responda todas as perguntas para enviar.</p>
            ) : null}
            {mutation.isError ? <p className="mt-2 text-sm text-red-700">Falha ao enviar tentativa.</p> : null}
          </Panel>
        </>
      ) : null}
      {mutation.data ? (
        <Panel className="border-2 border-emerald-200 bg-emerald-50">
          <p className="text-sm font-semibold text-emerald-800">Tentativa enviada com sucesso.</p>
          <p className="font-semibold">
            Resultado: {mutation.data.score}/{mutation.data.max_score} - {mutation.data.passed ? "Aprovado" : "Tente novamente"}
          </p>
          <p className="text-sm text-ink/70">XP ganho: {mutation.data.xp_awarded}</p>
          <p className="text-sm text-ink/70">
            Tentativa #{mutation.data.attempt_number} | melhor nota: {mutation.data.best_score}
          </p>
          <p className="text-sm text-ink/70">{mutation.data.xp_reason}</p>
          {mutation.data.completion_message ? <p className="text-sm font-medium text-emerald-800">{mutation.data.completion_message}</p> : null}
          {(mutation.data.lesson_completed || mutation.data.challenge_completed || mutation.data.trail_completed) ? (
            <div className="text-sm text-ink/80">
              <p>
                Lição concluída: {mutation.data.lesson_completed ? "sim" : "não"} | desafio concluído: {mutation.data.challenge_completed ? "sim" : "não"} |
                trilha concluída: {mutation.data.trail_completed ? "sim" : "não"}
              </p>
              {mutation.data.next_lesson_id ? (
                <Link to={`/lessons/${mutation.data.next_lesson_id}`} className="mt-2 inline-block rounded bg-ink px-3 py-1 text-white">
                  Próxima lição sugerida
                </Link>
              ) : (
                <Link to="/trails" className="mt-2 inline-block rounded bg-ink px-3 py-1 text-white">
                  Ver nova trilha sugerida
                </Link>
              )}
            </div>
          ) : null}
          {mutation.data.feedback.length > 0 ? (
            <div className="mt-2 space-y-1">
              <p className="text-sm font-medium">Pontos para revisar:</p>
              {quizQuery.data.questions.map((question, index) =>
                feedbackMap.has(question.id) ? (
                  <p key={question.id} className="text-sm text-amber-700">
                    {index + 1}. {feedbackMap.get(question.id)}
                  </p>
                ) : null
              )}
            </div>
          ) : null}
          {!mutation.data.passed ? (
            <button
              className="mt-3 rounded border border-ink px-3 py-1 text-ink"
              type="button"
              onClick={() => {
                mutation.reset();
                setAnswers({});
              }}
            >
              Refazer quiz
            </button>
          ) : null}
        </Panel>
      ) : null}
    </div>
  );
}
