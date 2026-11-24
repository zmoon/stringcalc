import "../standalone.css";
import "../components/sc-exact-gauge";
import "../components/sc-frets";
import "../components/sc-scale-length";

import { PyodideBackend } from "../backend/pyodide-backend";
import type { ScExactGauge } from "../components/sc-exact-gauge";
import type { ScFrets } from "../components/sc-frets";
import type { ScScaleLength } from "../components/sc-scale-length";
import type { ExactGaugeState, FretsState, ScaleLengthState } from "../types";

const exactEl = document.getElementById("exact-gauge-widget") as ScExactGauge;
const fretsEl = document.getElementById("frets-widget") as ScFrets;
const scaleEl = document.getElementById("scale-length-widget") as ScScaleLength;
const statusPill = document.getElementById("status-pill") as HTMLElement;
const statusText = document.getElementById("status-text") as HTMLElement;
const versionEl = document.getElementById("sc-version") as HTMLElement;

function setStatus(phase: string, msg: string) {
  statusPill.dataset.state = phase;
  statusText.textContent = msg;
}

const backend = new PyodideBackend(setStatus);

let exactSeq = 0;
async function computeExact(state: ExactGaugeState) {
  const seq = ++exactSeq;
  exactEl.loading = true;
  try {
    const res = await backend.exactGauge(state);
    if (seq === exactSeq) {
      exactEl.result = res;
      exactEl.loading = false;
    }
  } catch (err) {
    if (seq === exactSeq) {
      exactEl.result = {
        gauge_in: null,
        gauge_mm: null,
        error: err instanceof Error ? err.message : String(err),
      };
      exactEl.loading = false;
    }
  }
}

let fretsSeq = 0;
async function computeFrets(state: FretsState) {
  const seq = ++fretsSeq;
  fretsEl.loading = true;
  try {
    const res = await backend.frets(state);
    if (seq === fretsSeq) {
      fretsEl.result = res;
      fretsEl.loading = false;
    }
  } catch (err) {
    if (seq === fretsSeq) {
      fretsEl.result = {
        rows: [],
        lengthUnit: state.lengthUnit,
        error: err instanceof Error ? err.message : String(err),
      };
      fretsEl.loading = false;
    }
  }
}

let scaleSeq = 0;
async function computeScale(state: ScaleLengthState) {
  const seq = ++scaleSeq;
  scaleEl.loading = true;
  try {
    const res = await backend.scaleLength(state);
    if (seq === scaleSeq) {
      scaleEl.result = res;
      scaleEl.loading = false;
    }
  } catch (err) {
    if (seq === scaleSeq) {
      scaleEl.result = {
        L: null,
        L_in: null,
        L_mm: null,
        lengthUnit: state.lengthUnit,
        error: err instanceof Error ? err.message : String(err),
      };
      scaleEl.loading = false;
    }
  }
}

function readExactState(): ExactGaugeState {
  return {
    T: exactEl.T,
    tensionUnit: exactEl.tensionUnit,
    L: exactEl.L,
    lengthUnit: exactEl.lengthUnit,
    pitch: exactEl.pitch,
    material: exactEl.material,
    customDensity: exactEl.customDensity,
    densityUnit: exactEl.densityUnit,
  };
}

function readFretsState(): FretsState {
  return { N: fretsEl.N, L: fretsEl.L, lengthUnit: fretsEl.lengthUnit };
}

function readScaleState(): ScaleLengthState {
  return {
    a: scaleEl.a,
    b: scaleEl.b,
    d: scaleEl.d,
    lengthUnit: scaleEl.lengthUnit,
  };
}

exactEl.addEventListener("sc-change", (e: Event) => {
  void computeExact((e as CustomEvent<ExactGaugeState>).detail);
});
fretsEl.addEventListener("sc-change", (e: Event) => {
  void computeFrets((e as CustomEvent<FretsState>).detail);
});
scaleEl.addEventListener("sc-change", (e: Event) => {
  void computeScale((e as CustomEvent<ScaleLengthState>).detail);
});

exactEl.loading = true;
fretsEl.loading = true;
scaleEl.loading = true;

void (async () => {
  try {
    const catalog = await backend.getCatalog();
    exactEl.catalog = catalog;
    if (catalog.version) {
      versionEl.textContent = `v${catalog.version}`;
    }
    await Promise.all([
      computeExact(readExactState()),
      computeFrets(readFretsState()),
      computeScale(readScaleState()),
    ]);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    setStatus("error", "Failed to load");
    exactEl.result = { gauge_in: null, gauge_mm: null, error: message };
    fretsEl.result = {
      rows: [],
      lengthUnit: fretsEl.lengthUnit,
      error: message,
    };
    scaleEl.result = {
      L: null,
      L_in: null,
      L_mm: null,
      lengthUnit: scaleEl.lengthUnit,
      error: message,
    };
    exactEl.loading = false;
    fretsEl.loading = false;
    scaleEl.loading = false;
  }
})();
