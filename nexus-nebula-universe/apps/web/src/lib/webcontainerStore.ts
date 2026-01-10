"use client";

import { create } from "zustand";
import type { WebContainer, WebContainerProcess } from "@webcontainer/api";

export type PortInfo = { port: number; url: string; lastSeenAt: number };

type WCState = {
  wc: WebContainer | null;
  ports: Record<number, PortInfo>;
  activePort: number | null;
  logs: string;
  booting: boolean;
  setWC: (wc: WebContainer) => void;
  appendLog: (chunk: string) => void;
  setPort: (port: number, url: string) => void;
  setActivePort: (port: number) => void;
  reset: () => void;
};

export const useWebContainerStore = create<WCState>((set) => ({
  wc: null,
  ports: {},
  activePort: null,
  logs: "",
  booting: false,
  setWC: (wc) => set({ wc }),
  appendLog: (chunk) =>
    set((s) => ({ logs: (s.logs + chunk).slice(-120_000) })),
  setPort: (port, url) =>
    set((s) => ({
      ports: {
        ...s.ports,
        [port]: { port, url, lastSeenAt: Date.now() }
      },
      activePort: s.activePort ?? port
    })),
  setActivePort: (port) => set({ activePort: port }),
  reset: () => set({ wc: null, ports: {}, activePort: null, logs: "", booting: false })
}));

export async function wcSpawn(
  cmd: string,
  args: string[],
  onChunk?: (chunk: string) => void
): Promise<{ exitCode: number }> {
  const wc = useWebContainerStore.getState().wc;
  if (!wc) throw new Error("WebContainer not booted");

  const proc = await wc.spawn(cmd, args);
  proc.output.pipeTo(
    new WritableStream({
      write(data) {
        const s = String(data);
        useWebContainerStore.getState().appendLog(s);
        onChunk?.(s);
      }
    })
  );
  const exitCode = await proc.exit;
  return { exitCode };
}
