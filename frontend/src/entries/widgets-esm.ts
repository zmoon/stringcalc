import "../components/sc-exact-gauge";
import "../components/sc-frets";
import "../components/sc-gauge-suggest";
import "../components/sc-scale-length";

interface AnyWidgetModel {
  get(key: string): unknown;
  set(key: string, value: unknown): void;
  save_changes(): void;
  on(event: string, cb: () => void): void;
  off(event: string, cb: () => void): void;
}

interface WidgetSpec {
  tag: string;
  /** Mapping of `[pythonTraitName, elementPropertyName]`. */
  inputs: ReadonlyArray<readonly [string, string]>;
  extraReadOnly?: readonly string[];
  resultTrait: string;
}

const WIDGET_SPECS: Record<string, WidgetSpec> = {
  "gauge-suggest": {
    tag: "sc-gauge-suggest",
    inputs: [
      ["preset", "preset"],
      ["length_unit", "lengthUnit"],
      ["tension_unit", "tensionUnit"],
      ["n", "n"],
      ["L", "L"],
      ["types", "types"],
      ["strings", "strings"],
      ["fanned", "fanned"],
    ],
    extraReadOnly: ["catalog"],
    resultTrait: "results",
  },
  "exact-gauge": {
    tag: "sc-exact-gauge",
    inputs: [
      ["T", "T"],
      ["tension_unit", "tensionUnit"],
      ["L", "L"],
      ["length_unit", "lengthUnit"],
      ["pitch", "pitch"],
      ["material", "material"],
      ["custom_density", "customDensity"],
      ["density_unit", "densityUnit"],
    ],
    extraReadOnly: ["catalog"],
    resultTrait: "result",
  },
  frets: {
    tag: "sc-frets",
    inputs: [
      ["N", "N"],
      ["L", "L"],
      ["length_unit", "lengthUnit"],
    ],
    resultTrait: "result",
  },
  "scale-length": {
    tag: "sc-scale-length",
    inputs: [
      ["a", "a"],
      ["b", "b"],
      ["d", "d"],
      ["length_unit", "lengthUnit"],
    ],
    resultTrait: "result",
  },
};

function mountWidget(
  model: AnyWidgetModel,
  wrap: HTMLElement,
  spec: WidgetSpec,
): () => void {
  const widget = document.createElement(spec.tag) as unknown as Record<
    string,
    unknown
  > &
    HTMLElement;
  let syncingFromUI = false;

  const syncInputs = () => {
    if (syncingFromUI) return;
    for (const [trait, prop] of spec.inputs) {
      const val = model.get(trait);
      if (val !== undefined) widget[prop] = val;
    }
    for (const trait of spec.extraReadOnly ?? []) {
      widget[trait] = model.get(trait) ?? null;
    }
  };

  const syncResult = () => {
    widget[spec.resultTrait] = model.get(spec.resultTrait) ?? null;
  };

  syncInputs();
  syncResult();

  const watchedInputs = [
    ...spec.inputs.map(([t]) => t),
    ...(spec.extraReadOnly ?? []),
  ];
  for (const t of watchedInputs) model.on(`change:${t}`, syncInputs);
  model.on(`change:${spec.resultTrait}`, syncResult);

  const onUiChange = (e: Event) => {
    const detail = (e as CustomEvent<Record<string, unknown>>).detail;
    syncingFromUI = true;
    try {
      for (const [trait, prop] of spec.inputs) {
        model.set(trait, detail[prop]);
      }
      model.save_changes();
    } finally {
      syncingFromUI = false;
    }
  };

  widget.addEventListener("sc-change", onUiChange);
  wrap.appendChild(widget);

  return () => {
    widget.removeEventListener("sc-change", onUiChange);
    for (const t of watchedInputs) model.off(`change:${t}`, syncInputs);
    model.off(`change:${spec.resultTrait}`, syncResult);
    wrap.remove();
  };
}

export default {
  render({ model, el }: { model: AnyWidgetModel; el: HTMLElement }) {
    const wrap = document.createElement("div");
    wrap.style.setProperty(
      "--sc-accent",
      "var(--jp-brand-color1, var(--vscode-focusBorder, #b87333))",
    );
    wrap.style.padding = "4px 0";
    el.appendChild(wrap);

    const kind = String(model.get("_widget_name") ?? "");
    const spec = WIDGET_SPECS[kind];
    if (!spec) {
      wrap.textContent = `Unknown stringcalc widget: ${kind}`;
      return () => wrap.remove();
    }
    return mountWidget(model, wrap, spec);
  },
};
