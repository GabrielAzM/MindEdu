import type { SpritesheetData } from "pixi.js";

import foxIdle from "../../assets/mascots/fox/idle.json";
import foxHappy from "../../assets/mascots/fox/happy.json";
import foxLevelup from "../../assets/mascots/fox/levelup.json";
import foxBaseAtlas from "../../assets/mascots/fox/base.json";
import foxAccessoryAtlas from "../../assets/mascots/fox/accessory.json";
import foxEffectAtlas from "../../assets/mascots/fox/effect.json";
import foxBaseImage from "../../assets/mascots/fox/base.webp";
import foxAccessoryImage from "../../assets/mascots/fox/accessory.webp";
import foxEffectImage from "../../assets/mascots/fox/effect.webp";
import foxEvo1 from "../../assets/mascots/fox/evolutions/evo1.webp";
import foxEvo2 from "../../assets/mascots/fox/evolutions/evo2.webp";
import foxEvo3 from "../../assets/mascots/fox/evolutions/evo3.webp";
import foxEvo4 from "../../assets/mascots/fox/evolutions/evo4.webp";

import owlIdle from "../../assets/mascots/owl/idle.json";
import owlHappy from "../../assets/mascots/owl/happy.json";
import owlLevelup from "../../assets/mascots/owl/levelup.json";
import owlBaseAtlas from "../../assets/mascots/owl/base.json";
import owlAccessoryAtlas from "../../assets/mascots/owl/accessory.json";
import owlEffectAtlas from "../../assets/mascots/owl/effect.json";
import owlBaseImage from "../../assets/mascots/owl/base.webp";
import owlAccessoryImage from "../../assets/mascots/owl/accessory.webp";
import owlEffectImage from "../../assets/mascots/owl/effect.webp";
import owlEvo1 from "../../assets/mascots/owl/evolutions/evo1.webp";
import owlEvo2 from "../../assets/mascots/owl/evolutions/evo2.webp";
import owlEvo3 from "../../assets/mascots/owl/evolutions/evo3.webp";
import owlEvo4 from "../../assets/mascots/owl/evolutions/evo4.webp";

import { MascotId } from "../../store/mascotStore";

type AnimationMeta = { frames: string[]; fps: number };
type MascotLayer = "base" | "accessory" | "effect";

export type MascotAssets = {
  layers: Record<MascotLayer, { image: string; atlas: SpritesheetData }>;
  evolutions: Record<1 | 2 | 3 | 4, string>;
  animations: {
    idle: AnimationMeta;
    happy: AnimationMeta;
    levelup: AnimationMeta;
  };
};

const db: Record<MascotId, MascotAssets> = {
  fox: {
    layers: {
      base: { image: foxBaseImage, atlas: foxBaseAtlas as SpritesheetData },
      accessory: { image: foxAccessoryImage, atlas: foxAccessoryAtlas as SpritesheetData },
      effect: { image: foxEffectImage, atlas: foxEffectAtlas as SpritesheetData },
    },
    evolutions: {
      // Troque esses arquivos para usar artes finais:
      // src/assets/mascots/fox/evolutions/evo1.webp ... evo4.webp
      1: foxEvo1,
      2: foxEvo2,
      3: foxEvo3,
      4: foxEvo4,
    },
    animations: {
      idle: foxIdle,
      happy: foxHappy,
      levelup: foxLevelup,
    },
  },
  owl: {
    layers: {
      base: { image: owlBaseImage, atlas: owlBaseAtlas as SpritesheetData },
      accessory: { image: owlAccessoryImage, atlas: owlAccessoryAtlas as SpritesheetData },
      effect: { image: owlEffectImage, atlas: owlEffectAtlas as SpritesheetData },
    },
    evolutions: {
      // Troque esses arquivos para usar artes finais:
      // src/assets/mascots/owl/evolutions/evo1.webp ... evo4.webp
      1: owlEvo1,
      2: owlEvo2,
      3: owlEvo3,
      4: owlEvo4,
    },
    animations: {
      idle: owlIdle,
      happy: owlHappy,
      levelup: owlLevelup,
    },
  },
};

export function useMascotAssets(mascotId: MascotId) {
  return db[mascotId];
}
