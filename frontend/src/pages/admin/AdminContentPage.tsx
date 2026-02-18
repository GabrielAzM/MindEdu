import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { Panel } from "../../components/common/Panel";
import {
  AdminQuizQuestion,
  createAdminQuiz,
  createAdminQuizOption,
  createAdminQuizQuestion,
  deleteAdminQuiz,
  deleteAdminQuizOption,
  deleteAdminQuizQuestion,
  getAdminQuizQuestions,
  getAdminQuizzes,
  getAdminTrails,
  updateAdminQuiz,
  updateAdminQuizOption,
  updateAdminQuizQuestion,
} from "../../services/adminService";

function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) {
      return response.data.detail;
    }
  }
  return "Falha na operacao.";
}

function QuestionCard({
  question,
  onUpdateQuestion,
  onDeleteQuestion,
  onCreateOption,
  onUpdateOption,
  onDeleteOption,
}: {
  question: AdminQuizQuestion;
  onUpdateQuestion: (questionId: number, payload: { prompt: string; explanation: string; position: number }) => void;
  onDeleteQuestion: (questionId: number) => void;
  onCreateOption: (questionId: number, payload: { option_text: string; position: number; is_correct: boolean }) => void;
  onUpdateOption: (optionId: number, payload: { option_text: string; position: number; is_correct: boolean }) => void;
  onDeleteOption: (optionId: number) => void;
}) {
  const [newOptionText, setNewOptionText] = useState("");
  const [newOptionPosition, setNewOptionPosition] = useState(question.options.length + 1);
  const [newOptionCorrect, setNewOptionCorrect] = useState(false);

  return (
    <Panel>
      <form
        className="grid gap-2 md:grid-cols-3"
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          onUpdateQuestion(question.id, {
            position: Number(form.get("position")),
            prompt: String(form.get("prompt")),
            explanation: String(form.get("explanation")),
          });
        }}
      >
        <input
          name="position"
          type="number"
          min={1}
          defaultValue={question.position}
          className="rounded border p-2"
          aria-label={`Posicao da pergunta ${question.id}`}
        />
        <input
          name="prompt"
          defaultValue={question.prompt}
          className="rounded border p-2 md:col-span-2"
          aria-label={`Prompt da pergunta ${question.id}`}
        />
        <textarea
          name="explanation"
          defaultValue={question.explanation}
          className="rounded border p-2 md:col-span-3"
          rows={2}
          aria-label={`Explicacao da pergunta ${question.id}`}
        />
        <div className="flex gap-2 md:col-span-3">
          <button className="rounded bg-ink px-3 py-1 text-sm text-white" type="submit">
            Salvar pergunta
          </button>
          <button
            className="rounded border border-red-300 px-3 py-1 text-sm text-red-700"
            type="button"
            onClick={() => onDeleteQuestion(question.id)}
          >
            Remover pergunta
          </button>
        </div>
      </form>

      <div className="mt-4 space-y-2">
        <p className="text-sm font-semibold">Opcoes</p>
        {question.options.map((option) => (
          <form
            key={option.id}
            className="grid gap-2 rounded border border-sky-100 p-2 md:grid-cols-4"
            onSubmit={(event) => {
              event.preventDefault();
              const form = new FormData(event.currentTarget);
              onUpdateOption(option.id, {
                position: Number(form.get("position")),
                option_text: String(form.get("option_text")),
                is_correct: form.get("is_correct") === "on",
              });
            }}
          >
            <input
              name="position"
              type="number"
              min={1}
              defaultValue={option.position}
              className="rounded border p-2"
              aria-label={`Posicao da opcao ${option.id}`}
            />
            <input
              name="option_text"
              defaultValue={option.option_text}
              className="rounded border p-2 md:col-span-2"
              aria-label={`Texto da opcao ${option.id}`}
            />
            <label className="flex items-center gap-2 rounded border p-2 text-sm">
              <input name="is_correct" type="checkbox" defaultChecked={option.is_correct} /> Correta
            </label>
            <div className="flex gap-2 md:col-span-4">
              <button className="rounded bg-ink px-3 py-1 text-sm text-white" type="submit">
                Salvar opcao
              </button>
              <button
                className="rounded border border-red-300 px-3 py-1 text-sm text-red-700"
                type="button"
                onClick={() => onDeleteOption(option.id)}
              >
                Remover opcao
              </button>
            </div>
          </form>
        ))}

        <form
          className="grid gap-2 rounded border border-dashed border-sky-200 p-2 md:grid-cols-4"
          onSubmit={(event) => {
            event.preventDefault();
            if (!newOptionText.trim()) return;
            onCreateOption(question.id, {
              option_text: newOptionText,
              position: newOptionPosition,
              is_correct: newOptionCorrect,
            });
            setNewOptionText("");
            setNewOptionPosition(question.options.length + 1);
            setNewOptionCorrect(false);
          }}
        >
          <input
            type="number"
            min={1}
            value={newOptionPosition}
            className="rounded border p-2"
            onChange={(event) => setNewOptionPosition(Number(event.target.value))}
            aria-label={`Nova posicao da opcao para pergunta ${question.id}`}
          />
          <input
            value={newOptionText}
            onChange={(event) => setNewOptionText(event.target.value)}
            className="rounded border p-2 md:col-span-2"
            placeholder="Nova opcao"
            aria-label={`Novo texto de opcao para pergunta ${question.id}`}
          />
          <label className="flex items-center gap-2 rounded border p-2 text-sm">
            <input type="checkbox" checked={newOptionCorrect} onChange={(event) => setNewOptionCorrect(event.target.checked)} />
            Correta
          </label>
          <button className="rounded bg-ink px-3 py-1 text-sm text-white md:col-span-4" type="submit">
            Adicionar opcao
          </button>
        </form>
      </div>
    </Panel>
  );
}

