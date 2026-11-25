export type LengthUnit = "in" | "mm" | "cm";
export type ScaleLengthUnit = "in" | "mm";
export type TensionUnit = "lbf" | "kgf" | "N";
export type DensityUnit = "lbm/in^3" | "g/cm^3" | "kg/m^3";

export interface FannedConfig {
  enabled: boolean;
  L_bass: number;
  L_treble: number;
  nutWidth: number;
  edgeBass: number | null;
  edgeTreble: number | null;
}

export interface StringInput {
  pitch: string;
  T: number;
  L: number;
}

export interface PresetString {
  pitch: string;
  T: number;
  L?: number;
}

export interface Preset {
  id: string;
  name: string;
  lengthUnit: ScaleLengthUnit;
  tensionUnit: TensionUnit;
  L: number;
  types: string[];
  strings: PresetString[];
  fanned?: Partial<FannedConfig>;
}

export interface StringTypeInfo {
  id: string;
  brand: string;
  label: string;
}

export interface Catalog {
  version: string;
  presets: Preset[];
  stringTypes: StringTypeInfo[];
  densities: Record<string, number>;
}

export interface GaugeSuggestState {
  preset: string;
  lengthUnit: ScaleLengthUnit;
  tensionUnit: TensionUnit;
  n: number;
  L: number;
  types: string[];
  strings: StringInput[];
  fanned: FannedConfig;
}

export interface SuggestionItem {
  id: string;
  group_id: string;
  gauge_in: number | null;
  gauge_mm: number | null;
  T: number;
  dT: number;
}

export interface StringSuggestionResult {
  index: number;
  pitch: string;
  L: number | null;
  T_target: number | null;
  bestIndex: number | null;
  warnings: string[];
  error: string | null;
  suggestions: SuggestionItem[];
}

export interface SuggestGaugeResponse {
  error: string | null;
  lengthUnit?: ScaleLengthUnit;
  tensionUnit?: TensionUnit;
  fannedLengths?: number[] | null;
  strings: StringSuggestionResult[];
}

export interface ExactGaugeState {
  T: number;
  tensionUnit: TensionUnit;
  L: number;
  lengthUnit: ScaleLengthUnit;
  pitch: string;
  material: string;
  customDensity: number;
  densityUnit: DensityUnit;
}

export interface ExactGaugeResponse {
  gauge_in: number | null;
  gauge_mm: number | null;
  error: string | null;
}

export interface FretsState {
  N: number;
  L: number;
  lengthUnit: ScaleLengthUnit;
}

export interface FretRow {
  n: number;
  d: number;
  dd: number;
  d_inv: number;
}

export interface FretsResponse {
  rows: FretRow[];
  lengthUnit: ScaleLengthUnit;
  error: string | null;
}

export interface ScaleLengthState {
  a: string;
  b: string;
  d: number;
  lengthUnit: LengthUnit;
}

export interface ScaleLengthResponse {
  L: number | null;
  L_in: number | null;
  L_mm: number | null;
  lengthUnit: LengthUnit;
  error: string | null;
}

export const DEFAULT_FANNED: FannedConfig = {
  enabled: false,
  L_bass: 27.0,
  L_treble: 25.5,
  nutWidth: 1.89,
  edgeBass: 0.15625,
  edgeTreble: 0.125,
};
