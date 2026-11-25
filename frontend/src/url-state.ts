import type {
  FannedConfig,
  GaugeSuggestState,
  Preset,
  ScaleLengthUnit,
  StringInput,
  TensionUnit,
} from "./types";
import { DEFAULT_FANNED } from "./types";
import { defaultFanned, stateFromPreset } from "./units";

const DEFAULT_N = 5;

function numEq(
  a: number | null | undefined,
  b: number | null | undefined,
): boolean {
  if (a == null && b == null) return true;
  if (a == null || b == null) return false;
  return Math.abs(a - b) < 1e-6;
}

function fmtCompact(n: number): string {
  return Number(n.toFixed(4)).toString();
}

function encodeStrings(
  strings: StringInput[],
  baseL: number,
  fannedEnabled: boolean,
): string {
  return strings
    .map((s) => {
      const base = `${s.pitch}:${fmtCompact(s.T)}`;
      return !fannedEnabled && !numEq(s.L, baseL)
        ? `${base}:${fmtCompact(s.L)}`
        : base;
    })
    .join(",");
}

function decodeStrings(raw: string, fallbackL: number): StringInput[] | null {
  const parts = raw
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);
  if (!parts.length) return null;
  const out: StringInput[] = [];
  for (const part of parts) {
    const [pitch, tStr, lStr] = part.split(":");
    const T = Number(tStr);
    const L = lStr !== undefined && lStr !== "" ? Number(lStr) : fallbackL;
    if (
      !pitch ||
      !Number.isFinite(T) ||
      T <= 0 ||
      !Number.isFinite(L) ||
      L <= 0
    )
      return null;
    out.push({ pitch, T, L });
  }
  return out;
}

function encodeFanned(f: FannedConfig): string {
  const vals = [
    fmtCompact(f.L_bass),
    fmtCompact(f.L_treble),
    fmtCompact(f.nutWidth),
  ];
  if (f.edgeBass != null || f.edgeTreble != null) {
    vals.push(
      f.edgeBass != null ? fmtCompact(f.edgeBass) : "",
      f.edgeTreble != null ? fmtCompact(f.edgeTreble) : "",
    );
  }
  return vals.join(",");
}

function fannedEqual(a: FannedConfig, b: FannedConfig): boolean {
  if (a.enabled !== b.enabled) return false;
  if (!a.enabled) return true;
  return (
    numEq(a.L_bass, b.L_bass) &&
    numEq(a.L_treble, b.L_treble) &&
    numEq(a.nutWidth, b.nutWidth) &&
    numEq(a.edgeBass, b.edgeBass) &&
    numEq(a.edgeTreble, b.edgeTreble)
  );
}

/**
 * Serialize GaugeSuggestState into compact URLSearchParams.
 * Encodes `inst=<preset>` plus only differences from that preset when a preset is selected.
 */
export function stateToParams(
  state: GaugeSuggestState,
  presets: Preset[],
): URLSearchParams {
  const params = new URLSearchParams();
  const basePreset = presets.find((p) => p.id === state.preset);
  const base = basePreset ? stateFromPreset(basePreset, DEFAULT_N) : null;

  if (!base) {
    params.set("inst", "custom");
  } else if (state.preset !== presets[0]?.id) {
    params.set("inst", state.preset);
  }

  if (!base || state.lengthUnit !== base.lengthUnit)
    params.set("lu", state.lengthUnit);
  if (!base || state.tensionUnit !== base.tensionUnit)
    params.set("tu", state.tensionUnit);
  if (state.n !== (base?.n ?? DEFAULT_N)) params.set("n", String(state.n));
  if (!base || state.types.join(",") !== base.types.join(",")) {
    params.set("types", state.types.join(","));
  }
  if (!state.fanned.enabled && (!base || !numEq(state.L, base.L))) {
    params.set("L", fmtCompact(state.L));
  }
  if (!base) {
    if (state.fanned.enabled) params.set("fan", encodeFanned(state.fanned));
  } else if (!fannedEqual(state.fanned, base.fanned)) {
    params.set("fan", state.fanned.enabled ? encodeFanned(state.fanned) : "0");
  }

  const encodedCur = encodeStrings(
    state.strings,
    state.L,
    state.fanned.enabled,
  );
  const encodedBase = base
    ? encodeStrings(base.strings, base.L, base.fanned.enabled)
    : null;
  if (encodedCur !== encodedBase) {
    params.set("s", encodedCur);
  }

  return params;
}

