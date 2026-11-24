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

export type BackendStatusHandler = (phase: string, message: string) => void;

type MethodName =
  | "get_catalog"
  | "run_suggest_gauge"
  | "run_exact_gauge"
  | "run_frets"
  | "run_scale_length";

interface PendingCall {
  resolve: (value: unknown) => void;
  reject: (reason: Error) => void;
}

export class PyodideBackend {
  private worker: Worker;
  private nextId = 1;
  private pending = new Map<number, PendingCall>();
  private readyPromise: Promise<void>;
  private onStatus?: BackendStatusHandler;

  constructor(onStatus?: BackendStatusHandler) {
    this.onStatus = onStatus;
    this.worker = new Worker(new URL("./pyodide-worker.ts", import.meta.url), {
      type: "module",
    });

    this.worker.onmessage = (event: MessageEvent) => {
      const data = event.data as {
        type: string;
        id?: number;
        result?: unknown;
        error?: string;
        phase?: string;
        message?: string;
      };
      if (data.type === "status") {
        this.onStatus?.(data.phase ?? "loading", data.message ?? "");
        return;
      }
      if (data.type === "response" && data.id !== undefined) {
        const entry = this.pending.get(data.id);
        if (!entry) return;
        this.pending.delete(data.id);
        if (data.error) {
          entry.reject(new Error(data.error));
        } else {
          entry.resolve(data.result);
        }
      }
    };

    this.worker.onerror = (event) => {
      const err = new Error(event.message || "Pyodide worker crashed");
      this.onStatus?.("error", err.message);
      for (const [, entry] of this.pending) {
        entry.reject(err);
      }
      this.pending.clear();
    };

    const appBaseUrl = new URL("./", window.location.href).href;
    const pkgOverride = new URLSearchParams(window.location.search).get("pkg");
    this.readyPromise = this.sendRaw({
      type: "init",
      appBaseUrl,
      pkgOverride,
    }) as Promise<void>;
  }

  private sendRaw(msg: Record<string, unknown>): Promise<unknown> {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.worker.postMessage({ ...msg, id });
    });
  }

  async ready(): Promise<void> {
    await this.readyPromise;
  }

  private async call<T>(method: MethodName, payload?: unknown): Promise<T> {
    await this.readyPromise;
    return (await this.sendRaw({ type: "call", method, payload })) as T;
  }

  getCatalog(): Promise<Catalog> {
    return this.call<Catalog>("get_catalog");
  }

  suggestGauge(state: GaugeSuggestState): Promise<SuggestGaugeResponse> {
    return this.call<SuggestGaugeResponse>("run_suggest_gauge", state);
  }

  exactGauge(state: ExactGaugeState): Promise<ExactGaugeResponse> {
    return this.call<ExactGaugeResponse>("run_exact_gauge", state);
  }

  frets(state: FretsState): Promise<FretsResponse> {
    return this.call<FretsResponse>("run_frets", state);
  }

  scaleLength(state: ScaleLengthState): Promise<ScaleLengthResponse> {
    return this.call<ScaleLengthResponse>("run_scale_length", state);
  }

  terminate(): void {
    this.worker.terminate();
  }
}
