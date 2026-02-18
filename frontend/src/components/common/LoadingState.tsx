export function LoadingState({ label = "Carregando..." }: { label?: string }) {
  return <div className="rounded-lg bg-sky-50 p-4 text-sm text-ink/80">{label}</div>;
}
