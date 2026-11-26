import { LitElement, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { sharedStyles } from "../styles";
import type {
  LengthUnit,
  ScaleLengthResponse,
  ScaleLengthState,
} from "../types";
import { convertLength, fmtNum } from "../units";

const FRET_OPTIONS = [
  "nut",
  ...Array.from({ length: 30 }, (_, i) => String(i + 1)),
  "saddle",
];

@customElement("sc-scale-length")
export class ScScaleLength extends LitElement {
  static styles = [sharedStyles];

  @property({ type: String }) a = "nut";
  @property({ type: String }) b = "5";
  @property({ type: Number }) d = 6;
  @property({ type: String }) lengthUnit: LengthUnit = "in";
  @property({ type: Object }) result: ScaleLengthResponse | null = null;
  @property({ type: Boolean }) loading = false;

  private emitState(patch: Partial<ScaleLengthState>) {
    const next: ScaleLengthState = {
      a: patch.a ?? this.a,
      b: patch.b ?? this.b,
      d: patch.d ?? this.d,
      lengthUnit: patch.lengthUnit ?? this.lengthUnit,
    };
    Object.assign(this, next);
    this.dispatchEvent(
      new CustomEvent<ScaleLengthState>("sc-change", {
        detail: next,
        bubbles: true,
        composed: true,
      }),
    );
  }

  private fmtFretLabel(v: string): string {
    if (v === "nut" || v === "saddle") return v;
    return `fret ${v}`;
  }

  render() {
    return html`
      <div class="sc-section">
        <div class="sc-row">
          <div class="sc-field">
            <label for="sl-a">From (a)</label>
            <select
              id="sl-a"
              .value=${this.a}
              @change=${(e: Event) =>
                this.emitState({ a: (e.target as HTMLSelectElement).value })}
            >
              ${FRET_OPTIONS.map(
                (opt) =>
                  html`<option value=${opt} ?selected=${opt === this.a}>
                    ${this.fmtFretLabel(opt)}
                  </option>`,
              )}
            </select>
          </div>

          <div class="sc-field">
            <label for="sl-b">To (b)</label>
            <select
              id="sl-b"
              .value=${this.b}
              @change=${(e: Event) =>
                this.emitState({ b: (e.target as HTMLSelectElement).value })}
            >
              ${FRET_OPTIONS.map(
                (opt) =>
                  html`<option value=${opt} ?selected=${opt === this.b}>
                    ${this.fmtFretLabel(opt)}
                  </option>`,
              )}
            </select>
          </div>

          <div class="sc-field">
            <label for="sl-d">Distance (d)</label>
            <div class="sc-row" style="gap: 0.35rem; flex-wrap: nowrap">
              <input
                id="sl-d"
                type="number"
                inputmode="decimal"
                step="any"
                style="width: 7rem"
                .value=${String(this.d)}
                @change=${(e: Event) =>
                  this.emitState({
                    d: Number((e.target as HTMLInputElement).value),
                  })}
              />
              <select
                aria-label="Distance unit"
                .value=${this.lengthUnit}
                @change=${(e: Event) => {
                  const nextU = (e.target as HTMLSelectElement)
                    .value as LengthUnit;
                  this.emitState({
                    lengthUnit: nextU,
                    d: convertLength(this.d, this.lengthUnit, nextU),
                  });
                }}
              >
                <option value="in" ?selected=${this.lengthUnit === "in"}>
                  in
                </option>
                <option value="mm" ?selected=${this.lengthUnit === "mm"}>
                  mm
                </option>
                <option value="cm" ?selected=${this.lengthUnit === "cm"}>
                  cm
                </option>
              </select>
            </div>
          </div>
        </div>

        ${
          this.result?.error
            ? html`<div class="sc-alert sc-alert-error">
                ${this.result.error}
              </div>`
            : this.result?.L_in != null
              ? html`
                  <div class="sc-result-box sc-mono" aria-live="polite">
                    Scale length: ${fmtNum(this.result.L_in, 2)}"
                    (${fmtNum(this.result.L_mm, 1)} mm)
                  </div>
                `
              : this.loading
                ? html`<div class="sc-loading-note">Waiting for Python…</div>`
                : nothing
        }
      </div>
    `;
  }
}
