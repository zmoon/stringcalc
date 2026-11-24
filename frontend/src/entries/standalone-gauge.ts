import "../standalone.css";
import "../components/sc-gauge-suggest";

import defaultPresets from "../../../stringcalc/data/presets.json";
import { PyodideBackend } from "../backend/pyodide-backend";
import type { ScGaugeSuggest } from "../components/sc-gauge-suggest";
import type { GaugeSuggestState, Preset } from "../types";
import { createUrlSyncer, paramsToState } from "../url-state";

const presets = defaultPresets as Preset[];
const widget = document.getElementById("gauge-widget") as ScGaugeSuggest;
const statusPill = document.getElementById("status-pill") as HTMLElement;
const statusText = document.getElementById("status-text") as HTMLElement;
const versionEl = document.getElementById("sc-version") as HTMLElement;
const copyBtn = document.getElementById("copy-link-btn") as HTMLButtonElement;

function setStatus(phase: string, msg: string) {
  statusPill.dataset.state = phase;
  statusText.textContent = msg;
}

// Hydrate initial state from URL before Pyodide finishes loading
let currentState: GaugeSuggestState = paramsToState(
  new URLSearchParams(window.location.search),
  presets,
);

function applyStateToWidget(s: GaugeSuggestState) {
  widget.preset = s.preset;
  widget.lengthUnit = s.lengthUnit;
  widget.tensionUnit = s.tensionUnit;
  widget.n = s.n;
  widget.L = s.L;
  widget.types = s.types;
  widget.strings = s.strings;
  widget.fanned = s.fanned;
}

applyStateToWidget(currentState);
widget.loading = true;

const syncUrl = createUrlSyncer(presets);
const backend = new PyodideBackend(setStatus);

let reqSeq = 0;

async function compute(state: GaugeSuggestState) {
  const seq = ++reqSeq;
  widget.loading = true;
  try {
    const res = await backend.suggestGauge(state);
    if (seq === reqSeq) {
      widget.results = res;
      widget.loading = false;
    }
  } catch (err) {
    if (seq === reqSeq) {
      widget.results = {
        error: err instanceof Error ? err.message : String(err),
        strings: [],
      };
      widget.loading = false;
    }
  }
}

widget.addEventListener("sc-change", (e: Event) => {
  currentState = (e as CustomEvent<GaugeSuggestState>).detail;
  syncUrl(currentState);
  void compute(currentState);
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(window.location.href);
    const prev = copyBtn.textContent;
    copyBtn.textContent = "Copied!";
    setTimeout(() => {
      copyBtn.textContent = prev;
    }, 1500);
  } catch {
    window.prompt("Copy link:", window.location.href);
  }
});

// Boot Pyodide, fetch full catalog, and compute initial results
void (async () => {
  try {
    const catalog = await backend.getCatalog();
    widget.catalog = catalog;
    if (catalog.version) {
      versionEl.textContent = `v${catalog.version}`;
    }
    await compute(currentState);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    setStatus("error", "Failed to load");
    widget.results = { error: message, strings: [] };
    widget.loading = false;
  }
})();
