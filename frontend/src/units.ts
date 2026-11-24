import type {
  FannedConfig,
  GaugeSuggestState,
  LengthUnit,
  Preset,
  TensionUnit,
} from "./types";
import { DEFAULT_FANNED } from "./types";

const SHARP_NOTES = [
  "C",
  "C#",
  "D",
  "D#",
  "E",
  "F",
  "F#",
  "G",
  "G#",
  "A",
  "A#",
  "B",
];
const NOTE_TO_SEMITONE: Record<string, number> = {
  C: 0,
  "C#": 1,
  Db: 1,
  D: 2,
  "D#": 3,
  Eb: 3,
  E: 4,
  F: 5,
  "F#": 6,
  Gb: 6,
  G: 7,
  "G#": 8,
  Ab: 8,
  A: 9,
  "A#": 10,
  Bb: 10,
  B: 11,
};

const RE_PITCH = /^([A-Ga-g])([#b]?)(-?\d)$/;

export function parsePitchMidi(pitch: string): number | null {
  const m = RE_PITCH.exec(pitch.trim());
  if (!m) return null;
  const key = m[1].toUpperCase() + m[2];
  const semitone = NOTE_TO_SEMITONE[key];
  if (semitone === undefined) return null;
  const octave = Number(m[3]);
  return (octave + 1) * 12 + semitone;
}

export function midiToPitch(midi: number): string {
  const clamped = Math.max(12, Math.min(119, Math.round(midi)));
  const octave = Math.floor(clamped / 12) - 1;
  const note = SHARP_NOTES[((clamped % 12) + 12) % 12];
  return `${note}${octave}`;
}

export function transposePitch(pitch: string, semitones: number): string {
  const midi = parsePitchMidi(pitch);
  if (midi === null) return pitch;
  return midiToPitch(midi + semitones);
}

const LENGTH_TO_IN: Record<LengthUnit, number> = {
  in: 1,
  mm: 1 / 25.4,
  cm: 1 / 2.54,
};

export function convertLength(
  val: number,
  from: LengthUnit,
  to: LengthUnit,
): number {
  if (from === to || !Number.isFinite(val)) return val;
  const inches = val * LENGTH_TO_IN[from];
  const out = inches / LENGTH_TO_IN[to];
  return Number(out.toPrecision(5));
}

const TENSION_TO_LBF: Record<TensionUnit, number> = {
  lbf: 1,
  kgf: 2.20462262185,
  N: 1 / 4.44822161526,
};

export function convertTension(
  val: number,
  from: TensionUnit,
  to: TensionUnit,
): number {
  if (from === to || !Number.isFinite(val)) return val;
  const lbf = val * TENSION_TO_LBF[from];
  const out = lbf / TENSION_TO_LBF[to];
  return Math.round(out * 100) / 100;
}

export function fmtNum(val: number | null | undefined, digits = 2): string {
  if (val === null || val === undefined || !Number.isFinite(val)) return "—";
  return val.toFixed(digits);
}

export function fmtGaugeIn(gIn: number | null): string {
  if (gIn === null || !Number.isFinite(gIn)) return "—";
  const s = gIn.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
  return `${s.startsWith("0.") ? s.slice(1) : s}"`;
}

export function stateFromPreset(preset: Preset, n = 5): GaugeSuggestState {
  const fanned: FannedConfig = {
    ...DEFAULT_FANNED,
    ...(preset.fanned ?? {}),
  };
  return {
    preset: preset.id,
    lengthUnit: preset.lengthUnit,
    tensionUnit: preset.tensionUnit,
    n,
    L: preset.L,
    types: [...preset.types],
    strings: preset.strings.map((s) => ({
      pitch: s.pitch,
      T: s.T,
      L: s.L ?? preset.L,
    })),
    fanned,
  };
}
