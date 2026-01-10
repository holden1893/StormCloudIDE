"use client";

const NODES = ["Researcher", "Planner", "Coder", "Designer", "Reviewer", "Exporter"] as const;

export function SwarmVisualizer({ activeNode, notes }: { activeNode: string | null; notes?: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="flex items-center justify-between">
        <div className="font-semibold">Swarm Flow</div>
        <div className="text-xs text-zinc-400">LangGraph StateGraph</div>
      </div>

      <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
        {NODES.map((n) => {
          const active = activeNode === n;
          return (
            <div
              key={n}
              className={[
                "rounded-lg px-3 py-2 border text-sm",
                active ? "border-emerald-500 bg-emerald-500/10" : "border-zinc-800 bg-zinc-950/40"
              ].join(" ")}
            >
              <div className="font-medium">{n}</div>
              <div className="text-xs text-zinc-400">{active ? "running…" : "idle"}</div>
            </div>
          );
        })}
      </div>

      {notes ? (
        <div className="mt-3 text-sm text-zinc-300">
          <span className="text-zinc-400">Reviewer:</span> {notes}
        </div>
      ) : null}
    </div>
  );
}
