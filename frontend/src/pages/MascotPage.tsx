import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Panel } from "../components/common/Panel";
import { MascotStage } from "../components/pixi/MascotStage";
import { useMascotAssets } from "../components/pixi/useMascotAssets";
import { equipMascotItem, getMyProfile } from "../services/progressService";
import { mascotCatalog, type MascotId, useMascotStore } from "../store/mascotStore";

type MascotAnimation = "idle" | "happy" | "levelup";

const animationLabels: Record<MascotAnimation, string> = {
  idle: "Parado",
  happy: "Feliz",
  levelup: "Evoluindo",
};

const rarityLabels = {
  common: "comum",
  rare: "raro",
  epic: "epico",
} as const;

export function MascotPage() {
  const queryClient = useQueryClient();
  const mascotId = useMascotStore((s) => s.mascotId);
  const setMascot = useMascotStore((s) => s.setMascot);
  const inventory = useMascotStore((s) => s.inventory);
  const equippedByMascot = useMascotStore((s) => s.equippedByMascot);
  const hydrateFromProfile = useMascotStore((s) => s.hydrateFromProfile);
  const setEquippedForMascot = useMascotStore((s) => s.setEquippedForMascot);
  const [animation, setAnimation] = useState<MascotAnimation>("idle");
  const assets = useMascotAssets(mascotId);

  const profileQuery = useQuery({ queryKey: ["my-profile"], queryFn: getMyProfile });

  useEffect(() => {
    if (!profileQuery.data) return;
    hydrateFromProfile({
      inventory: profileQuery.data.cosmetics.inventory,
      equipped: profileQuery.data.cosmetics.equipped,
    });
  }, [hydrateFromProfile, profileQuery.data]);

  const equipMutation = useMutation({
    mutationFn: ({ selectedMascotId, itemId }: { selectedMascotId: MascotId; itemId: string | null }) =>
      equipMascotItem(selectedMascotId, itemId),
    onSuccess: (payload) => {
      setEquippedForMascot(payload.mascot_id, payload.equipped_item?.id ?? null);
      void queryClient.invalidateQueries({ queryKey: ["my-profile"] });
    },
  });

  if (profileQuery.isPending) return <LoadingState label="Carregando painel do mascote..." />;
  if (profileQuery.isError) return <ErrorState message="Falha ao carregar mascote." />;

  const profile = profileQuery.data;
  const mascotMeta = mascotCatalog[mascotId];
  const skillData = Object.entries(profile.skills).map(([name, value]) => ({ name, value }));
  const xpData = profile.recent_xp.map((item) => ({ ...item, xp: Number(item.xp) }));
  const stage = Math.max(1, Math.min(4, profile.mascot.stage ?? 1)) as 1 | 2 | 3 | 4;
  const equippedItemId = equippedByMascot[mascotId];
  const equippedItem = inventory.find((item) => item.id === equippedItemId) ?? null;
  const recentlyGranted = profile.cosmetics.new_rewards;

  const thresholds = [10, 30, 50, 70];
  const current = profile.xp.total;
  const prev = stage <= 1 ? 0 : thresholds[stage - 2];
  const next = stage >= 4 ? thresholds[3] : thresholds[stage - 1];
  const span = Math.max(1, next - prev);
  const progressed = Math.max(0, Math.min(span, current - prev));
  const stageProgress = Math.round((progressed / span) * 100);

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-bold">Mascote</h1>
      <Panel className="border-2 border-emerald-200 bg-emerald-50">
        <p className="font-semibold">{mascotMeta.name}</p>
        <p className="text-sm text-ink/70">{mascotMeta.description}</p>
      </Panel>

      <div className="flex gap-2">
        <button
          className={`rounded border px-3 py-1 ${mascotId === "fox" ? "border-ink bg-sky-50" : ""}`}
          onClick={() => setMascot("fox")}
          type="button"
        >
          Raposa Lumi
        </button>
        <button
          className={`rounded border px-3 py-1 ${mascotId === "owl" ? "border-ink bg-sky-50" : ""}`}
          onClick={() => setMascot("owl")}
          type="button"
        >
          Coruja Nino
        </button>
      </div>

      <div className="space-y-2">
        <p className="text-sm font-semibold">Animacao da cena</p>
        <div className="flex flex-wrap gap-2">
          {(Object.keys(animationLabels) as MascotAnimation[]).map((key) => (
            <button
              key={key}
              className={`rounded border px-3 py-1 text-sm ${animation === key ? "border-ink bg-sky-50" : ""}`}
              onClick={() => setAnimation(key)}
              type="button"
            >
              {animationLabels[key]}
            </button>
          ))}
        </div>
      </div>

      <MascotStage animation={animation} />

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-semibold">Evolucao por XP</h2>
          <img
            src={assets.evolutions[stage]}
            alt={`Mascote ${mascotId} evolucao ${stage}`}
            className="mt-3 h-56 w-full rounded-xl border border-sky-100 object-contain"
          />
          <p className="mt-2 text-sm">Evolucao atual: {stage}/4</p>
          <p className="text-sm text-ink/70">
            Thresholds: 10, 30, 50, 70 XP | total atual: {profile.xp.total}
          </p>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-sky-100">
            <div className="h-full rounded-full bg-ink" style={{ width: `${stageProgress}%` }} />
          </div>
        </Panel>

        <Panel>
          <h2 className="font-semibold">Inventario cosmetico ({mascotId})</h2>
          <p className="mt-1 text-xs text-ink/70">
            Regra: apenas 1 item equipado por mascote. Raridade aumenta efeito visual.
          </p>
          <p className="text-xs text-ink/70">
            Recompensas de trilha: 7 itens possiveis por level up. Repetido vira +5 XP.
          </p>
          {equippedItem ? (
            <p className="mt-2 rounded border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs text-emerald-900">
              Equipado agora: {equippedItem.name} ({rarityLabels[equippedItem.rarity]}) | multiplicador x{equippedItem.effect_multiplier}
            </p>
          ) : (
            <p className="mt-2 rounded border border-sky-100 bg-sky-50 px-2 py-1 text-xs text-ink/80">
              Nenhum item equipado neste mascote.
            </p>
          )}
          <div className="mt-3 grid gap-2">
            {inventory.length === 0 ? (
              <p className="rounded border border-sky-100 bg-sky-50 p-2 text-sm text-ink/80">
                Ainda sem itens liberados. Complete trilhas e suba de nivel para desbloquear.
              </p>
            ) : null}
            {inventory.map((item) => {
              const isEquipped = equippedItemId === item.id;
              return (
                <div key={item.id} className="rounded border p-2">
                  <p className="font-medium">{item.name}</p>
                  <p className="text-xs text-ink/70">
                    {rarityLabels[item.rarity]} | slot: {item.slot} | efeito x{item.effect_multiplier}
                  </p>
                  <button
                    className={`mt-2 rounded border px-3 py-1 text-sm ${isEquipped ? "border-emerald-700 bg-emerald-50" : "border-sky-200"}`}
                    onClick={() =>
                      equipMutation.mutate({
                        selectedMascotId: mascotId,
                        itemId: isEquipped ? null : item.id,
                      })
                    }
                    type="button"
                    disabled={equipMutation.isPending}
                  >
                    {isEquipped ? "Desequipar" : "Equipar neste mascote"}
                  </button>
                </div>
              );
            })}
          </div>
        </Panel>
      </div>

      <Panel>
        <h2 className="font-semibold">Drops recentes de level up</h2>
        {recentlyGranted.length === 0 ? (
          <p className="mt-2 text-sm text-ink/70">Nenhum novo item neste momento.</p>
        ) : (
          <div className="mt-2 grid gap-2 md:grid-cols-2">
            {recentlyGranted.map((reward) => (
              <div key={`${reward.level}-${reward.id}`} className="rounded border border-sky-100 bg-sky-50 p-2 text-sm">
                Nivel {reward.level}: {reward.name} ({rarityLabels[reward.rarity]}) - efeito x{reward.effect_multiplier}
              </div>
            ))}
          </div>
        )}
        {profile.cosmetics.duplicate_xp_converted > 0 ? (
          <p className="mt-2 text-sm font-medium text-emerald-800">
            Duplicatas convertidas em XP nesta leitura: +{profile.cosmetics.duplicate_xp_converted}
          </p>
        ) : null}
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-semibold">Habilidades conectadas ao progresso</h2>
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
        <Panel>
          <h2 className="font-semibold">XP recente (dinamico)</h2>
          <div className="mt-3 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={xpData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="xp" stroke="#1d4ed8" strokeWidth={2} dot={{ r: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </div>
  );
}
