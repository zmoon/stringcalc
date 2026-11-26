import { describe, expect, it } from "vitest";
import "./components/sc-exact-gauge";
import "./components/sc-frets";
import "./components/sc-gauge-suggest";
import "./components/sc-scale-length";
import type { ScExactGauge } from "./components/sc-exact-gauge";
import type { ScFrets } from "./components/sc-frets";
import type { ScGaugeSuggest } from "./components/sc-gauge-suggest";
import type { ScScaleLength } from "./components/sc-scale-length";
import type { ScTypePicker } from "./components/sc-type-picker";

describe("Lit custom elements", () => {
  it("renders sc-gauge-suggest and emits sc-change on add string", async () => {
    const el = document.createElement("sc-gauge-suggest") as ScGaugeSuggest;
    document.body.appendChild(el);
    await el.updateComplete;

    let emitted: CustomEvent | null = null;
    el.addEventListener("sc-change", (e) => {
      emitted = e as CustomEvent;
    });

    const initialCount = el.strings.length;
    const addBtn = el.shadowRoot!.querySelector(
      "button.sc-btn-primary",
    ) as HTMLButtonElement;
    expect(addBtn).toBeTruthy();
    addBtn.click();
    await el.updateComplete;

    expect(el.strings.length).toBe(initialCount + 1);
    expect(emitted).not.toBeNull();
    el.remove();
  });

  it("resets clicked gauge selection when inputs change", async () => {
    const el = document.createElement("sc-gauge-suggest") as ScGaugeSuggest;
    el.results = {
      error: null,
      lengthUnit: "in",
      tensionUnit: "lbf",
      strings: [
        {
          index: 0,
          pitch: "E2",
          L: 25.5,
          T_target: 16.5,
          bestIndex: 0,
          warnings: [],
          error: null,
          suggestions: [
            {
              id: "DA:PB042",
              group_id: "DA:PB",
              gauge_in: 0.042,
              gauge_mm: 1.07,
              T: 16.5,
              dT: 0,
            },
            {
              id: "DA:PB045",
              group_id: "DA:PB",
              gauge_in: 0.045,
              gauge_mm: 1.14,
              T: 19.1,
              dT: 2.6,
            },
          ],
        },
      ],
    };
    document.body.appendChild(el);
    await el.updateComplete;

    const rows = el.shadowRoot!.querySelectorAll("button.sug-row");
    (rows[1] as HTMLButtonElement).click();
    await el.updateComplete;
    expect(el.shadowRoot!.querySelector(".summary-set")?.textContent).toContain(
      "DA:PB045",
    );

    // Changing state via UI clears stale chosenRows back to bestIndex (0 -> DA:PB042)
    (
      el.shadowRoot!.querySelector(
        "button[title*='Transpose all strings up']",
      ) as HTMLButtonElement
    ).click();
    await el.updateComplete;
    expect(el.shadowRoot!.querySelector(".summary-set")?.textContent).toContain(
      "DA:PB042",
    );
    expect(el.shadowRoot!.querySelector(".res-pitch sub")?.textContent).toBe(
      "2",
    );
    expect(el.shadowRoot!.querySelector(".summary-set sub")?.textContent).toBe(
      "2",
    );
    expect(
      (el.shadowRoot!.querySelector("#pitch-0") as HTMLInputElement).value,
    ).toBe("F₂");
    el.remove();
  });

  it("renders misc tool components and displays results", async () => {
    const eg = document.createElement("sc-exact-gauge") as ScExactGauge;
    eg.result = { gauge_in: 0.0172, gauge_mm: 0.437, error: null };
    document.body.appendChild(eg);
    await eg.updateComplete;
    expect(eg.shadowRoot!.textContent).toContain('0.0172"');
    eg.remove();

    const fr = document.createElement("sc-frets") as ScFrets;
    fr.result = {
      rows: [{ n: 1, d: 1.431, dd: 1.431, d_inv: 24.069 }],
      lengthUnit: "in",
      error: null,
    };
    document.body.appendChild(fr);
    await fr.updateComplete;
    expect(fr.shadowRoot!.textContent).toContain("1.431");
    fr.remove();

    const sl = document.createElement("sc-scale-length") as ScScaleLength;
    sl.result = {
      L: 25.5,
      L_in: 25.5,
      L_mm: 647.7,
      lengthUnit: "in",
      error: null,
    };
    document.body.appendChild(sl);
    await sl.updateComplete;
    expect(sl.shadowRoot!.textContent).toContain('25.50"');
    sl.remove();
  });

  it("shows selected string type descriptions inline in sc-type-picker", async () => {
    const picker = document.createElement("sc-type-picker") as ScTypePicker;
    picker.selected = ["DA:PB"];
    picker.catalogTypes = [
      {
        id: "DA:PB",
        brand: "D'Addario (Chart)",
        label: "Acoustic Guitar - Phosphor Bronze",
      },
    ];
    document.body.appendChild(picker);
    await picker.updateComplete;
    expect(
      picker.shadowRoot!.querySelector(".selected-legend")?.textContent,
    ).toContain("D'Addario (Chart): Acoustic Guitar - Phosphor Bronze");
    picker.remove();
  });

  it("shows a consistent loading placeholder across all tool widgets", async () => {
    for (const tag of [
      "sc-gauge-suggest",
      "sc-exact-gauge",
      "sc-frets",
      "sc-scale-length",
    ]) {
      const el = document.createElement(tag) as HTMLElement & {
        loading: boolean;
        updateComplete: Promise<boolean>;
      };
      el.loading = true;
      document.body.appendChild(el);
      await el.updateComplete;
      expect(
        el.shadowRoot!.querySelector(".sc-loading-note")?.textContent?.trim(),
      ).toBe("Waiting for Python…");
      el.remove();
    }
  });
});
