import type {
  FannedConfig,
  GaugeSuggestState,
  Preset,
  ScaleLengthUnit,
  StringInput,
  TensionUnit,
} from "./types";
import { DEFAULT_FANNED } from "./types";
import { stateFromPreset } from "./units";

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
      if (!fannedEnabled && !numEq(s.L, baseL)) {
        return `${base}:${fmtCompact(s.L)}`;
      }
      return base;
    })
    .join(",");
}

function decodeStrings(raw: string, fallbackL: number): StringInput[] | null {
  const parts = raw
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);
  if (parts.length === 0) return null;
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
    ) {
      return null;
    }
    out.push({ pitch, T, L });
  }
  return out;
}

function arraysEqual(a: string[], b: string[]): boolean {
  return a.length === b.length && a.every((v, i) => v === b[i]);
}

function fannedEqual(a: FannedConfig, b: FannedConfig): boolean {
  return (
    a.enabled === b.enabled &&
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

  if (base) {
    if (state.preset !== presets[0]?.id) {
      params.set("inst", state.preset);
    }
    if (state.lengthUnit !== base.lengthUnit)
      params.set("lu", state.lengthUnit);
    if (state.tensionUnit !== base.tensionUnit)
      params.set("tu", state.tensionUnit);
    if (state.n !== base.n) params.set("n", String(state.n));
    if (!arraysEqual(state.types, base.types))
      params.set("types", state.types.join(","));
    if (!state.fanned.enabled && !numEq(state.L, base.L)) {
      params.set("L", fmtCompact(state.L));
    }
    if (!fannedEqual(state.fanned, base.fanned)) {
      if (state.fanned.enabled) {
        const vals = [
          fmtCompact(state.fanned.L_bass),
          fmtCompact(state.fanned.L_treble),
          fmtCompact(state.fanned.nutWidth),
        ];
        if (state.fanned.edgeBass != null || state.fanned.edgeTreble != null) {
          vals.push(
            state.fanned.edgeBass != null
              ? fmtCompact(state.fanned.edgeBass)
              : "",
            state.fanned.edgeTreble != null
              ? fmtCompact(state.fanned.edgeTreble)
              : "",
          );
        }
        params.set("fan", vals.join(","));
      } else {
        params.set("fan", "0");
      }
    }

    const encodedCur = encodeStrings(
      state.strings,
      state.L,
      state.fanned.enabled,
    );
    const encodedBase = encodeStrings(
      base.strings,
      base.L,
      base.fanned.enabled,
    );
    if (encodedCur !== encodedBase) {
      params.set("s", encodedCur);
    }
  } else {
    params.set("inst", "custom");
    params.set("lu", state.lengthUnit);
    params.set("tu", state.tensionUnit);
    if (state.n !== DEFAULT_N) params.set("n", String(state.n));
    params.set("types", state.types.join(","));
    if (!state.fanned.enabled) {
      params.set("L", fmtCompact(state.L));
    } else {
      const vals = [
        fmtCompact(state.fanned.L_bass),
        fmtCompact(state.fanned.L_treble),
        fmtCompact(state.fanned.nutWidth),
      ];
      if (state.fanned.edgeBass != null || state.fanned.edgeTreble != null) {
        vals.push(
          state.fanned.edgeBass != null
            ? fmtCompact(state.fanned.edgeBass)
            : "",
          state.fanned.edgeTreble != null
            ? fmtCompact(state.fanned.edgeTreble)
            : "",
        );
      }
      params.set("fan", vals.join(","));
    }
    params.set(
      "s",
      encodeStrings(state.strings, state.L, state.fanned.enabled),
    );
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
  const defaultPreset = presets[0];
  const inst = params.get("inst");
  const matchedPreset =
    inst && inst !== "custom" ? presets.find((p) => p.id === inst) : undefined;

  const state: GaugeSuggestState = matchedPreset
    ? stateFromPreset(matchedPreset, DEFAULT_N)
    : defaultPreset
      ? stateFromPreset(defaultPreset, DEFAULT_N)
      : {
          preset: "",
          lengthUnit: "in",
          tensionUnit: "lbf",
          n: DEFAULT_N,
          L: 25.5,
          types: ["DA:PB", "DA:PL"],
          strings: [{ pitch: "E2", T: 16.5, L: 25.5 }],
          fanned: { ...DEFAULT_FANNED },
        };

  if (inst === "custom") {
    state.preset = "";
  }

  const lu = params.get("lu");
  if (lu === "in" || lu === "mm") {
    state.lengthUnit = lu as ScaleLengthUnit;
  }

  const tu = params.get("tu");
  if (tu === "lbf" || tu === "kgf" || tu === "N") {
    state.tensionUnit = tu as TensionUnit;
  }

  const nRaw = params.get("n");
  if (nRaw !== null) {
    const nParsed = Number.parseInt(nRaw, 10);
    if (Number.isInteger(nParsed) && nParsed >= 1 && nParsed <= 20) {
      state.n = nParsed;
    }
  }

  const typesRaw = params.get("types");
  if (typesRaw !== null) {
    const parsed = typesRaw
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    if (parsed.length > 0) {
      state.types = parsed;
    }
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
    const L_bass = Number(parts[0]);
    const L_treble = Number(parts[1]);
    const nutWidth = Number(parts[2]);
    if (
      Number.isFinite(L_bass) &&
      L_bass > 0 &&
      Number.isFinite(L_treble) &&
      L_treble > 0 &&
      Number.isFinite(nutWidth) &&
      nutWidth > 0
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
    if (decoded) {
      state.strings = decoded;
    }
  }

  return state;
}

export function createUrlSyncer(presets: Preset[], delayMs = 250) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  return (state: GaugeSuggestState) => {
    if (timer !== null) clearTimeout(timer);
    timer = setTimeout(() => {
      const params = stateToParams(state, presets);
      // Preserve ?pkg=... override when developing
      const currentPkg = new URLSearchParams(window.location.search).get("pkg");
      if (currentPkg) params.set("pkg", currentPkg);
      const qs = params.toString();
      const nextUrl = qs
        ? `${window.location.pathname}?${qs}`
        : window.location.pathname;
      window.history.replaceState(null, "", nextUrl);
    }, delayMs);
  };
}
