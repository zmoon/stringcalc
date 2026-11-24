import { describe, expect, it } from "vitest";
import rawPresets from "../../stringcalc/data/presets.json";
import type { Preset } from "./types";
import {
  convertLength,
  convertTension,
  stateFromPreset,
  transposePitch,
} from "./units";
import { paramsToState, stateToParams } from "./url-state";

const presets = rawPresets as Preset[];

describe("url-state", () => {
  it("produces empty query params for the default preset", () => {
    const s = stateFromPreset(presets[0]);
    const params = stateToParams(s, presets);
    expect(params.toString()).toBe("");
    expect(paramsToState(params, presets)).toEqual(s);
  });

  it("encodes only diffs from a selected preset", () => {
    const banjo = presets.find((p) => p.id === "tenor-banjo-4-irish")!;
    const s = stateFromPreset(banjo);
    s.L = 22.5;
    s.strings = s.strings.map((x) => ({ ...x, L: 22.5 }));
    s.n = 6;

    const params = stateToParams(s, presets);
    expect(params.get("inst")).toBe("tenor-banjo-4-irish");
    expect(params.get("L")).toBe("22.5");
    expect(params.get("n")).toBe("6");
    expect(params.get("s")).toBeNull();
    expect(params.get("types")).toBeNull();

    const restored = paramsToState(params, presets);
    expect(restored).toEqual(s);
  });

  it("round-trips fanned fret parameters and custom strings", () => {
    const s = stateFromPreset(presets[0]);
    s.fanned = {
      enabled: true,
      L_bass: 26.5,
      L_treble: 25.0,
      nutWidth: 1.75,
      edgeBass: 0.15,
      edgeTreble: 0.125,
    };
    s.strings[0] = { pitch: "D2", T: 18, L: 25.5 };

    const params = stateToParams(s, presets);
    expect(params.get("fan")).toBe("26.5,25,1.75,0.15,0.125");
    expect(params.get("s")).toContain("D2:18");

    const restored = paramsToState(params, presets);
    expect(restored.fanned).toEqual(s.fanned);
    expect(restored.strings[0].pitch).toBe("D2");
    expect(restored.strings[0].T).toBe(18);
  });

  it("handles malformed query parameters gracefully", () => {
    const params = new URLSearchParams(
      "inst=nonexistent&lu=furlong&tu=dyn&n=999&L=-5&s=bad",
    );
    const restored = paramsToState(params, presets);
    expect(restored).toEqual(stateFromPreset(presets[0]));
  });
});

describe("units & pitch helpers", () => {
  it("transposes pitches accurately", () => {
    expect(transposePitch("E2", 1)).toBe("F2");
    expect(transposePitch("B3", 1)).toBe("C4");
    expect(transposePitch("C4", -1)).toBe("B3");
    expect(transposePitch("Bb2", 2)).toBe("C3");
    expect(transposePitch("not-a-pitch", 1)).toBe("not-a-pitch");
  });

  it("converts length and tension units cleanly", () => {
    expect(convertLength(25.5, "in", "mm")).toBeCloseTo(647.7, 1);
    expect(convertLength(650, "mm", "in")).toBeCloseTo(25.59, 2);
    expect(convertTension(10, "lbf", "kgf")).toBeCloseTo(4.54, 2);
    expect(convertTension(10, "lbf", "N")).toBeCloseTo(44.48, 2);
  });
});
