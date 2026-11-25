export function createStatusUpdater() {
  const pill = document.getElementById("status-pill") as HTMLElement;
  const text = document.getElementById("status-text") as HTMLElement;
  return (phase: string, msg: string) => {
    pill.dataset.state = phase;
    text.textContent = msg;
  };
}

export function setFooterVersion(version?: string) {
  if (!version) return;
  const el = document.getElementById("sc-version");
  if (el) el.textContent = `v${version}`;
}

export function setFooterRuntime(mode: "http" | "pyodide") {
  const el = document.getElementById("sc-runtime");
  if (el) {
    el.textContent =
      mode === "http" ? "locally with Python" : "in your browser via Pyodide";
  }
}

export function wireCalc<S, R>(
  el: HTMLElement & { loading: boolean },
  resultProp: "result" | "results",
  call: (state: S) => Promise<R>,
  makeError: (message: string, state: S) => R,
  onState?: (state: S) => void,
) {
  let seq = 0;
  const target = el as unknown as Record<string, unknown>;

  const run = async (state: S) => {
    const id = ++seq;
    el.loading = true;
    try {
      const res = await call(state);
      if (id === seq) {
        target[resultProp] = res;
        el.loading = false;
      }
    } catch (err) {
      if (id === seq) {
        const msg = err instanceof Error ? err.message : String(err);
        target[resultProp] = makeError(msg, state);
        el.loading = false;
      }
    }
  };

  el.addEventListener("sc-change", (e: Event) => {
    const state = (e as CustomEvent<S>).detail;
    onState?.(state);
    void run(state);
  });

  return {
    run,
    fail(message: string, state: S) {
      target[resultProp] = makeError(message, state);
      el.loading = false;
    },
  };
}
