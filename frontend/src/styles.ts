import { css } from "lit";

export const sharedStyles = css`
  :host {
    display: block;
    container-type: inline-size;
    font-family: inherit;
    color: inherit;
    --sc-accent: #b87333;
    --sc-bg: transparent;
    --sc-surface: color-mix(in srgb, currentColor 4%, transparent);
    --sc-surface-hover: color-mix(in srgb, currentColor 8%, transparent);
    --sc-border: color-mix(in srgb, currentColor 18%, transparent);
    --sc-border-strong: color-mix(in srgb, currentColor 34%, transparent);
    --sc-muted: color-mix(in srgb, currentColor 62%, transparent);
    --sc-highlight-bg: color-mix(in srgb, var(--sc-accent) 16%, transparent);
    --sc-selected-bg: color-mix(in srgb, var(--sc-accent) 26%, transparent);
    --sc-warn: #b45309;
    --sc-warn-bg: color-mix(in srgb, #d97706 14%, transparent);
    --sc-error: #dc2626;
    --sc-error-bg: color-mix(in srgb, #dc2626 12%, transparent);
    --sc-radius: 8px;
    --sc-radius-sm: 6px;
    --sc-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    box-sizing: border-box;
    background: var(--sc-bg);
  }

  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  sub {
    font-size: 0.72em;
    line-height: 0;
    vertical-align: sub;
  }

  .sc-card {
    border: 1px solid var(--sc-border);
    border-radius: var(--sc-radius);
    background: var(--sc-surface);
    padding: 0.9rem;
  }

  .sc-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .sc-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    align-items: flex-end;
  }

  .sc-field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 0;
  }

  .sc-field label,
  .sc-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--sc-muted);
    letter-spacing: 0.01em;
  }

  input[type="text"],
  input[type="number"],
  select {
    font: inherit;
    font-size: 0.92rem;
    color: inherit;
    background: var(--sc-bg, transparent);
    border: 1px solid var(--sc-border-strong);
    border-radius: var(--sc-radius-sm);
    padding: 0.45rem 0.6rem;
    min-height: 44px;
    line-height: 1.2;
    max-width: 100%;
  }

  @container (min-width: 640px) {
    input[type="text"],
    input[type="number"],
    select {
      min-height: 36px;
      padding: 0.35rem 0.55rem;
    }
  }

  input:focus,
  select:focus,
  button:focus-visible {
    outline: 2px solid var(--sc-accent);
    outline-offset: 1px;
  }

  input:disabled,
  select:disabled,
  button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  input:disabled,
  select:disabled {
    background: var(--sc-surface-hover);
  }

  button {
    font: inherit;
    font-size: 0.88rem;
    color: inherit;
    background: var(--sc-surface);
    border: 1px solid var(--sc-border-strong);
    border-radius: var(--sc-radius-sm);
    padding: 0.4rem 0.75rem;
    min-height: 44px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
    transition:
      background 120ms ease,
      border-color 120ms ease;
  }

  @container (min-width: 640px) {
    button {
      min-height: 36px;
      padding: 0.32rem 0.65rem;
    }
  }

  button:hover:not(:disabled) {
    background: var(--sc-surface-hover);
    border-color: var(--sc-accent);
  }

  button.sc-btn-primary {
    background: var(--sc-accent);
    border-color: var(--sc-accent);
    color: #fff;
    font-weight: 600;
  }

  button.sc-btn-primary:hover:not(:disabled) {
    filter: brightness(1.08);
  }

  button.sc-btn-ghost {
    background: transparent;
    border-color: transparent;
    color: var(--sc-muted);
    padding: 0.25rem 0.45rem;
  }

  button.sc-btn-ghost:hover:not(:disabled) {
    color: inherit;
    background: var(--sc-surface-hover);
  }

  button.sc-btn-sm {
    font-size: 0.8rem;
    min-height: 36px;
    padding: 0.22rem 0.5rem;
  }

  @container (min-width: 640px) {
    button.sc-btn-sm {
      min-height: 30px;
    }
  }

  .sc-segmented {
    display: inline-flex;
    width: fit-content;
    border: 1px solid var(--sc-border-strong);
    border-radius: var(--sc-radius-sm);
    overflow: hidden;
  }

  .sc-segmented button {
    border: 0;
    border-radius: 0;
    background: transparent;
    padding-inline: 0.65rem;
  }

  .sc-segmented button + button {
    border-left: 1px solid var(--sc-border);
  }

  .sc-segmented button[aria-pressed="true"] {
    background: var(--sc-accent);
    color: #fff;
    font-weight: 600;
  }

  .sc-alert {
    padding: 0.55rem 0.75rem;
    border-radius: var(--sc-radius-sm);
    font-size: 0.85rem;
    line-height: 1.4;
  }

  .sc-alert-warn {
    background: var(--sc-warn-bg);
    border: 1px solid color-mix(in srgb, var(--sc-warn) 45%, transparent);
    color: var(--sc-warn);
  }

  .sc-alert-error {
    background: var(--sc-error-bg);
    border: 1px solid color-mix(in srgb, var(--sc-error) 45%, transparent);
    color: var(--sc-error);
  }

  .sc-mono {
    font-family: var(--sc-mono);
    font-variant-numeric: tabular-nums;
  }

  .sc-muted {
    color: var(--sc-muted);
  }

  .sc-result-box {
    padding: 0.85rem 1rem;
    border-radius: var(--sc-radius);
    border: 1px solid color-mix(in srgb, var(--sc-accent) 45%, transparent);
    background: var(--sc-highlight-bg);
    font-size: 1.05rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }
`;
