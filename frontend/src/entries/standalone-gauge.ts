import "../standalone.css";
import "../components/sc-gauge-suggest";

import defaultPresets from "../../../stringcalc/data/presets.json";
import { createBackend } from "../backend";
import type { ScGaugeSuggest } from "../components/sc-gauge-suggest";
import type { GaugeSuggestState, Preset } from "../types";
import { createUrlSyncer, paramsToState } from "../url-state";
import {
  createStatusUpdater,
  setFooterRuntime,
  setFooterVersion,
  wireCalc,
} from "./standalone-util";

const presets = defaultPresets as Preset[];
const widget = document.getElementById("gauge-widget") as ScGaugeSuggest;
const copyBtn = document.getElementById("copy-link-btn") as HTMLButtonElement;
const setStatus = createStatusUpdater();

let currentState: GaugeSuggestState = paramsToState(
  new URLSearchParams(window.location.search),
  presets,
);

Object.assign(widget, currentState);
widget.loading = true;

const urlSync = createUrlSyncer(presets);
const backend = createBackend(setStatus, setFooterRuntime);

const runner = wireCalc(
  widget,
  "results",
  (state: GaugeSuggestState) => backend.suggestGauge(state),
  (error) => ({ error, strings: [] }),
  (state) => {
    currentState = state;
    urlSync.sync(state);
  },
);

copyBtn.addEventListener("click", async () => {
  urlSync.flush(currentState);
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

void (async () => {
  try {
    const catalog = await backend.getCatalog();
    widget.catalog = catalog;
    setFooterVersion(catalog.version);
    await runner.run(currentState);
  } catch (err) {
    setStatus("error", "Failed to load");
    runner.fail(err instanceof Error ? err.message : String(err), currentState);
  }
})();
