"use client";

import { useMemo, useState } from "react";
import { useIDEStore } from "@/lib/ideStore";
import { useWebContainerStore, wcSpawn } from "@/lib/webcontainerStore";

type Kind = "dependencies" | "devDependencies";

export function PackageManagerPanel() {
  const files = useIDEStore((s) => s.files);
  const updateFile = useIDEStore((s) => s.updateFile);
  const appendLog = useWebContainerStore((s) => s.appendLog);
  const wc = useWebContainerStore((s) => s.wc);

  const [pkgName, setPkgName] = useState("");
  const [kind, setKind] = useState<Kind>("dependencies");
  const [running, setRunning] = useState(false);

  const pkgJson = useMemo(() => {
    const raw = files["package.json"];
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }, [files]);

  const deps = useMemo(() => {
    if (!pkgJson) return [];
    const d = pkgJson[kind] || {};
    return Object.entries(d).sort(([a], [b]) => a.localeCompare(b));
  }, [pkgJson, kind]);

  async function install() {
    if (!pkgName.trim()) return;
    if (!wc) {
      alert("WebContainer not ready yet. Switch preview to WebContainer and wait for boot.");
      return;
    }

    const name = pkgName.trim();
    setRunning(true);
    try {
      // Update local package.json immediately (keeps IDE state in sync)
      const next = { ...(pkgJson || {}), [kind]: { ...(pkgJson?.[kind] || {}) } };
      next[kind][name] = "latest";
      updateFile("package.json", JSON.stringify(next, null, 2));

      appendLog(`\n[nexus] npm install ${name} (${kind})…\n`);
      const args = ["install", name];
      if (kind === "devDependencies") args.push("-D");

      const r = await wcSpawn("npm", args);
      appendLog(`\n[nexus] install exit ${r.exitCode}\n`);
      if (r.exitCode !== 0) alert("Install failed. See terminal logs.");
      setPkgName("");
    } catch (e: any) {
      appendLog("\n[nexus] package manager error: " + (e?.message || String(e)) + "\n");
      alert("Install error. See terminal logs.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="h-full grid grid-rows-[40px_56px_1fr]">
      <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-950/40 text-xs text-zinc-300 flex items-center gap-2">
        <span>Packages</span>
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setKind("dependencies")}
            className={[
              "px-2 py-1 rounded border text-xs",
              kind === "dependencies" ? "bg-zinc-800 border-zinc-700" : "bg-zinc-950/20 border-zinc-800 hover:bg-zinc-900/40",
            ].join(" ")}
          >
            deps
          </button>
          <button
            onClick={() => setKind("devDependencies")}
            className={[
              "px-2 py-1 rounded border text-xs",
              kind === "devDependencies" ? "bg-zinc-800 border-zinc-700" : "bg-zinc-950/20 border-zinc-800 hover:bg-zinc-900/40",
            ].join(" ")}
          >
            dev
          </button>
        </div>
      </div>

      <div className="border-b border-zinc-800 bg-zinc-950/30 p-2 flex gap-2">
        <input
          value={pkgName}
          onChange={(e) => setPkgName(e.target.value)}
          placeholder="package name (e.g. zod)"
          className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950/40 px-3 py-2 text-sm text-zinc-200"
        />
        <button
          disabled={running}
          onClick={install}
          className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-sm font-semibold disabled:opacity-50"
        >
          {running ? "Installing…" : "Install"}
        </button>
      </div>

      <div className="overflow-auto p-2">
        {!pkgJson ? (
          <div className="text-zinc-500 text-sm">No package.json found in this artifact.</div>
        ) : (
          <div className="space-y-1">
            {deps.map(([name, ver]) => (
              <div key={name} className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/20 px-2 py-1">
                <div className="text-sm text-zinc-200">{name}</div>
                <div className="text-xs text-zinc-500">{String(ver)}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
