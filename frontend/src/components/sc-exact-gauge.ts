import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { sharedStyles } from "../styles";
import type {
  Catalog,
  DensityUnit,
  ExactGaugeResponse,
  ExactGaugeState,
  ScaleLengthUnit,
  TensionUnit,
} from "../types";
import {
  convertLength,
  convertTension,
  fmtNum,
  fmtPitchSub,
  normalizePitch,
  transposePitch,
} from "../units";

@customElement("sc-exact-gauge")
export class ScExactGauge extends LitElement {
  static styles = [
    sharedStyles,
    css`
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 0.7rem;
        align-items: end;
      }

      .pitch-group {
        display: flex;
        gap: 0.25rem;
      }

      .pitch-group input {
        width: 100%;
        font-family: var(--sc-mono);
        font-weight: 600;
      }
    `,
  ];

  @property({ type: Number }) T = 16;
  @property({ type: String }) tensionUnit: TensionUnit = "lbf";
  @property({ type: Number }) L = 22.5;
  @property({ type: String }) lengthUnit: ScaleLengthUnit = "in";
  @property({ type: String }) pitch = "E4";
  @property({ type: String }) material = "plain steel";
  @property({ type: Number }) customDensity = 1.3;
  @property({ type: String }) densityUnit: DensityUnit = "g/cm^3";
  @property({ type: Object }) catalog: Catalog | null = null;
  @property({ type: Object }) result: ExactGaugeResponse | null = null;
  @property({ type: Boolean }) loading = false;

  private emitState(patch: Partial<ExactGaugeState>) {
    const next: ExactGaugeState = {
      T: patch.T ?? this.T,
      tensionUnit: patch.tensionUnit ?? this.tensionUnit,
      L: patch.L ?? this.L,
      lengthUnit: patch.lengthUnit ?? this.lengthUnit,
      pitch: patch.pitch ?? this.pitch,
      material: patch.material ?? this.material,
      customDensity: patch.customDensity ?? this.customDensity,
      densityUnit: patch.densityUnit ?? this.densityUnit,
    };
    Object.assign(this, next);
    this.dispatchEvent(
      new CustomEvent<ExactGaugeState>("sc-change", {
        detail: next,
        bubbles: true,
        composed: true,
      }),
    );
  }

