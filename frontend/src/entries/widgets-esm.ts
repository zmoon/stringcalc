import "../components/sc-exact-gauge";
import "../components/sc-frets";
import "../components/sc-gauge-suggest";
import "../components/sc-scale-length";

import type { ScExactGauge } from "../components/sc-exact-gauge";
import type { ScFrets } from "../components/sc-frets";
import type { ScGaugeSuggest } from "../components/sc-gauge-suggest";
import type { ScScaleLength } from "../components/sc-scale-length";
import type {
  ExactGaugeState,
  FretsState,
  GaugeSuggestState,
  ScaleLengthState,
} from "../types";

interface AnyWidgetModel {
  get(key: string): unknown;
  set(key: string, value: unknown): void;
  save_changes(): void;
  on(event: string, cb: () => void): void;
  off(event: string, cb: () => void): void;
}

function mountHost(el: HTMLElement): HTMLDivElement {
  const wrap = document.createElement("div");
  wrap.style.setProperty(
    "--sc-accent",
    "var(--jp-brand-color1, var(--vscode-focusBorder, #b87333))",
  );
  wrap.style.padding = "4px 0";
  el.appendChild(wrap);
  return wrap;
}

function renderGaugeSuggest(
  model: AnyWidgetModel,
  wrap: HTMLElement,
): () => void {
  const widget = document.createElement("sc-gauge-suggest") as ScGaugeSuggest;
  let syncingFromUI = false;

  const syncAllFromModel = () => {
    if (syncingFromUI) return;
    widget.preset = String(model.get("preset") ?? "");
    widget.lengthUnit =
      (model.get("length_unit") as ScGaugeSuggest["lengthUnit"]) ?? "in";
    widget.tensionUnit =
      (model.get("tension_unit") as ScGaugeSuggest["tensionUnit"]) ?? "lbf";
    widget.n = Number(model.get("n") ?? 5);
    widget.L = Number(model.get("L") ?? 25.5);
    widget.types = (model.get("types") as string[]) ?? [];
    widget.strings = (model.get("strings") as ScGaugeSuggest["strings"]) ?? [];
    widget.fanned =
      (model.get("fanned") as ScGaugeSuggest["fanned"]) ?? widget.fanned;
    widget.catalog =
      (model.get("catalog") as ScGaugeSuggest["catalog"]) ?? null;
  };

  const syncResults = () => {
    widget.results =
      (model.get("results") as ScGaugeSuggest["results"]) ?? null;
  };

  syncAllFromModel();
  syncResults();

  const inputTraits = [
    "preset",
    "length_unit",
    "tension_unit",
    "n",
    "L",
    "types",
    "strings",
    "fanned",
    "catalog",
  ];
  for (const t of inputTraits) model.on(`change:${t}`, syncAllFromModel);
  model.on("change:results", syncResults);

  const onUiChange = (e: Event) => {
    const s = (e as CustomEvent<GaugeSuggestState>).detail;
    syncingFromUI = true;
    try {
      model.set("preset", s.preset);
      model.set("length_unit", s.lengthUnit);
      model.set("tension_unit", s.tensionUnit);
      model.set("n", s.n);
      model.set("L", s.L);
      model.set("types", s.types);
      model.set("strings", s.strings);
      model.set("fanned", s.fanned);
      model.save_changes();
    } finally {
      syncingFromUI = false;
    }
  };

  widget.addEventListener("sc-change", onUiChange);
  wrap.appendChild(widget);

  return () => {
    widget.removeEventListener("sc-change", onUiChange);
    for (const t of inputTraits) model.off(`change:${t}`, syncAllFromModel);
    model.off("change:results", syncResults);
    wrap.remove();
  };
}

