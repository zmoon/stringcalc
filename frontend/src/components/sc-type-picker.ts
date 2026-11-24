import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { sharedStyles } from "../styles";
import type { StringTypeInfo } from "../types";

@customElement("sc-type-picker")
export class ScTypePicker extends LitElement {
  static styles = [
    sharedStyles,
    css`
      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        align-items: center;
      }

      .chip {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.2rem 0.45rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-family: var(--sc-mono);
        background: var(--sc-highlight-bg);
        border: 1px solid color-mix(in srgb, var(--sc-accent) 45%, transparent);
      }

      .chip button {
        border: 0;
        background: transparent;
        min-height: 22px;
        min-width: 22px;
        padding: 0;
        font-size: 0.9rem;
        line-height: 1;
        border-radius: 50%;
      }

      .panel {
        margin-top: 0.5rem;
        border: 1px solid var(--sc-border-strong);
        border-radius: var(--sc-radius-sm);
        padding: 0.65rem;
        background: var(--sc-bg, transparent);
      }

      .search-row {
        display: flex;
        gap: 0.45rem;
        margin-bottom: 0.55rem;
        align-items: center;
      }

      .search-row input {
        flex: 1;
      }

      .groups {
        max-height: 260px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 0.55rem;
      }

      .brand-title {
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--sc-muted);
        margin: 0 0 0.25rem;
      }

      .option-list {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.2rem;
      }

      @container (min-width: 560px) {
        .option-list {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }

      .option {
        display: flex;
        align-items: flex-start;
        gap: 0.4rem;
        padding: 0.3rem 0.4rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.82rem;
        line-height: 1.3;
      }

      .option:hover {
        background: var(--sc-surface-hover);
      }

      .option input {
        margin-top: 0.12rem;
        min-height: auto;
      }

      .opt-id {
        font-family: var(--sc-mono);
        font-weight: 600;
        white-space: nowrap;
      }

      .opt-label {
        color: var(--sc-muted);
      }
    `,
  ];

  @property({ type: Array }) selected: string[] = [];
  @property({ type: Array }) catalogTypes: StringTypeInfo[] = [];
  @state() private open = false;
  @state() private query = "";

  private toggleType(id: string) {
    const next = this.selected.includes(id)
      ? this.selected.filter((x) => x !== id)
      : [...this.selected, id];
    this.dispatchEvent(
      new CustomEvent("sc-types-change", {
        detail: { types: next },
        bubbles: true,
        composed: true,
      }),
    );
  }

  private get filteredGroups(): Array<[string, StringTypeInfo[]]> {
    const q = this.query.trim().toLowerCase();
    const byBrand = new Map<string, StringTypeInfo[]>();
    for (const item of this.catalogTypes) {
      if (
        q &&
        !item.id.toLowerCase().includes(q) &&
        !item.label.toLowerCase().includes(q) &&
        !item.brand.toLowerCase().includes(q)
      ) {
        continue;
      }
      const list = byBrand.get(item.brand) ?? [];
      list.push(item);
      byBrand.set(item.brand, list);
    }
    return [...byBrand.entries()];
  }

  render() {
    const labelMap = new Map(
      this.catalogTypes.map((t) => [t.id, `${t.brand}: ${t.label}`]),
    );

    return html`
      <div class="chips">
        ${this.selected.map(
          (id) => html`
            <span class="chip" title=${labelMap.get(id) ?? id}>
              <span>${id}</span>
              <button
                type="button"
                aria-label="Remove ${id}"
                @click=${() => this.toggleType(id)}
              >
                ×
              </button>
            </span>
          `,
        )}
        <button
          type="button"
          class="sc-btn-sm"
          aria-expanded=${String(this.open)}
          @click=${() => {
            this.open = !this.open;
          }}
        >
          ${this.open ? "Done" : "+ String types"}
        </button>
      </div>

      ${
        this.open
          ? html`
              <div class="panel">
                <div class="search-row">
                  <input
                    type="text"
                    placeholder="Filter by ID, brand, or material (e.g. PB, nylon, Stringjoy)…"
                    .value=${this.query}
                    @input=${(e: Event) => {
                      this.query = (e.target as HTMLInputElement).value;
                    }}
                  />
                  ${
                    this.query
                      ? html`
                          <button
                            type="button"
                            class="sc-btn-sm sc-btn-ghost"
                            @click=${() => {
                              this.query = "";
                            }}
                          >
                            Clear
                          </button>
                        `
                      : nothing
                  }
                </div>

                ${
                  this.catalogTypes.length === 0
                    ? html`<div class="sc-muted" style="font-size: 0.84rem">
                        Loading full string catalog from Python…
                      </div>`
                    : html`
                        <div class="groups">
                          ${
                            this.filteredGroups.length === 0
                              ? html`<div
                                  class="sc-muted"
                                  style="font-size: 0.84rem"
                                >
                                  No string types match "${this.query}".
                                </div>`
                              : this.filteredGroups.map(
                                  ([brand, items]) => html`
                                    <div>
                                      <div class="brand-title">
                                        ${brand} (${items.length})
                                      </div>
                                      <div class="option-list">
                                        ${items.map(
                                          (item) => html`
                                            <label class="option">
                                              <input
                                                type="checkbox"
                                                .checked=${this.selected.includes(item.id)}
                                                @change=${() => this.toggleType(item.id)}
                                              />
                                              <span>
                                                <span class="opt-id"
                                                  >${item.id}</span
                                                >
                                                <span class="opt-label">
                                                  — ${item.label}</span
                                                >
                                              </span>
                                            </label>
                                          `,
                                        )}
                                      </div>
                                    </div>
                                  `,
                                )
                          }
                        </div>
                      `
                }
              </div>
            `
          : nothing
      }
    `;
  }
}