  render() {
    const materials = Object.keys(
      this.catalog?.densities ?? {
        "plain steel": 0.285,
        "plain nylon": 0.0412,
      },
    );

    return html`
      <div class="sc-section">
        <div class="grid">
          <div class="sc-field">
            <label for="eg-T">Tension</label>
            <div class="sc-row" style="gap: 0.35rem; flex-wrap: nowrap">
              <input
                id="eg-T"
                type="number"
                inputmode="decimal"
                step="any"
                style="width: 100%"
                .value=${String(this.T)}
                @change=${(e: Event) =>
                  this.emitState({
                    T: Number((e.target as HTMLInputElement).value),
                  })}
              />
              <select
                aria-label="Tension unit"
                .value=${this.tensionUnit}
                @change=${(e: Event) => {
                  const u = (e.target as HTMLSelectElement)
                    .value as TensionUnit;
                  this.emitState({
                    tensionUnit: u,
                    T: convertTension(this.T, this.tensionUnit, u),
                  });
                }}
              >
                <option value="lbf" ?selected=${this.tensionUnit === "lbf"}>
                  lbf
                </option>
                <option value="kgf" ?selected=${this.tensionUnit === "kgf"}>
                  kgf
                </option>
                <option value="N" ?selected=${this.tensionUnit === "N"}>
                  N
                </option>
              </select>
            </div>
          </div>

          <div class="sc-field">
            <label for="eg-L">Scale length</label>
            <div class="sc-row" style="gap: 0.35rem; flex-wrap: nowrap">
              <input
                id="eg-L"
                type="number"
                inputmode="decimal"
                step="any"
                style="width: 100%"
                .value=${String(this.L)}
                @change=${(e: Event) =>
                  this.emitState({
                    L: Number((e.target as HTMLInputElement).value),
                  })}
              />
              <select
                aria-label="Scale length unit"
                .value=${this.lengthUnit}
                @change=${(e: Event) => {
                  const u = (e.target as HTMLSelectElement)
                    .value as ScaleLengthUnit;
                  this.emitState({
                    lengthUnit: u,
                    L: convertLength(this.L, this.lengthUnit, u),
                  });
                }}
              >
                <option value="in" ?selected=${this.lengthUnit === "in"}>
                  in
                </option>
                <option value="mm" ?selected=${this.lengthUnit === "mm"}>
                  mm
                </option>
              </select>
            </div>
          </div>

          <div class="sc-field">
            <label for="eg-pitch">Pitch</label>
            <div class="pitch-group">
              <button
                type="button"
                aria-label="Lower pitch"
                @click=${() => this.emitState({ pitch: transposePitch(this.pitch, -1) })}
              >
                −
              </button>
              <input
                id="eg-pitch"
                type="text"
                .value=${fmtPitchSub(this.pitch)}
                @change=${(e: Event) => {
                  const input = e.target as HTMLInputElement;
                  const pitch = normalizePitch(input.value);
                  input.value = fmtPitchSub(pitch);
                  this.emitState({ pitch });
                }}
              />
              <button
                type="button"
                aria-label="Raise pitch"
                @click=${() => this.emitState({ pitch: transposePitch(this.pitch, 1) })}
              >
                +
              </button>
            </div>
          </div>

          <div class="sc-field">
            <label for="eg-mat">Material</label>
            <select
              id="eg-mat"
              .value=${this.material}
              @change=${(e: Event) =>
                this.emitState({
                  material: (e.target as HTMLSelectElement).value,
                })}
            >
              ${materials.map(
                (m) =>
                  html`<option value=${m} ?selected=${m === this.material}>
                    ${m}
                  </option>`,
              )}
              <option value="custom" ?selected=${this.material === "custom"}>
                Custom density…
              </option>
            </select>
          </div>
        </div>

        ${
          this.material === "custom"
            ? html`
                <div class="sc-row">
                  <div class="sc-field">
                    <label for="eg-rho">Density</label>
                    <input
                      id="eg-rho"
                      type="number"
                      inputmode="decimal"
                      step="any"
                      style="width: 7.5rem"
                      .value=${String(this.customDensity)}
                      @change=${(e: Event) =>
                        this.emitState({
                          customDensity: Number(
                            (e.target as HTMLInputElement).value,
                          ),
                        })}
                    />
                  </div>
                  <div class="sc-field">
                    <label for="eg-rhou">Density unit</label>
                    <select
                      id="eg-rhou"
                      .value=${this.densityUnit}
                      @change=${(e: Event) =>
                        this.emitState({
                          densityUnit: (e.target as HTMLSelectElement)
                            .value as DensityUnit,
                        })}
                    >
                      <option
                        value="g/cm^3"
                        ?selected=${this.densityUnit === "g/cm^3"}
                      >
                        g/cm³
                      </option>
                      <option
                        value="kg/m^3"
                        ?selected=${this.densityUnit === "kg/m^3"}
                      >
                        kg/m³
                      </option>
                      <option
                        value="lbm/in^3"
                        ?selected=${this.densityUnit === "lbm/in^3"}
                      >
                        lbm/in³
                      </option>
                    </select>
                  </div>
                </div>
              `
            : nothing
        }
        ${
          this.result?.error
            ? html`<div class="sc-alert sc-alert-error">
                ${this.result.error}
              </div>`
            : this.result?.gauge_in != null
              ? html`
                  <div class="sc-result-box sc-mono" aria-live="polite">
                    Gauge: ${fmtNum(this.result.gauge_in, 4)}" =
                    ${fmtNum(this.result.gauge_mm, 3)} mm
                  </div>
                `
              : this.loading
                ? html`<div class="sc-muted" style="font-size: 0.85rem">
                    Computing…
                  </div>`
                : nothing
        }
      </div>
    `;
  }
}