function renderExactGauge(
  model: AnyWidgetModel,
  wrap: HTMLElement,
): () => void {
  const widget = document.createElement("sc-exact-gauge") as ScExactGauge;
  let syncingFromUI = false;

  const syncInputs = () => {
    if (syncingFromUI) return;
    widget.T = Number(model.get("T") ?? 16);
    widget.tensionUnit =
      (model.get("tension_unit") as ScExactGauge["tensionUnit"]) ?? "lbf";
    widget.L = Number(model.get("L") ?? 22.5);
    widget.lengthUnit =
      (model.get("length_unit") as ScExactGauge["lengthUnit"]) ?? "in";
    widget.pitch = String(model.get("pitch") ?? "D3");
    widget.material = String(model.get("material") ?? "plain steel");
    widget.customDensity = Number(model.get("custom_density") ?? 1.3);
    widget.densityUnit =
      (model.get("density_unit") as ScExactGauge["densityUnit"]) ?? "g/cm^3";
    widget.catalog = (model.get("catalog") as ScExactGauge["catalog"]) ?? null;
  };
  const syncResult = () => {
    widget.result = (model.get("result") as ScExactGauge["result"]) ?? null;
  };

  syncInputs();
  syncResult();

  const traits = [
    "T",
    "tension_unit",
    "L",
    "length_unit",
    "pitch",
    "material",
    "custom_density",
    "density_unit",
    "catalog",
  ];
  for (const t of traits) model.on(`change:${t}`, syncInputs);
  model.on("change:result", syncResult);

  const onUiChange = (e: Event) => {
    const s = (e as CustomEvent<ExactGaugeState>).detail;
    syncingFromUI = true;
    try {
      model.set("T", s.T);
      model.set("tension_unit", s.tensionUnit);
      model.set("L", s.L);
      model.set("length_unit", s.lengthUnit);
      model.set("pitch", s.pitch);
      model.set("material", s.material);
      model.set("custom_density", s.customDensity);
      model.set("density_unit", s.densityUnit);
      model.save_changes();
    } finally {
      syncingFromUI = false;
    }
  };

  widget.addEventListener("sc-change", onUiChange);
  wrap.appendChild(widget);

  return () => {
    widget.removeEventListener("sc-change", onUiChange);
    for (const t of traits) model.off(`change:${t}`, syncInputs);
    model.off("change:result", syncResult);
    wrap.remove();
  };
}

function renderFrets(model: AnyWidgetModel, wrap: HTMLElement): () => void {
  const widget = document.createElement("sc-frets") as ScFrets;
  let syncingFromUI = false;

  const syncInputs = () => {
    if (syncingFromUI) return;
    widget.N = Number(model.get("N") ?? 24);
    widget.L = Number(model.get("L") ?? 25.5);
    widget.lengthUnit =
      (model.get("length_unit") as ScFrets["lengthUnit"]) ?? "in";
  };
  const syncResult = () => {
    widget.result = (model.get("result") as ScFrets["result"]) ?? null;
  };

  syncInputs();
  syncResult();

  const traits = ["N", "L", "length_unit"];
  for (const t of traits) model.on(`change:${t}`, syncInputs);
  model.on("change:result", syncResult);

  const onUiChange = (e: Event) => {
    const s = (e as CustomEvent<FretsState>).detail;
    syncingFromUI = true;
    try {
      model.set("N", s.N);
      model.set("L", s.L);
      model.set("length_unit", s.lengthUnit);
      model.save_changes();
    } finally {
      syncingFromUI = false;
    }
  };

  widget.addEventListener("sc-change", onUiChange);
  wrap.appendChild(widget);

  return () => {
    widget.removeEventListener("sc-change", onUiChange);
    for (const t of traits) model.off(`change:${t}`, syncInputs);
    model.off("change:result", syncResult);
    wrap.remove();
  };
}

function renderScaleLength(
  model: AnyWidgetModel,
  wrap: HTMLElement,
): () => void {
  const widget = document.createElement("sc-scale-length") as ScScaleLength;
  let syncingFromUI = false;

  const syncInputs = () => {
    if (syncingFromUI) return;
    widget.a = String(model.get("a") ?? "nut");
    widget.b = String(model.get("b") ?? "1");
    widget.d = Number(model.get("d") ?? 1.4);
    widget.lengthUnit =
      (model.get("length_unit") as ScScaleLength["lengthUnit"]) ?? "in";
  };
  const syncResult = () => {
    widget.result = (model.get("result") as ScScaleLength["result"]) ?? null;
  };

  syncInputs();
  syncResult();

  const traits = ["a", "b", "d", "length_unit"];
  for (const t of traits) model.on(`change:${t}`, syncInputs);
  model.on("change:result", syncResult);

  const onUiChange = (e: Event) => {
    const s = (e as CustomEvent<ScaleLengthState>).detail;
    syncingFromUI = true;
    try {
      model.set("a", s.a);
      model.set("b", s.b);
      model.set("d", s.d);
      model.set("length_unit", s.lengthUnit);
      model.save_changes();
    } finally {
      syncingFromUI = false;
    }
  };

  widget.addEventListener("sc-change", onUiChange);
  wrap.appendChild(widget);

  return () => {
    widget.removeEventListener("sc-change", onUiChange);
    for (const t of traits) model.off(`change:${t}`, syncInputs);
    model.off("change:result", syncResult);
    wrap.remove();
  };
}

export default {
  render({ model, el }: { model: AnyWidgetModel; el: HTMLElement }) {
    const wrap = mountHost(el);
    const kind = String(model.get("_widget_name") ?? "");
    switch (kind) {
      case "gauge-suggest":
        return renderGaugeSuggest(model, wrap);
      case "exact-gauge":
        return renderExactGauge(model, wrap);
      case "frets":
        return renderFrets(model, wrap);
      case "scale-length":
        return renderScaleLength(model, wrap);
      default:
        wrap.textContent = `Unknown stringcalc widget: ${kind}`;
        return () => wrap.remove();
    }
  },
};
