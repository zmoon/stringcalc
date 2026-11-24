import "../standalone.css";
import "../components/sc-exact-gauge";
import "../components/sc-frets";
import "../components/sc-scale-length";

import { PyodideBackend } from "../backend/pyodide-backend";
import type { ScExactGauge } from "../components/sc-exact-gauge";
import type { ScFrets } from "../components/sc-frets";
import type { ScScaleLength } from "../components/sc-scale-length";
import type { ExactGaugeState, FretsState, ScaleLengthState } from "../types";
import {
  createStatusUpdater,
  setFooterVersion,
  wireCalc,
} from "./standalone-util";

const exactEl = document.getElementById("exact-gauge-widget") as ScExactGauge;
const fretsEl = document.getElementById("frets-widget") as ScFrets;
const scaleEl = document.getElementById("scale-length-widget") as ScScaleLength;
const setStatus = createStatusUpdater();
const backend = new PyodideBackend(setStatus);

const exactState = (): ExactGaugeState => ({
  T: exactEl.T,
  tensionUnit: exactEl.tensionUnit,
  L: exactEl.L,
  lengthUnit: exactEl.lengthUnit,
  pitch: exactEl.pitch,
  material: exactEl.material,
  customDensity: exactEl.customDensity,
  densityUnit: exactEl.densityUnit,
});
const fretsState = (): FretsState => ({
  N: fretsEl.N,
  L: fretsEl.L,
  lengthUnit: fretsEl.lengthUnit,
});
const scaleState = (): ScaleLengthState => ({
  a: scaleEl.a,
  b: scaleEl.b,
  d: scaleEl.d,
  lengthUnit: scaleEl.lengthUnit,
});

const exact = wireCalc(
  exactEl,
  "result",
  (s: ExactGaugeState) => backend.exactGauge(s),
  (error) => ({ gauge_in: null, gauge_mm: null, error }),
);
const frets = wireCalc(
  fretsEl,
  "result",
  (s: FretsState) => backend.frets(s),
  (error, s) => ({ rows: [], lengthUnit: s.lengthUnit, error }),
);
const scale = wireCalc(
  scaleEl,
  "result",
  (s: ScaleLengthState) => backend.scaleLength(s),
  (error, s) => ({
    L: null,
    L_in: null,
    L_mm: null,
    lengthUnit: s.lengthUnit,
    error,
  }),
);

exactEl.loading = fretsEl.loading = scaleEl.loading = true;

void (async () => {
  try {
    const catalog = await backend.getCatalog();
    exactEl.catalog = catalog;
    setFooterVersion(catalog.version);
    await Promise.all([
      exact.run(exactState()),
      frets.run(fretsState()),
      scale.run(scaleState()),
    ]);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    setStatus("error", "Failed to load");
    exact.fail(msg, exactState());
    frets.fail(msg, fretsState());
    scale.fail(msg, scaleState());
  }
})();
