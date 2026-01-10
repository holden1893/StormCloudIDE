"use client";

import { useMemo, useState } from "react";
import { useWebContainerStore, wcSpawn } from "@/lib/webcontainerStore";

export function TerminalPanel() {
  const logs = useWebContainerStore((s) => s.logs);
  const wc = useWebContainerStore((s) => s.wc);
  const appendLog = useWebContainerStore((s) => s.appendLog);

  const [cmd, setCmd] = useState<string>("npm run test");
  const [running, setRunning] = useState(false);

  const canRun = useMemo(() => !!wc, [wc]);

  async function run(commandLine: string) {
    const parts = commandLine.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return;

    setRunning(true);
    try {
      appendLog(`\n$ ${commandLine}\n`);
      const [c, ...args] = parts;
      const r = await wcSpawn(c, args);
      appendLog(`\n[nexus] exit ${r.exitCode}\n`);
    } catch (e: any) {
      appendLog("\n[nexus] terminal error: " + (e?.message || String(e)) + "\n");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="h-full grid grid-rows-[40px_1fr_44px]">
      <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-950/40 text-xs text-zinc-300 flex items-center gap-2">
        <span>Terminal</span>
        <div className="ml-auto flex gap-2">
          <button
            disabled={!canRun || running}
            onClick={() => run("npm test")}
            className="px-2 py-1 rounded border border-zinc-800 bg-zinc-950/30 hover:bg-zinc-900/40 disabled:opacity-50"
          >
            Run Tests
          </button>
          <button
            disabled={!canRun || running}
            onClick={() => run("npm run build")}
            className="px-2 py-1 rounded border border-zinc-800 bg-zinc-950/30 hover:bg-zinc-900/40 disabled:opacity-50"
          >
            Build
          </button>
        </div>
      </div>

      <div className="bg-zinc-950/20 overflow-auto p-2 text-xs text-zinc-200 font-mono whitespace-pre-wrap">
        {logs || "[nexus] waiting…"}
      </div>

      <div className="border-t border-zinc-800 bg-zinc-950/30 p-2 flex gap-2 items-center">
        <input
          value={cmd}
          onChange={(e) => setCmd(e.target.value)}
          placeholder="command…"
          className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950/40 px-3 py-2 text-sm text-zinc-200"
        />
        <button
          disabled={!canRun || running}
          onClick={() => run(cmd)}
          className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-sm font-semibold disabled:opacity-50"
        >
          {running ? "Running…" : "Run"}
        </button>
      </div>
    </div>
  );
}
