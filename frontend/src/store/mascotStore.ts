import { create } from "zustand";

export type MascotId = "fox" | "owl";

export const mascotCatalog: Record<MascotId, { name: string; description: string }> = {
  fox: {
    name: "Raposa Lumi",
    description: "Mascote de energia e coragem para desafios do dia.",
  },
  owl: {
    name: "Coruja Nino",
    description: "Mascote de calma e estratégia para estudar com foco.",
  },
};

export type CosmeticItem = {
  id: string;
  name: string;
  slot: "head" | "face" | "neck" | "back" | "effect" | "hand" | "chest";
  rarity: "common" | "rare" | "epic";
  obtained_from: "seed" | "levelup";
  obtained_at: string;
  effect_multiplier: number;
};

type MascotState = {
  mascotId: MascotId;
  inventory: CosmeticItem[];
  equippedByMascot: Record<MascotId, string | null>;
  setMascot: (mascotId: MascotId) => void;
  hydrateFromProfile: (payload: {
    inventory: CosmeticItem[];
    equipped: Record<MascotId, string | null>;
  }) => void;
  setEquippedForMascot: (mascotId: MascotId, itemId: string | null) => void;
};

export const useMascotStore = create<MascotState>((set) => ({
  mascotId: "fox",
  inventory: [],
  equippedByMascot: {
    fox: null,
    owl: null,
  },
  setMascot: (mascotId) => set({ mascotId }),
  hydrateFromProfile: ({ inventory, equipped }) =>
    set({
      inventory,
      equippedByMascot: {
        fox: equipped.fox ?? null,
        owl: equipped.owl ?? null,
      },
    }),
  setEquippedForMascot: (mascotId, itemId) =>
    set((state) => ({
      equippedByMascot: {
        ...state.equippedByMascot,
        [mascotId]: itemId,
      },
    })),
}));
