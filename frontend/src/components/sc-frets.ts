import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { sharedStyles } from "../styles";
import type { FretsResponse, FretsState, ScaleLengthUnit } from "../types";
import { convertLength, fmtNum } from "../units";

@customElement("sc-frets")
export class ScFrets extends LitElement {
  static styles = [
    sharedStyles,
    css`
      .table-wrap {
        max-height: 360px;
        overflow-y: auto;
        border: 1px solid var(--sc-border);
        border-radius: var(--sc-radius-sm);
      }

      .table-wrap thead th {
        position: sticky;
        top: 0;
        background: var(--sc-bg, Canvas);
        z-index: 1;
      }
    `,
  ];

  @property({ type: Number }) N = 24;
  @property({ type: Number }) L = 25.5;
  @property({ type: String }) lengthUnit: ScaleLengthUnit = "in";
  @property({ type: Object }) result: FretsResponse | null = null;
  @property({ type: Boolean }) loading = false;

  private emitState(patch: Partial<FretsState>) {
    const next: FretsState = {
      N: patch.N ?? this.N,
      L: patch.L ?? this.L,
      lengthUnit: patch.lengthUnit ?? this.lengthUnit,
    };
    Object.assign(this, next);
    this.dispatchEvent(
      new CustomEvent<FretsState>("sc-change", {
        detail: next,
        bubbles: true,
        composed: true,
      }),
    );
  }

  render() {
    const u = this.result?.lengthUnit ?? this.lengthUnit;
    const digits = u === "mm" ? 2 : 3;

    return html`
      <div class="sc-section">
        <div class="sc-row">
          <div class="sc-field">
            <label for="fr-L">Scale length</label>
            <div class="sc-row" style="gap: 0.35rem; flex-wrap: nowrap">
              <input
                id="fr-L"
                type="number"
                inputmode="decimal"
                step="any"
                style="width: 7.5rem"
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
                  const nextU = (e.target as HTMLSelectElement)
                    .value as ScaleLengthUnit;
                  this.emitState({
                    lengthUnit: nextU,
                    L: convertLength(this.L, this.lengthUnit, nextU),
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
            <label for="fr-N">Number of frets</label>
            <input
              id="fr-N"
              type="number"
              inputmode="numeric"
              min="1"
              max="48"
              style="width: 5.5rem"
              .value=${String(this.N)}
              @change=${(e: Event) =>
                this.emitState({
                  N: Number.parseInt((e.target as HTMLInputElement).value, 10),
                })}
            />
          </div>
        </div>

        ${
          this.result?.error
            ? html`<div class="sc-alert sc-alert-error">
                ${this.result.error}
              </div>`
            : this.result?.rows?.length
              ? html`
                  <div class="table-wrap">
                    <table class="sc-table">
                      <thead>
                        <tr>
                          <th class="num">n</th>
                          <th class="num">d (${u})</th>
                          <th class="num">Δd (${u})</th>
                          <th class="num">L−d (${u})</th>
                        </tr>
                      </thead>
                      <tbody>
                        ${this.result.rows.map(
                          (r) => html`
                            <tr>
                              <td class="num">${r.n}</td>
                              <td class="num">${fmtNum(r.d, digits)}</td>
                              <td class="num">${fmtNum(r.dd, digits)}</td>
                              <td class="num">${fmtNum(r.d_inv, digits)}</td>
                            </tr>
                          `,
                        )}
                      </tbody>
                    </table>
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
