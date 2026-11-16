import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatedSprite, Application, Assets, Container, Spritesheet, Texture, type SpritesheetData } from "pixi.js";

import { useMascotStore } from "../../store/mascotStore";
import { useMascotAssets } from "./useMascotAssets";

const rarityBoost: Record<"common" | "rare" | "epic", number> = {
  common: 1,
  rare: 1.2,
  epic: 1.4,
};

function cloneSheetData(atlas: SpritesheetData, image: string): SpritesheetData {
  const cloned = JSON.parse(JSON.stringify(atlas)) as SpritesheetData;
  cloned.meta = { ...cloned.meta, image };
  return cloned;
}

function createLayerAnimation(sheet: Spritesheet, frames: string[], fps: number): AnimatedSprite | null {
  const textures = frames
    .map((frameName) => sheet.textures[frameName as keyof typeof sheet.textures])
    .filter((texture): texture is Texture => Boolean(texture));

  if (!textures.length) return null;

  const layer = new AnimatedSprite(textures);
  layer.loop = true;
  layer.animationSpeed = Math.max(1, fps) / 60;
  layer.anchor.set(0.5);
  layer.play();
  return layer;
}

export function MascotStage({ animation = "idle" }: { animation?: "idle" | "happy" | "levelup" }) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const appRef = useRef<Application | null>(null);
  const [pixiError, setPixiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const mascotId = useMascotStore((s) => s.mascotId);
  const inventory = useMascotStore((s) => s.inventory);
  const equippedByMascot = useMascotStore((s) => s.equippedByMascot);
  const assets = useMascotAssets(mascotId);

  const equippedItem = useMemo(() => {
    const equippedId = equippedByMascot[mascotId];
    if (!equippedId) return null;
    return inventory.find((item) => item.id === equippedId) ?? null;
  }, [equippedByMascot, mascotId, inventory]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    let cancelled = false;
    const sheets: Spritesheet[] = [];

    const setup = async () => {
      try {
        setPixiError(null);
        setIsLoading(true);
        const app = new Application();
        await app.init({
          width: 420,
          height: 280,
          antialias: true,
          backgroundAlpha: 0,
          preference: "webgl",
        });

        if (cancelled) {
          app.destroy(true, { children: true, texture: false, textureSource: false });
          return;
        }

        host.innerHTML = "";
        host.appendChild(app.canvas);
        appRef.current = app;

        const root = new Container();
        root.x = 210;
        root.y = 140;
        app.stage.addChild(root);

        const animationMeta = assets.animations[animation];
        if (!animationMeta.frames.length) {
          throw new Error("animation frames missing");
        }

        const baseTexture = await Assets.load<Texture>(assets.layers.base.image);
        if (cancelled) return;
        const baseSheet = new Spritesheet({
          texture: baseTexture,
          data: cloneSheetData(assets.layers.base.atlas, assets.layers.base.image),
        });
        sheets.push(baseSheet);
        await baseSheet.parse();
        if (cancelled) return;

        const base = createLayerAnimation(baseSheet, animationMeta.frames, animationMeta.fps);
        if (!base) throw new Error("base layer could not be rendered");
        base.width = 196;
        base.height = 196;
        root.addChild(base);

        if (equippedItem) {
          const accessoryTexture = await Assets.load<Texture>(assets.layers.accessory.image);
          if (cancelled) return;
          const accessorySheet = new Spritesheet({
            texture: accessoryTexture,
            data: cloneSheetData(assets.layers.accessory.atlas, assets.layers.accessory.image),
          });
          sheets.push(accessorySheet);
          await accessorySheet.parse();
          if (cancelled) return;

          const accessory = createLayerAnimation(accessorySheet, animationMeta.frames, animationMeta.fps);
          if (accessory) {
            accessory.width = 204;
            accessory.height = 204;
            accessory.alpha = 0.78 + (equippedItem.effect_multiplier - 1) * 0.08;
            root.addChild(accessory);
          }
        }

        const effectTexture = await Assets.load<Texture>(assets.layers.effect.image);
        if (cancelled) return;
        const effectSheet = new Spritesheet({
          texture: effectTexture,
          data: cloneSheetData(assets.layers.effect.atlas, assets.layers.effect.image),
        });
        sheets.push(effectSheet);
        await effectSheet.parse();
        if (cancelled) return;

        const effect = createLayerAnimation(effectSheet, animationMeta.frames, animationMeta.fps);
        if (effect) {
          const boost = equippedItem ? rarityBoost[equippedItem.rarity] : 0.9;
          effect.width = 206 * boost;
          effect.height = 206 * boost;
          effect.alpha = equippedItem ? 0.42 + equippedItem.effect_multiplier * 0.1 : 0.22;
          root.addChild(effect);
        }
        app.canvas.style.display = "block";
        app.canvas.style.maxWidth = "100%";
        app.canvas.style.height = "auto";
        setIsLoading(false);
      } catch (error) {
        const detail = error instanceof Error ? error.message : "render failed";
        if (!cancelled) {
          setPixiError(detail);
          setIsLoading(false);
        }
      }
    };

    void setup();

    return () => {
      cancelled = true;
      sheets.forEach((sheet) => sheet.destroy(false));
      appRef.current?.destroy(true, { children: true, texture: false, textureSource: false });
      appRef.current = null;
    };
  }, [assets, animation, equippedItem]);

  return (
    <div className="rounded-xl border border-sky-100 bg-white p-3">
      <div className="relative min-h-[280px]">
        {pixiError ? (
          <div className="flex min-h-[280px] flex-col items-center justify-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-4 text-center">
            <img src={assets.evolutions[1]} alt="Mascote" className="h-28 w-28 object-contain" />
            <p className="text-sm font-semibold text-amber-900">Não foi possível abrir a animação em tempo real.</p>
            <p className="text-xs text-amber-800">O mascote continua aqui. Tente recarregar a página para ver a animação.</p>
            <details className="text-left text-xs text-amber-800">
              <summary className="cursor-pointer">Detalhes técnicos</summary>
              <p className="mt-1">{pixiError}</p>
            </details>
          </div>
        ) : (
          <div ref={hostRef} className="min-h-[280px]" />
        )}
        {isLoading && !pixiError ? (
          <div className="absolute inset-0 flex min-h-[280px] flex-col items-center justify-center gap-2 rounded-lg bg-white/90" aria-live="polite">
            <img src={assets.evolutions[1]} alt="" className="h-28 w-28 animate-pulse object-contain" />
            <p className="text-sm text-ink/70">Carregando animação do mascote…</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}
