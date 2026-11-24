import type {
  Catalog,
  ExactGaugeResponse,
  ExactGaugeState,
  FretsResponse,
  FretsState,
  GaugeSuggestState,
  ScaleLengthResponse,
  ScaleLengthState,
  SuggestGaugeResponse,
} from "../types";
import { PyodideBackend } from "./pyodide-backend";

export type BackendStatusHandler = (phase: string, message: string) => void;
export type BackendMode = "http" | "pyodide";

export type MethodName =
  | "get_catalog"
  | "run_suggest_gauge"
  | "run_exact_gauge"
  | "run_frets"
  | "run_scale_length";

type RawCaller = <T>(method: MethodName, payload?: unknown) => Promise<T>;

export interface AppBackend {
  getCatalog(): Promise<Catalog>;
  suggestGauge(state: GaugeSuggestState): Promise<SuggestGaugeResponse>;
  exactGauge(state: ExactGaugeState): Promise<ExactGaugeResponse>;
  frets(state: FretsState): Promise<FretsResponse>;
  scaleLength(state: ScaleLengthState): Promise<ScaleLengthResponse>;
}

function createHttpCaller(onStatus?: BackendStatusHandler): RawCaller {
  let ready = false;
  onStatus?.("loading", "Connecting…");

  return async <T>(method: MethodName, payload?: unknown): Promise<T> => {
    let resp: Response;
    try {
      resp = await fetch(`./api/${method}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload ?? {}),
      });
    } catch (err) {
      ready = false;
      onStatus?.("error", "Server unreachable");
      throw err;
    }
    if (!resp.ok) {
      ready = false;
      let detail = `HTTP ${resp.status}`;
      try {
        const body = (await resp.json()) as { error?: string };
        if (body.error) detail = body.error;
      } catch {
        // Ignore non-JSON error responses.
      }
      onStatus?.("error", "Request failed");
      throw new Error(detail);
    }
    if (!ready) {
      ready = true;
      onStatus?.("ready", "Ready (Python)");
    }
    return (await resp.json()) as T;
  };
}

export function createBackend(
  onStatus?: BackendStatusHandler,
  onMode?: (mode: BackendMode) => void,
): AppBackend {
  const callPromise: Promise<RawCaller> = (async () => {
    let cfg: { backend?: string; stringcalcSource?: string } = {};
    try {
      const resp = await fetch("./app-config.json", { cache: "no-store" });
      if (resp.ok) cfg = (await resp.json()) as typeof cfg;
    } catch {
      // Fall back to Pyodide when app-config.json is absent or unreadable.
    }

    if (cfg.backend === "http") {
      onMode?.("http");
      return createHttpCaller(onStatus);
    }

    onMode?.("pyodide");
    const py = new PyodideBackend(onStatus, cfg.stringcalcSource ?? null);
    return <T>(method: MethodName, payload?: unknown) =>
      py.call<T>(method, payload);
  })();

  const call: RawCaller = (method, payload) =>
    callPromise.then((fn) => fn(method, payload));

  return {
    getCatalog: () => call<Catalog>("get_catalog"),
    suggestGauge: (s) => call<SuggestGaugeResponse>("run_suggest_gauge", s),
    exactGauge: (s) => call<ExactGaugeResponse>("run_exact_gauge", s),
    frets: (s) => call<FretsResponse>("run_frets", s),
    scaleLength: (s) => call<ScaleLengthResponse>("run_scale_length", s),
  };
}
