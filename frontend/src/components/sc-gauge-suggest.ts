import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import defaultPresets from "../../../stringcalc/data/presets.json";
import { sharedStyles } from "../styles";
import type {
  Catalog,
  FannedConfig,
  GaugeSuggestState,
  Preset,
  ScaleLengthUnit,
  StringInput,
  SuggestGaugeResponse,
  TensionUnit,
} from "../types";
import { DEFAULT_FANNED } from "../types";
import {
  convertLength,
  convertTension,
  fmtGaugeIn,
  fmtNum,
  stateFromPreset,
  transposePitch,
} from "../units";
import "./sc-type-picker";

@customElement("sc-gauge-suggest")
export class ScGaugeSuggest extends LitElement {
  static styles = [
    sharedStyles,
    css`
      .layout {
        display: flex;
        flex-direction: column;
        gap: 1rem;
      }

      .controls-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.75rem;
      }

      @container (min-width: 640px) {
        .controls-grid {
          grid-template-columns: minmax(220px, 1.4fr) auto auto auto;
          align-items: end;
        }
      }

      .scale-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: flex-end;
        padding-top: 0.65rem;
        border-top: 1px solid var(--sc-border);
      }

      .fan-toggle {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.88rem;
        font-weight: 500;
        cursor: pointer;
        min-height: 36px;
      }

      .fan-toggle input {
        min-height: auto;
      }

      .fan-fields {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 0.6rem;
        width: 100%;
      }

      .editor-header {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
      }

      .editor-header h3 {
        margin: 0;
        font-size: 0.95rem;
      }

      .editor-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        align-items: center;
      }

      .strings-list {
        display: flex;
        flex-direction: column;
        gap: 0.55rem;
      }

      .string-row {
        display: grid;
        grid-template-columns: auto 1fr auto;
        gap: 0.5rem;
        padding: 0.6rem;
        border: 1px solid var(--sc-border);
        border-radius: var(--sc-radius-sm);
        background: var(--sc-bg, transparent);
        align-items: end;
      }

      .string-fields {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
      }

      .string-fields .pitch-field {
        grid-column: 1 / -1;
      }

      @container (min-width: 640px) {
        .string-row {
          grid-template-columns: 2rem 1fr auto;
          padding: 0.45rem 0.6rem;
          align-items: center;
        }

        .string-fields {
          grid-template-columns: 1.25fr 1fr 1fr;
          align-items: end;
        }

        .string-fields .pitch-field {
          grid-column: auto;
        }
      }

      .string-num {
        font-family: var(--sc-mono);
        font-size: 0.8rem;
        font-weight: 700;
        color: var(--sc-muted);
        min-width: 1.5rem;
        text-align: center;
      }

      .pitch-group {
        display: flex;
        gap: 0.25rem;
        align-items: stretch;
      }

      .pitch-group input {
        width: 100%;
        min-width: 4.5rem;
        font-family: var(--sc-mono);
        font-weight: 600;
      }

      .nudge-btn {
        min-width: 34px;
        padding: 0 0.4rem;
        font-weight: 700;
      }

      .results-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.75rem;
      }

      @container (min-width: 640px) {
        .results-grid {
          grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
        }
      }

      .res-card {
        border: 1px solid var(--sc-border);
        border-radius: var(--sc-radius);
        background: var(--sc-surface);
        padding: 0.75rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        min-width: 0;
      }

      .sug-list {
        display: flex;
        flex-direction: column;
      }

      .sug-head,
      .sug-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 4.4rem 4rem 3.6rem;
        gap: 0.35rem;
        align-items: center;
        width: 100%;
        padding: 0.32rem 0.4rem;
        font-size: 0.82rem;
        font-variant-numeric: tabular-nums;
        text-align: left;
        border: 0;
        border-bottom: 1px solid var(--sc-border);
        border-radius: 0;
        background: transparent;
      }

      .sug-id {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .sug-head {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--sc-muted);
      }

      .sug-head .num,
      .sug-row .num {
        text-align: right;
        font-family: var(--sc-mono);
        white-space: nowrap;
      }

      .sug-row {
        min-height: 34px;
        justify-content: stretch;
      }

      .sug-row.best {
        background: var(--sc-highlight-bg);
      }

      .sug-row[aria-pressed="true"] {
        background: var(--sc-selected-bg);
        font-weight: 600;
      }

      .sug-row[aria-pressed="true"] .sug-id::before {
        content: "✓ ";
        color: var(--sc-accent);
      }

      .res-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 0.5rem;
        flex-wrap: wrap;
      }

      .res-pitch {
        font-family: var(--sc-mono);
        font-size: 1rem;
        font-weight: 700;
      }

      .res-meta {
        font-size: 0.8rem;
        color: var(--sc-muted);
        font-family: var(--sc-mono);
      }

      .summary-bar {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 0.75rem;
        padding: 0.85rem 1rem;
        border-radius: var(--sc-radius);
        border: 1px solid color-mix(in srgb, var(--sc-accent) 45%, transparent);
        background: var(--sc-highlight-bg);
      }

      .summary-set {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem 0.75rem;
        font-size: 0.86rem;
        font-family: var(--sc-mono);
      }

      .summary-total {
        font-size: 0.96rem;
        font-weight: 700;
        font-family: var(--sc-mono);
        white-space: nowrap;
      }

      .loading-note {
        font-size: 0.86rem;
        color: var(--sc-muted);
        padding: 0.5rem 0;
      }
    `,
  ];

