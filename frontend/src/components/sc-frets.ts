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
        max-width: 30rem;
        overflow-x: auto;
        border: 1px solid var(--sc-border);
        border-radius: var(--sc-radius-sm);
      }

      table {
        width: 100%;
        min-width: 18rem;
        table-layout: fixed;
        border-collapse: collapse;
        font-size: 0.86rem;
        font-family: var(--sc-mono);
        font-variant-numeric: tabular-nums;
      }

      th,
      td {
        padding: 0.36rem 0.5rem;
        border-bottom: 1px solid var(--sc-border);
        text-align: right;
      }

      thead th {
        font-size: 0.76rem;
        font-weight: 600;
        white-space: nowrap;
        background: var(--sc-surface);
        color: var(--sc-muted);
        border-bottom: 1px solid var(--sc-border-strong);
      }

      thead th:first-child {
        width: 3rem;
      }

      tbody tr:hover {
        background: var(--sc-surface-hover);
      }

      tbody tr:last-child td {
        border-bottom: 0;
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
                    <table>
                      <thead>
                        <tr>
                          <th>n</th>
                          <th>d (${u})</th>
                          <th>Δd (${u})</th>
                          <th>L−d (${u})</th>
                        </tr>
                      </thead>
                      <tbody>
                        ${this.result.rows.map(
                          (r) => html`
                            <tr>
                              <td>${r.n}</td>
                              <td>${fmtNum(r.d, digits)}</td>
                              <td>${fmtNum(r.dd, digits)}</td>
                              <td>${fmtNum(r.d_inv, digits)}</td>
                            </tr>
                          `,
                        )}
                      </tbody>
                    </table>
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
