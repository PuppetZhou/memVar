"use client";

import { useEffect, useState } from "react";
import { getJson } from "./api-client";

export type JsonResourceState<T> =
  | { kind: "loading" }
  | { kind: "error"; error: string }
  | { kind: "ready"; response: T };

export function useJsonResource<T>(path: string, unavailableMessage: string): JsonResourceState<T> {
  const [state, setState] = useState<JsonResourceState<T>>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    getJson<T>(path, controller.signal)
      .then((response) => setState({ kind: "ready", response }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({
          kind: "error",
          error: error instanceof Error ? error.message : unavailableMessage,
        });
      });
    return () => controller.abort();
  }, [path, unavailableMessage]);

  return state;
}