  @property({ type: String }) preset = "guitar-6";
  @property({ type: String }) lengthUnit: ScaleLengthUnit = "in";
  @property({ type: String }) tensionUnit: TensionUnit = "lbf";
  @property({ type: Number }) n = 5;
  @property({ type: Number }) L = 25.5;
  @property({ type: Array }) types: string[] = ["DA:PB", "DA:PL"];
  @property({ type: Array }) strings: StringInput[] = stateFromPreset(
    (defaultPresets as Preset[])[0],
  ).strings;
  @property({ type: Object }) fanned: FannedConfig = { ...DEFAULT_FANNED };
  @property({ type: Object }) catalog: Catalog | null = null;
  @property({ type: Object }) results: SuggestGaugeResponse | null = null;
  @property({ type: Boolean }) loading = false;

  /** Optional user-picked row index per string (overrides bestIndex in Set Summary). */
  @state() private chosenRows: Record<number, number> = {};

  private get presetsList(): Preset[] {
    return this.catalog?.presets ?? (defaultPresets as Preset[]);
  }

  private emitState(patch: Partial<GaugeSuggestState>) {
    const next: GaugeSuggestState = {
      preset: patch.preset ?? this.preset,
      lengthUnit: patch.lengthUnit ?? this.lengthUnit,
      tensionUnit: patch.tensionUnit ?? this.tensionUnit,
      n: patch.n ?? this.n,
      L: patch.L ?? this.L,
      types: patch.types ?? this.types,
      strings: patch.strings ?? this.strings,
      fanned: patch.fanned ?? this.fanned,
    };

    Object.assign(this, next);
    this.chosenRows = {};

    this.dispatchEvent(
      new CustomEvent<GaugeSuggestState>("sc-change", {
        detail: next,
        bubbles: true,
        composed: true,
      }),
    );
  }

  private onPresetChange(presetId: string) {
    if (!presetId) {
      this.emitState({ preset: "" });
      return;
    }
    const found = this.presetsList.find((p) => p.id === presetId);
    if (!found) return;
    this.emitState(stateFromPreset(found, this.n));
  }