export function AdminContentPage() {
  const queryClient = useQueryClient();
  const [selectedQuizId, setSelectedQuizId] = useState<number | null>(null);
  const [createQuestionCorrect, setCreateQuestionCorrect] = useState<"a" | "b">("a");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const trailsQuery = useQuery({ queryKey: ["admin-trails"], queryFn: getAdminTrails });
  const quizzesQuery = useQuery({ queryKey: ["admin-quizzes"], queryFn: getAdminQuizzes });

  useEffect(() => {
    if (!selectedQuizId && quizzesQuery.data?.items.length) {
      setSelectedQuizId(quizzesQuery.data.items[0].id);
    }
  }, [quizzesQuery.data, selectedQuizId]);

  const selectedQuiz = useMemo(
    () => quizzesQuery.data?.items.find((quiz) => quiz.id === selectedQuizId) ?? null,
    [quizzesQuery.data, selectedQuizId]
  );

  const questionsQuery = useQuery({
    queryKey: ["admin-quiz-questions", selectedQuizId],
    queryFn: () => getAdminQuizQuestions(selectedQuizId as number),
    enabled: !!selectedQuizId,
  });

  const createQuizMutation = useMutation({
    mutationFn: createAdminQuiz,
    onSuccess: (result) => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["admin-quizzes"] });
      setSelectedQuizId(result.id);
    },
    onError: (error) => setErrorMessage(getErrorMessage(error)),
  });

  const updateQuizMutation = useMutation({
    mutationFn: ({ quizId, payload }: { quizId: number; payload: Parameters<typeof updateAdminQuiz>[1] }) =>
      updateAdminQuiz(quizId, payload),
    onSuccess: () => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["admin-quizzes"] });
    },
    onError: (error) => setErrorMessage(getErrorMessage(error)),
  });

  const deleteQuizMutation = useMutation({
    mutationFn: deleteAdminQuiz,
    onSuccess: () => {
      setErrorMessage(null);
      setSelectedQuizId(null);
      queryClient.invalidateQueries({ queryKey: ["admin-quizzes"] });
      queryClient.invalidateQueries({ queryKey: ["admin-quiz-questions"] });
    },
    onError: (error) => setErrorMessage(getErrorMessage(error)),
  });

  const createQuestionMutation = useMutation({
    mutationFn: ({ quizId, payload }: { quizId: number; payload: Parameters<typeof createAdminQuizQuestion>[1] }) =>
      createAdminQuizQuestion(quizId, payload),
    onSuccess: () => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["admin-quiz-questions", selectedQuizId] });
    },
    onError: (error) => setErrorMessage(getErrorMessage(error)),
  });

  const updateQuestionMutation = useMutation({
    mutationFn: ({ questionId, payload }: { questionId: number; payload: Parameters<typeof updateAdminQuizQuestion>[1] }) =>
      updateAdminQuizQuestion(questionId, payload),
    onSuccess: () => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["admin-quiz-questions", selectedQuizId] });
    },
    onError: (error) => setErrorMessage(getErrorMessage(error)),
  });

  const deleteQuestionMutation = useMutation({
    mutationFn: deleteAdminQuizQuestion,
    onSuccess: () => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["admin-quiz-questions", selectedQuizId] });
    },
    onError: (error) => setErrorMessage(getErrorMessage(error)),
  });

  const createOptionMutation = useMutation({
    mutationFn: ({ questionId, payload }: { questionId: number; payload: Parameters<typeof createAdminQuizOption>[1] }) =>
      createAdminQuizOption(questionId, payload),
    onSuccess: () => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["admin-quiz-questions", selectedQuizId] });
    },
    onError: (error) => setErrorMessage(getErrorMessage(error)),
  });

  const updateOptionMutation = useMutation({
    mutationFn: ({ optionId, payload }: { optionId: number; payload: Parameters<typeof updateAdminQuizOption>[1] }) =>
      updateAdminQuizOption(optionId, payload),
    onSuccess: () => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["admin-quiz-questions", selectedQuizId] });
    },
    onError: (error) => setErrorMessage(getErrorMessage(error)),
  });

  const deleteOptionMutation = useMutation({
    mutationFn: deleteAdminQuizOption,
    onSuccess: () => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["admin-quiz-questions", selectedQuizId] });
    },
    onError: (error) => setErrorMessage(getErrorMessage(error)),
  });

  if (trailsQuery.isPending || quizzesQuery.isPending) return <LoadingState label="Carregando conteudo admin..." />;
  if (trailsQuery.isError || quizzesQuery.isError) return <ErrorState message="Falha ao carregar conteudo admin." />;

  const submitCreateQuiz = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    createQuizMutation.mutate({
      trail_id: Number(form.get("trail_id")),
      lesson_id: form.get("lesson_id") ? Number(form.get("lesson_id")) : null,
      slug: String(form.get("slug") ?? ""),
      title: String(form.get("title") ?? ""),
      passing_score: Number(form.get("passing_score") ?? 70),
      is_active: form.get("is_active") === "on",
    });
    event.currentTarget.reset();
  };

  const submitUpdateQuiz = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedQuizId) return;
    const form = new FormData(event.currentTarget);
    updateQuizMutation.mutate({
      quizId: selectedQuizId,
      payload: {
        trail_id: Number(form.get("trail_id")),
        lesson_id: form.get("lesson_id") ? Number(form.get("lesson_id")) : null,
        slug: String(form.get("slug") ?? ""),
        title: String(form.get("title") ?? ""),
        passing_score: Number(form.get("passing_score") ?? 70),
        is_active: form.get("is_active") === "on",
      },
    });
  };

  const submitCreateQuestion = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedQuizId) return;
    const form = new FormData(event.currentTarget);
    const optionA = String(form.get("option_a") ?? "");
    const optionB = String(form.get("option_b") ?? "");

    createQuestionMutation.mutate({
      quizId: selectedQuizId,
      payload: {
        position: Number(form.get("position")),
        prompt: String(form.get("prompt") ?? ""),
        explanation: String(form.get("explanation") ?? ""),
        options: [
          { position: 1, option_text: optionA, is_correct: createQuestionCorrect === "a" },
          { position: 2, option_text: optionB, is_correct: createQuestionCorrect === "b" },
        ],
      },
    });
    event.currentTarget.reset();
    setCreateQuestionCorrect("a");
  };

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Admin - Conteudo (Quiz Builder)</h1>
      {errorMessage ? <ErrorState message={errorMessage} /> : null}

      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <div className="space-y-4">
          <Panel>
            <h2 className="font-semibold">Quizzes</h2>
            <div className="mt-2 space-y-2">
              {quizzesQuery.data.items.map((quiz) => (
                <button
                  key={quiz.id}
                  className={`w-full rounded border p-2 text-left text-sm ${
                    selectedQuizId === quiz.id ? "border-ink bg-sky-50" : "border-sky-100"
                  }`}
                  type="button"
                  onClick={() => setSelectedQuizId(quiz.id)}
                >
                  #{quiz.id} {quiz.title}
                  <div className="text-xs text-ink/60">slug: {quiz.slug}</div>
                </button>
              ))}
            </div>
          </Panel>

          <Panel>
            <h2 className="font-semibold">Novo quiz</h2>
            <form className="mt-3 space-y-2" onSubmit={submitCreateQuiz}>
              <select name="trail_id" className="w-full rounded border p-2" defaultValue={trailsQuery.data.items[0]?.id ?? ""}>
                {trailsQuery.data.items.map((trail) => (
                  <option key={trail.id} value={trail.id}>
                    {trail.title}
                  </option>
                ))}
              </select>
              <input name="lesson_id" type="number" className="w-full rounded border p-2" placeholder="lesson_id opcional" />
              <input name="slug" className="w-full rounded border p-2" placeholder="slug" required />
              <input name="title" className="w-full rounded border p-2" placeholder="titulo" required />
              <input name="passing_score" type="number" min={0} max={100} className="w-full rounded border p-2" defaultValue={70} />
              <label className="flex items-center gap-2 text-sm">
                <input name="is_active" type="checkbox" defaultChecked /> Ativo
              </label>
              <button className="w-full rounded bg-ink px-3 py-2 text-sm text-white" type="submit" disabled={createQuizMutation.isPending}>
                Criar quiz
              </button>
            </form>
          </Panel>
        </div>

        <div className="space-y-4">
          {!selectedQuiz ? (
            <Panel>
              <p className="text-sm text-ink/70">Selecione um quiz para editar perguntas e opcoes.</p>
            </Panel>
          ) : (
            <>
              <Panel>
                <h2 className="font-semibold">Editar quiz #{selectedQuiz.id}</h2>
                <form key={`quiz-form-${selectedQuiz.id}`} className="mt-3 grid gap-2 md:grid-cols-2" onSubmit={submitUpdateQuiz}>
                  <select name="trail_id" className="rounded border p-2" defaultValue={selectedQuiz.trail_id}>
                    {trailsQuery.data.items.map((trail) => (
                      <option key={trail.id} value={trail.id}>
                        {trail.title}
                      </option>
                    ))}
                  </select>
                  <input
                    name="lesson_id"
                    type="number"
                    className="rounded border p-2"
                    placeholder="lesson_id opcional"
                    defaultValue={selectedQuiz.lesson_id ?? ""}
                  />
                  <input name="slug" className="rounded border p-2" defaultValue={selectedQuiz.slug} required />
                  <input name="title" className="rounded border p-2" defaultValue={selectedQuiz.title} required />
                  <input
                    name="passing_score"
                    type="number"
                    min={0}
                    max={100}
                    className="rounded border p-2"
                    defaultValue={selectedQuiz.passing_score}
                  />
                  <label className="flex items-center gap-2 rounded border p-2 text-sm">
                    <input name="is_active" type="checkbox" defaultChecked={selectedQuiz.is_active === 1} /> Ativo
                  </label>
                  <div className="flex gap-2 md:col-span-2">
                    <button className="rounded bg-ink px-3 py-2 text-sm text-white" type="submit" disabled={updateQuizMutation.isPending}>
                      Salvar quiz
                    </button>
                    <button
                      className="rounded border border-red-300 px-3 py-2 text-sm text-red-700"
                      type="button"
                      onClick={() => deleteQuizMutation.mutate(selectedQuiz.id)}
                      disabled={deleteQuizMutation.isPending}
                    >
                      Excluir quiz
                    </button>
                  </div>
                </form>
              </Panel>

              <Panel>
                <h2 className="font-semibold">Nova pergunta</h2>
                <form key={`new-question-${selectedQuiz.id}`} className="mt-3 grid gap-2 md:grid-cols-2" onSubmit={submitCreateQuestion}>
                  <input name="position" type="number" min={1} className="rounded border p-2" placeholder="posicao" required />
                  <input name="prompt" className="rounded border p-2" placeholder="prompt" required />
                  <textarea name="explanation" className="rounded border p-2 md:col-span-2" rows={2} placeholder="explicacao" required />
                  <input name="option_a" className="rounded border p-2" placeholder="opcao A" required />
                  <input name="option_b" className="rounded border p-2" placeholder="opcao B" required />
                  <div className="flex gap-4 text-sm md:col-span-2">
                    <label className="flex items-center gap-1">
                      <input
                        type="radio"
                        checked={createQuestionCorrect === "a"}
                        onChange={() => setCreateQuestionCorrect("a")}
                      />
                      Opcao A correta
                    </label>
                    <label className="flex items-center gap-1">
                      <input
                        type="radio"
                        checked={createQuestionCorrect === "b"}
                        onChange={() => setCreateQuestionCorrect("b")}
                      />
                      Opcao B correta
                    </label>
                  </div>
                  <button className="rounded bg-ink px-3 py-2 text-sm text-white md:col-span-2" type="submit">
                    Criar pergunta
                  </button>
                </form>
              </Panel>

              {questionsQuery.isPending ? <LoadingState label="Carregando perguntas..." /> : null}
              {questionsQuery.isError ? <ErrorState message="Falha ao carregar perguntas." /> : null}

              {questionsQuery.data?.items.map((question) => (
                <QuestionCard
                  key={question.id}
                  question={question}
                  onUpdateQuestion={(questionId, payload) => updateQuestionMutation.mutate({ questionId, payload })}
                  onDeleteQuestion={(questionId) => deleteQuestionMutation.mutate(questionId)}
                  onCreateOption={(questionId, payload) => createOptionMutation.mutate({ questionId, payload })}
                  onUpdateOption={(optionId, payload) => updateOptionMutation.mutate({ optionId, payload })}
                  onDeleteOption={(optionId) => deleteOptionMutation.mutate(optionId)}
                />
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