/**
 * Hydrate GaugeSuggestState from URLSearchParams, falling back cleanly on invalid values.
 */
export function paramsToState(
  params: URLSearchParams,
  presets: Preset[],
): GaugeSuggestState {
  const inst = params.get("inst");
  const matched =
    inst && inst !== "custom" ? presets.find((p) => p.id === inst) : undefined;
  const fallback = matched ?? presets[0];

  const state: GaugeSuggestState = fallback
    ? stateFromPreset(fallback, DEFAULT_N)
    : {
        preset: "",
        lengthUnit: "in",
        tensionUnit: "lbf",
        n: DEFAULT_N,
        L: 25.5,
        types: ["DA:PB", "DA:PL"],
        strings: [{ pitch: "E2", T: 26, L: 25.5 }],
        fanned: { ...DEFAULT_FANNED },
      };

  if (inst === "custom") state.preset = "";

  const lu = params.get("lu");
  if ((lu === "in" || lu === "mm") && lu !== state.lengthUnit) {
    state.lengthUnit = lu as ScaleLengthUnit;
    state.fanned = defaultFanned(state.lengthUnit);
  }

  const tu = params.get("tu");
  if (tu === "lbf" || tu === "kgf" || tu === "N")
    state.tensionUnit = tu as TensionUnit;

  const nRaw = params.get("n");
  if (nRaw !== null) {
    const nParsed = Number.parseInt(nRaw, 10);
    if (Number.isInteger(nParsed) && nParsed >= 1 && nParsed <= 20)
      state.n = nParsed;
  }

  const typesRaw = params.get("types");
  if (typesRaw !== null) {
    const parsed = typesRaw
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    if (parsed.length > 0) state.types = parsed;
  }

  const lRaw = params.get("L");
  if (lRaw !== null) {
    const lParsed = Number(lRaw);
    if (Number.isFinite(lParsed) && lParsed > 0) {
      state.L = lParsed;
      state.strings = state.strings.map((s) => ({ ...s, L: lParsed }));
    }
  }

  const fanRaw = params.get("fan");
  if (fanRaw === "0") {
    state.fanned = { ...state.fanned, enabled: false };
  } else if (fanRaw) {
    const parts = fanRaw.split(",");
    const [L_bass, L_treble, nutWidth] = parts.slice(0, 3).map(Number);
    if (
      [L_bass, L_treble, nutWidth].every((v) => Number.isFinite(v) && v > 0)
    ) {
      const eb =
        parts[3] !== undefined && parts[3] !== "" ? Number(parts[3]) : null;
      const et =
        parts[4] !== undefined && parts[4] !== "" ? Number(parts[4]) : null;
      state.fanned = {
        enabled: true,
        L_bass,
        L_treble,
        nutWidth,
        edgeBass: eb !== null && Number.isFinite(eb) ? eb : null,
        edgeTreble: et !== null && Number.isFinite(et) ? et : null,
      };
    }
  }

  const sRaw = params.get("s");
  if (sRaw) {
    const decoded = decodeStrings(sRaw, state.L);
    if (decoded) state.strings = decoded;
  }

  return state;
}

export function buildUrl(state: GaugeSuggestState, presets: Preset[]): string {
  const params = stateToParams(state, presets);
  const currentPkg = new URLSearchParams(window.location.search).get("pkg");
  if (currentPkg) params.set("pkg", currentPkg);
  const qs = params.toString();
  return qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
}

export function createUrlSyncer(presets: Preset[], delayMs = 250) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  const write = (state: GaugeSuggestState) => {
    window.history.replaceState(null, "", buildUrl(state, presets));
  };
  return {
    sync(state: GaugeSuggestState) {
      if (timer !== null) clearTimeout(timer);
      timer = setTimeout(() => {
        timer = null;
        write(state);
      }, delayMs);
    },
    flush(state: GaugeSuggestState) {
      if (timer !== null) {
        clearTimeout(timer);
        timer = null;
      }
      write(state);
    },
  };
}
