/// <reference lib="webworker" />

const PYODIDE_INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.5/full/";

interface InitMessage {
  type: "init";
  id: number;
  appBaseUrl: string;
  pkgOverride: string | null;
}

interface CallMessage {
  type: "call";
  id: number;
  method:
    | "get_catalog"
    | "run_suggest_gauge"
    | "run_exact_gauge"
    | "run_frets"
    | "run_scale_length";
  payload?: unknown;
}

type WorkerRequest = InitMessage | CallMessage;

interface PyodideInterface {
  loadPackage(names: string | string[]): Promise<void>;
  pyimport(name: string): unknown;
  runPythonAsync(code: string): Promise<unknown>;
  globals: {
    get(name: string): unknown;
    set(name: string, value: unknown): void;
  };
}

type DispatchFn = (method: string, payloadJson: string) => string;

let pyodide: PyodideInterface | null = null;
let dispatchFn: DispatchFn | null = null;
let initialized = false;
let callQueue: Promise<void> = Promise.resolve();

function postStatus(phase: string, message: string) {
  self.postMessage({ type: "status", phase, message });
}

async function resolvePackageSpec(
  appBaseUrl: string,
  pkgOverride: string | null,
): Promise<string> {
  let source = pkgOverride;
  if (!source) {
    try {
      const res = await fetch(new URL("app-config.json", appBaseUrl), {
        cache: "no-store",
      });
      if (res.ok) {
        const cfg = (await res.json()) as { stringcalcSource?: string };
        if (cfg.stringcalcSource) source = cfg.stringcalcSource;
      }
    } catch {
      // Fall through to pypi
    }
  }

  if (source === "local") {
    const manifestUrl = new URL("wheels/manifest.json", appBaseUrl);
    const res = await fetch(manifestUrl, { cache: "no-store" });
    if (!res.ok) {
      throw new Error(
        `Local wheel manifest not found at ${manifestUrl.href}. ` +
          `Run "uv run python scripts/build_web.py --wheel-only" or open with ?pkg=pypi.`,
      );
    }
    const manifest = (await res.json()) as { wheel?: string };
    if (!manifest.wheel) {
      throw new Error("wheels/manifest.json is missing 'wheel' entry.");
    }
    return new URL(`wheels/${manifest.wheel}`, appBaseUrl).href;
  }

  if (!source || source === "pypi") {
    return "stringcalc";
  }

  return source;
}

async function initPyodide(appBaseUrl: string, pkgOverride: string | null) {
  if (initialized) return;

  postStatus("loading", "Loading Python (Pyodide)…");
  const pyodideModule = (await import(
    /* @vite-ignore */ `${PYODIDE_INDEX_URL}pyodide.mjs`
  )) as {
    loadPyodide: (opts: { indexURL: string }) => Promise<PyodideInterface>;
  };
  pyodide = await pyodideModule.loadPyodide({ indexURL: PYODIDE_INDEX_URL });

  postStatus("loading", "Loading NumPy & pandas…");
  await pyodide.loadPackage(["numpy", "pandas", "micropip"]);

  const spec = await resolvePackageSpec(appBaseUrl, pkgOverride);
  postStatus(
    "loading",
    spec.endsWith(".whl")
      ? "Installing local stringcalc wheel…"
      : `Installing ${spec}…`,
  );

  const micropip = pyodide.pyimport("micropip") as {
    install(pkg: string | string[]): Promise<void>;
  };
  await micropip.install(spec);

  postStatus("loading", "Initializing stringcalc…");
  await pyodide.runPythonAsync(`
import json
from stringcalc import _app

def _sc_dispatch(method: str, payload_json: str) -> str:
    fn = getattr(_app, method)
    if method == "get_catalog":
        res = fn()
    else:
        res = fn(json.loads(payload_json))
    return json.dumps(res)
`);

  dispatchFn = pyodide.globals.get("_sc_dispatch") as DispatchFn;
  initialized = true;
  postStatus("ready", "Ready");
}

self.onmessage = (event: MessageEvent<WorkerRequest>) => {
  const msg = event.data;
  callQueue = callQueue.then(async () => {
    try {
      if (msg.type === "init") {
        await initPyodide(msg.appBaseUrl, msg.pkgOverride);
        self.postMessage({ type: "response", id: msg.id, result: true });
        return;
      }

      if (!pyodide || !dispatchFn || !initialized) {
        throw new Error("Pyodide worker is not initialized yet.");
      }

      const raw = dispatchFn(msg.method, JSON.stringify(msg.payload ?? {}));
      const result = JSON.parse(raw);
      self.postMessage({ type: "response", id: msg.id, result });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (msg.type === "init") {
        postStatus("error", message);
      }
      self.postMessage({ type: "response", id: msg.id, error: message });
    }
  });
};