  private onLengthUnitChange(nextUnit: ScaleLengthUnit) {
    if (nextUnit === this.lengthUnit) return;
    const prev = this.lengthUnit;
    const conv = (v: number) => convertLength(v, prev, nextUnit);
    const nextL = conv(this.L);
    const nextStrings = this.strings.map((s) => ({ ...s, L: conv(s.L) }));
    const nextFanned: FannedConfig = {
      ...this.fanned,
      L_bass: conv(this.fanned.L_bass),
      L_treble: conv(this.fanned.L_treble),
      nutWidth: conv(this.fanned.nutWidth),
      edgeBass:
        this.fanned.edgeBass != null ? conv(this.fanned.edgeBass) : null,
      edgeTreble:
        this.fanned.edgeTreble != null ? conv(this.fanned.edgeTreble) : null,
    };
    this.emitState({
      lengthUnit: nextUnit,
      L: nextL,
      strings: nextStrings,
      fanned: nextFanned,
    });
  }

  private onTensionUnitChange(nextUnit: TensionUnit) {
    if (nextUnit === this.tensionUnit) return;
    const prev = this.tensionUnit;
    const nextStrings = this.strings.map((s) => ({
      ...s,
      T: convertTension(s.T, prev, nextUnit),
    }));
    this.emitState({ tensionUnit: nextUnit, strings: nextStrings });
  }

  private onUniformLengthChange(val: number) {
    if (!Number.isFinite(val) || val <= 0) return;
    this.emitState({
      L: val,
      strings: this.strings.map((s) => ({ ...s, L: val })),
    });
  }

  private onStringField(idx: number, patch: Partial<StringInput>) {
    const next = this.strings.map((s, i) =>
      i === idx ? { ...s, ...patch } : s,
    );
    this.emitState({ strings: next });
  }

  private addString() {
    const last = this.strings[this.strings.length - 1] ?? {
      pitch: "E4",
      T: this.tensionUnit === "lbf" ? 16 : 7,
      L: this.L,
    };
    const nextPitch = transposePitch(last.pitch, 5);
    this.emitState({
      strings: [...this.strings, { pitch: nextPitch, T: last.T, L: this.L }],
    });
  }

  private removeString(idx: number) {
    if (this.strings.length <= 1) return;
    this.emitState({ strings: this.strings.filter((_, i) => i !== idx) });
  }

  private transposeAll(semitones: number) {
    this.emitState({
      strings: this.strings.map((s) => ({
        ...s,
        pitch: transposePitch(s.pitch, semitones),
      })),
    });
  }

  private equalizeTension() {
    if (this.strings.length === 0) return;
    const t0 = this.strings[0].T;
    this.emitState({
      strings: this.strings.map((s) => ({ ...s, T: t0 })),
    });
  }

  private fmtGauge(
    gaugeIn: number | null,
    gaugeMm: number | null,
    unitL: ScaleLengthUnit,
  ): string {
    if (unitL === "mm" && gaugeMm != null) return `${fmtNum(gaugeMm, 2)} mm`;
    return fmtGaugeIn(gaugeIn);
  }

  private renderSummary() {
    const res = this.results;
    if (!res || res.error || !res.strings.length) return nothing;
    const unitL = res.lengthUnit ?? this.lengthUnit;
    const unit = res.tensionUnit ?? this.tensionUnit;

    let totalT = 0;
    let validCount = 0;
    const items = res.strings.map((s, idx) => {
      const rowIdx =
        this.chosenRows[idx] !== undefined &&
        this.chosenRows[idx] < s.suggestions.length
          ? this.chosenRows[idx]
          : s.bestIndex;
      const pick = rowIdx != null ? s.suggestions[rowIdx] : undefined;
      if (pick) {
        totalT += pick.T;
        validCount++;
      }
      return { pitch: s.pitch, pick };
    });

    if (validCount === 0) return nothing;

    return html`
      <div class="summary-bar" aria-live="polite">
        <div class="summary-set">
          ${items.map(
            (it) => html`
              <span>
                <strong>${it.pitch}</strong>:
                ${
                  it.pick
                    ? `${it.pick.id} (${this.fmtGauge(it.pick.gauge_in, it.pick.gauge_mm, unitL)})`
                    : "—"
                }
              </span>
            `,
          )}
        </div>
        <div class="summary-total">Total: ${fmtNum(totalT, 2)} ${unit}</div>
      </div>
    `;
  }

