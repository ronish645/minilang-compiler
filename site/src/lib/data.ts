import { useEffect, useState } from "react";
import type { Episode, Summary, Task } from "./types";

export type Loadable<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: T };

const cache = new Map<string, Promise<unknown>>();

/** Fetch a generated JSON file from public/data once and share the result. */
function loadJson<T>(name: string): Promise<T> {
  if (!cache.has(name)) {
    const url = `${import.meta.env.BASE_URL}data/${name}`;
    const request = fetch(url).then((response) => {
      if (!response.ok) throw new Error(`Could not load ${name} (HTTP ${response.status})`);
      return response.json();
    });
    request.catch(() => cache.delete(name)); // let a later visit retry
    cache.set(name, request);
  }
  return cache.get(name) as Promise<T>;
}

function useJson<T>(name: string): Loadable<T> {
  const [state, setState] = useState<Loadable<T>>({ status: "loading" });
  useEffect(() => {
    let active = true;
    loadJson<T>(name).then(
      (data) => active && setState({ status: "ready", data }),
      (error: Error) => active && setState({ status: "error", message: error.message }),
    );
    return () => {
      active = false;
    };
  }, [name]);
  return state;
}

export const useSummary = () => useJson<Summary>("summary.json");
export const useEpisodes = () => useJson<Episode[]>("episodes.json");
export const useTasks = () => useJson<Task[]>("tasks.json");
