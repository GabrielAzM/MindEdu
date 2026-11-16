import { Panel } from "../components/common/Panel";

export function AchievementsPage() {
  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Conquistas</h1>
      <Panel>
        <ul className="list-disc space-y-1 pl-5">
          <li>Primeiro check-in</li>
          <li>Primeira resposta útil</li>
          <li>Sequência de 3 dias</li>
        </ul>
      </Panel>
    </div>
  );
}
