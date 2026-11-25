import { describe, expect, it } from "vitest";
import rawPresets from "../../stringcalc/data/presets.json";
import type { Preset } from "./types";
import {
  convertLength,
  convertTension,
  fmtPitchSub,
  normalizePitch,
  splitPitch,
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

  it("round-trips custom preset and per-string scale lengths", () => {
    const s = stateFromPreset(presets[0]);
    s.preset = "";
    s.strings = [
      { pitch: "E2", T: 16.5, L: 26 },
      { pitch: "A2", T: 16.5, L: 25.5 },
    ];

    const params = stateToParams(s, presets);
    expect(params.get("inst")).toBe("custom");
    expect(params.get("s")).toBe("E2:16.5:26,A2:16.5");

    const restored = paramsToState(params, presets);
    expect(restored.preset).toBe("");
    expect(restored.strings).toEqual(s.strings);
  });

  it("seeds metric fanned defaults for mm presets", () => {
    const classical = presets.find((p) => p.id === "guitar-6-classical")!;
    const s = stateFromPreset(classical);
    expect(s.lengthUnit).toBe("mm");
    expect(s.fanned.L_bass).toBeGreaterThan(600);
    expect(s.fanned.L_treble).toBeGreaterThan(600);
    expect(s.fanned.nutWidth).toBeGreaterThan(40);

    // URL override lu=mm on an inch preset also seeds metric fanned defaults
    const fromUrl = paramsToState(
      new URLSearchParams("inst=guitar-6&lu=mm&L=647.7"),
      presets,
    );
    expect(fromUrl.lengthUnit).toBe("mm");
    expect(fromUrl.fanned.L_bass).toBeGreaterThan(600);
    expect(stateToParams(fromUrl, presets).get("fan")).toBeNull();
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

  it("formats and normalizes subscript pitch octaves and accidentals", () => {
    expect(fmtPitchSub("A4")).toBe("A₄");
    expect(fmtPitchSub("F#3")).toBe("F♯₃");
    expect(fmtPitchSub("Bb2")).toBe("B♭₂");
    expect(fmtPitchSub("B2")).toBe("B₂");
    expect(fmtPitchSub("C-1")).toBe("C₋₁");
    expect(fmtPitchSub("bad")).toBe("bad");
    expect(normalizePitch("A₄")).toBe("A4");
    expect(normalizePitch("F♯₃")).toBe("F#3");
    expect(normalizePitch("B♭₂")).toBe("Bb2");
    expect(normalizePitch("C₋₁")).toBe("C-1");
    expect(splitPitch("Bb2")).toEqual(["B♭", "2"]);
    expect(transposePitch("F♯₃", 1)).toBe("G3");
  });

  it("converts length and tension units cleanly", () => {
    expect(convertLength(25.5, "in", "mm")).toBeCloseTo(647.7, 1);
    expect(convertLength(650, "mm", "in")).toBeCloseTo(25.59, 2);
    expect(convertTension(10, "lbf", "kgf")).toBeCloseTo(4.54, 2);
    expect(convertTension(10, "lbf", "N")).toBeCloseTo(44.48, 2);
  });
});