  render() {
    const unitL = this.lengthUnit;
    const unitT = this.tensionUnit;
    const fannedLs = this.results?.fannedLengths ?? null;

    return html`
      <div class="layout">
        <section class="sc-card sc-section" aria-label="Instrument settings">
          <div class="controls-grid">
            <div class="sc-field">
              <label for="preset-select">Instrument preset</label>
              <select
                id="preset-select"
                .value=${this.preset}
                @change=${(e: Event) => this.onPresetChange((e.target as HTMLSelectElement).value)}
              >
                ${this.presetsList.map(
                  (p) => html`
                    <option value=${p.id} ?selected=${p.id === this.preset}>
                      ${p.name}
                    </option>
                  `,
                )}
                <option value="" ?selected=${!this.preset}>Custom</option>
              </select>
            </div>

            <div class="sc-field">
              <span class="sc-label">Length unit</span>
              <div
                class="sc-segmented"
                role="group"
                aria-label="Scale length unit"
              >
                ${(["in", "mm"] as ScaleLengthUnit[]).map(
                  (u) => html`
                    <button
                      type="button"
                      aria-pressed=${String(this.lengthUnit === u)}
                      @click=${() => this.onLengthUnitChange(u)}
                    >
                      ${u}
                    </button>
                  `,
                )}
              </div>
            </div>

            <div class="sc-field">
              <span class="sc-label">Tension unit</span>
              <div class="sc-segmented" role="group" aria-label="Tension unit">
                ${(["lbf", "kgf", "N"] as TensionUnit[]).map(
                  (u) => html`
                    <button
                      type="button"
                      aria-pressed=${String(this.tensionUnit === u)}
                      @click=${() => this.onTensionUnitChange(u)}
                    >
                      ${u}
                    </button>
                  `,
                )}
              </div>
            </div>

            <div class="sc-field">
              <label for="n-input">Suggestions</label>
              <input
                id="n-input"
                type="number"
                inputmode="numeric"
                min="1"
                max="20"
                style="width: 4.8rem"
                .value=${String(this.n)}
                @change=${(e: Event) => {
                  const v = Number.parseInt(
                    (e.target as HTMLInputElement).value,
                    10,
                  );
                  if (Number.isInteger(v) && v >= 1 && v <= 20)
                    this.emitState({ n: v });
                }}
              />
            </div>
          </div>

          <div class="sc-field">
            <span class="sc-label">String types</span>
            <sc-type-picker
              .selected=${this.types}
              .catalogTypes=${this.catalog?.stringTypes ?? []}
              @sc-types-change=${(e: CustomEvent<{ types: string[] }>) =>
                this.emitState({ types: e.detail.types })}
            ></sc-type-picker>
          </div>

          <div class="scale-bar">
            ${
              !this.fanned.enabled
                ? html`
                    <div class="sc-field">
                      <label for="uniform-L">Scale length (${unitL})</label>
                      <input
                        id="uniform-L"
                        type="number"
                        inputmode="decimal"
                        step="any"
                        style="width: 7.5rem"
                        .value=${String(this.L)}
                        @change=${(e: Event) =>
                          this.onUniformLengthChange(
                            Number((e.target as HTMLInputElement).value),
                          )}
                      />
                    </div>
                  `
                : nothing
            }

            <label class="fan-toggle">
              <input
                type="checkbox"
                .checked=${this.fanned.enabled}
                @change=${(e: Event) => {
                  const enabled = (e.target as HTMLInputElement).checked;
                  this.emitState({ fanned: { ...this.fanned, enabled } });
                }}
              />
              <span>Fanned / multiscale</span>
            </label>

            ${
              this.fanned.enabled
                ? html`
                    <div class="fan-fields">
                      ${(
                        [
                          ["fan-lb", "Bass scale", "L_bass", false],
                          ["fan-lt", "Treble scale", "L_treble", false],
                          ["fan-nw", "Nut width", "nutWidth", false],
                          ["fan-eb", "Bass edge", "edgeBass", true],
                          ["fan-et", "Treble edge", "edgeTreble", true],
                        ] as const
                      ).map(([id, label, key, optional]) => {
                        const val = this.fanned[key];
                        return html`
                          <div class="sc-field">
                            <label for=${id}>${label} (${unitL})</label>
                            <input
                              id=${id}
                              type="number"
                              inputmode="decimal"
                              step="any"
                              placeholder=${optional ? "default" : ""}
                              .value=${val != null ? String(val) : ""}
                              @change=${(e: Event) => {
                                const raw = (
                                  e.target as HTMLInputElement
                                ).value.trim();
                                this.emitState({
                                  fanned: {
                                    ...this.fanned,
                                    [key]:
                                      optional && raw === ""
                                        ? null
                                        : Number(raw),
                                  },
                                });
                              }}
                            />
                          </div>
                        `;
                      })}
                    </div>
                  `
                : nothing
            }
          </div>
        </section>

        <section class="sc-card sc-section" aria-label="String set">
          <div class="editor-header">
            <h3>Strings (${this.strings.length})</h3>
            <div class="editor-actions">
              <button
                type="button"
                class="sc-btn-sm"
                title="Transpose all strings down 1 semitone"
                @click=${() => this.transposeAll(-1)}
              >
                −1 st
              </button>
              <button
                type="button"
                class="sc-btn-sm"
                title="Transpose all strings up 1 semitone"
                @click=${() => this.transposeAll(1)}
              >
                +1 st
              </button>
              <button
                type="button"
                class="sc-btn-sm"
                title="Apply string 1 target tension to all strings"
                @click=${() => this.equalizeTension()}
              >
                Match #1 T
              </button>
              <button
                type="button"
                class="sc-btn-sm sc-btn-primary"
                @click=${() => this.addString()}
              >
                + Add string
              </button>
            </div>
          </div>

          <div class="strings-list">
            ${this.strings.map((s, idx) => {
              const displayL =
                this.fanned.enabled && fannedLs?.[idx] != null
                  ? fannedLs[idx]
                  : s.L;
              return html`
                <div class="string-row">
                  <div class="string-num">#${idx + 1}</div>
                  <div class="string-fields">
                    <div class="sc-field pitch-field">
                      <label for="pitch-${idx}">Pitch</label>
                      <div class="pitch-group">
                        <button
                          type="button"
                          class="nudge-btn"
                          aria-label="Lower string ${idx + 1} pitch"
                          @click=${() =>
                            this.onStringField(idx, {
                              pitch: transposePitch(s.pitch, -1),
                            })}
                        >
                          −
                        </button>
                        <input
                          id="pitch-${idx}"
                          type="text"
                          .value=${s.pitch}
                          @change=${(e: Event) =>
                            this.onStringField(idx, {
                              pitch: (
                                e.target as HTMLInputElement
                              ).value.trim(),
                            })}
                        />
                        <button
                          type="button"
                          class="nudge-btn"
                          aria-label="Raise string ${idx + 1} pitch"
                          @click=${() =>
                            this.onStringField(idx, {
                              pitch: transposePitch(s.pitch, 1),
                            })}
                        >
                          +
                        </button>
                      </div>
                    </div>

                    <div class="sc-field">
                      <label for="tension-${idx}">Target T (${unitT})</label>
                      <input
                        id="tension-${idx}"
                        type="number"
                        inputmode="decimal"
                        step="any"
                        .value=${String(s.T)}
                        @change=${(e: Event) =>
                          this.onStringField(idx, {
                            T: Number((e.target as HTMLInputElement).value),
                          })}
                      />
                    </div>

                    <div class="sc-field">
                      <label for="length-${idx}">Scale L (${unitL})</label>
                      <input
                        id="length-${idx}"
                        type="number"
                        inputmode="decimal"
                        step="any"
                        ?disabled=${this.fanned.enabled}
                        .value=${String(displayL)}
                        @change=${(e: Event) =>
                          this.onStringField(idx, {
                            L: Number((e.target as HTMLInputElement).value),
                          })}
                      />
                    </div>
                  </div>

                  <button
                    type="button"
                    class="sc-btn-ghost"
                    aria-label="Remove string ${idx + 1}"
                    ?disabled=${this.strings.length <= 1}
                    @click=${() => this.removeString(idx)}
                  >
                    ×
                  </button>
                </div>
              `;
            })}
          </div>
        </section>

        ${
          this.results?.error
            ? html`<div class="sc-alert sc-alert-error">
                ${this.results.error}
              </div>`
            : nothing
        }
        ${
          this.loading && !this.results
            ? html`<div class="loading-note">
                Waiting for Python engine to compute suggestions…
              </div>`
            : nothing
        }
        ${this.renderSummary()}
        ${
          this.results?.strings?.length
            ? html`
                <section class="results-grid" aria-label="Gauge suggestions">
                  ${this.results.strings.map((res, idx) => {
                    const selectedIdx =
                      this.chosenRows[idx] !== undefined &&
                      this.chosenRows[idx] < res.suggestions.length
                        ? this.chosenRows[idx]
                        : res.bestIndex;
                    const resUnitL = this.results?.lengthUnit ?? unitL;
                    const resUnitT = this.results?.tensionUnit ?? unitT;

                    return html`
                      <div class="res-card">
                        <div class="res-head">
                          <span class="res-pitch"
                            >#${idx + 1} · ${res.pitch || "?"}</span
                          >
                          <span class="res-meta">
                            ${res.L != null ? `${fmtNum(res.L, resUnitL === "mm" ? 1 : 2)} ${resUnitL}` : ""}
                            ${res.T_target != null ? ` · ${fmtNum(res.T_target, 1)} ${resUnitT}` : ""}
                          </span>
                        </div>

                        ${
                          res.error
                            ? html`<div class="sc-alert sc-alert-error">
                                ${res.error}
                              </div>`
                            : nothing
                        }
                        ${res.warnings.map(
                          (w) =>
                            html`<div class="sc-alert sc-alert-warn">
                              ${w}
                            </div>`,
                        )}
                        ${
                          res.suggestions.length
                            ? html`
                                <div
                                  class="sug-list"
                                  role="group"
                                  aria-label="Suggestions for ${res.pitch}"
                                >
                                  <div class="sug-head" aria-hidden="true">
                                    <span>ID</span>
                                    <span class="num">Gauge</span>
                                    <span class="num">T (${resUnitT})</span>
                                    <span class="num">ΔT</span>
                                  </div>
                                  ${res.suggestions.map((sug, sIdx) => {
                                    const isBest = sIdx === res.bestIndex;
                                    const isSel = sIdx === selectedIdx;
                                    const sign = sug.dT > 0 ? "+" : "";
                                    return html`
                                      <button
                                        type="button"
                                        class=${isBest ? "sug-row best" : "sug-row"}
                                        aria-pressed=${String(isSel)}
                                        title=${`Select ${sug.id} for Set Summary`}
                                        @click=${() => {
                                          this.chosenRows = {
                                            ...this.chosenRows,
                                            [idx]: sIdx,
                                          };
                                        }}
                                      >
                                        <span class="sc-mono sug-id"
                                          >${sug.id}</span
                                        >
                                        <span class="num">
                                          ${this.fmtGauge(sug.gauge_in, sug.gauge_mm, resUnitL)}
                                        </span>
                                        <span class="num"
                                          >${fmtNum(sug.T, 2)}</span
                                        >
                                        <span class="num"
                                          >${sign}${fmtNum(sug.dT, 2)}</span
                                        >
                                      </button>
                                    `;
                                  })}
                                </div>
                              `
                            : nothing
                        }
                      </div>
                    `;
                  })}
                </section>
              `
            : nothing
        }
      </div>
    `;
  }
}
