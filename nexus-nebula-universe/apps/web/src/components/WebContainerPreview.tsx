"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { FileSystemTree, WebContainer as WCType } from "@webcontainer/api";
import { useWebContainerStore, wcSpawn } from "@/lib/webcontainerStore";

type Props = { files: Record<string, string> };

function toTree(files: Record<string, string>): FileSystemTree {
  const root: any = {};
  for (const [path, content] of Object.entries(files)) {
    const clean = path.replace(/^\/+/, "");
    const parts = clean.split("/").filter(Boolean);
    let node = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      if (isLast) node[part] = { file: { contents: content } };
      else {
        node[part] = node[part] || { directory: {} };
        node = node[part].directory;
      }
    }
  }
  return root as FileSystemTree;
}

function sha(s: string) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h.toString(16);
}

export function WebContainerPreview({ files }: Props) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  const wc = useWebContainerStore((s) => s.wc);
  const ports = useWebContainerStore((s) => s.ports);
  const activePort = useWebContainerStore((s) => s.activePort);
  const setWC = useWebContainerStore((s) => s.setWC);
  const setPort = useWebContainerStore((s) => s.setPort);
  const setActivePort = useWebContainerStore((s) => s.setActivePort);
  const appendLog = useWebContainerStore((s) => s.appendLog);

  const [phase, setPhase] = useState<"idle" | "booting" | "mounting" | "installing" | "starting" | "ready" | "error">(
    "idle"
  );

  const hashesRef = useRef<Record<string, string>>({});
  const syncTimer = useRef<any>(null);
  const installedRef = useRef(false);
  const startedRef = useRef(false);

  const isNextProject = useMemo(() => {
    const pkg = files["package.json"];
    if (!pkg) return false;
    try {
      const j = JSON.parse(pkg);
      return Boolean(j?.dependencies?.next || j?.devDependencies?.next);
    } catch {
      return false;
    }
  }, [files]);

  const canRun = typeof window !== "undefined" && (window as any).crossOriginIsolated;

  // Boot + mount + install + start
  useEffect(() => {
    if (!canRun) return;
    if (!isNextProject) return;

    let cancelled = false;

    async function bootOnce() {
      try {
        if (wc) return;

        setPhase("booting");
        appendLog("\n[nexus] booting webcontainer…\n");

        const mod = await import("@webcontainer/api");
        const WebContainer = mod.WebContainer;

        const w = await WebContainer.boot();
        if (cancelled) return;

        w.on("server-ready", (port: number, url: string) => {
          setPort(port, url);
          setPhase("ready");
        });

        setWC(w);
      } catch (e: any) {
        setPhase("error");
        appendLog("\n[nexus] boot error: " + (e?.message || String(e)) + "\n");
      }
    }

    bootOnce();

    return () => {
      cancelled = true;
    };
  }, [canRun, isNextProject, wc, setWC, setPort, appendLog]);

  // Mount files when wc becomes available
  useEffect(() => {
    if (!wc) return;
    if (!isNextProject) return;

    let cancelled = false;

    async function mountAndStart() {
      try {
        setPhase("mounting");
        appendLog("\n[nexus] mounting project files…\n");
        await wc.mount(toTree(files));
        if (cancelled) return;

        const h: Record<string, string> = {};
        for (const [p, c] of Object.entries(files)) h[p] = sha(c);
        hashesRef.current = h;

        if (!installedRef.current) {
          setPhase("installing");
          appendLog("\n[nexus] npm install…\n");
          installedRef.current = true;

          let r = await wcSpawn("npm", ["install"]);
          if (r.exitCode !== 0) {
            appendLog("\n[nexus] npm install failed; retrying with --legacy-peer-deps…\n");
            r = await wcSpawn("npm", ["install", "--legacy-peer-deps"]);
            if (r.exitCode !== 0) throw new Error("npm install failed");
          }
        }

        if (!startedRef.current) {
          setPhase("starting");
          appendLog("\n[nexus] starting dev server (port 3001)…\n");
          startedRef.current = true;
          // Don't await forever; server-ready event will come later.
          wcSpawn("npm", ["run", "dev", "--", "-p", "3001", "-H", "0.0.0.0"]).catch((e) =>
            appendLog("\n[nexus] dev server error: " + (e?.message || String(e)) + "\n")
          );
        }
      } catch (e: any) {
        setPhase("error");
        appendLog("\n[nexus] mount/start error: " + (e?.message || String(e)) + "\n");
      }
    }

    mountAndStart();
    return () => {
      cancelled = true;
    };
  }, [wc, isNextProject, files, appendLog]);

  // Active port -> iframe src
  useEffect(() => {
    if (!iframeRef.current) return;
    if (!activePort) return;
    const url = ports[activePort]?.url;
    if (url) iframeRef.current.src = url;
  }, [activePort, ports]);

  // Debounced sync: write changed files
  useEffect(() => {
    if (!wc) return;
    if (phase !== "ready" && phase !== "starting") return;

    if (syncTimer.current) clearTimeout(syncTimer.current);
    syncTimer.current = setTimeout(async () => {
      try {
        const prev = hashesRef.current;
        const next: Record<string, string> = { ...prev };
        const writes: Array<[string, string]> = [];

        for (const [p, c] of Object.entries(files)) {
          const h = sha(c);
          if (prev[p] !== h) {
            next[p] = h;
            writes.push([p, c]);
          }
        }

        if (writes.length === 0) return;

        for (const [p, c] of writes) {
          const clean = p.replace(/^\/+/, "");
          const dir = clean.split("/").slice(0, -1).join("/");
          if (dir) await wc.fs.mkdir(dir, { recursive: true });
          await wc.fs.writeFile(clean, c);
        }

        hashesRef.current = next;
        appendLog(`\n[nexus] synced ${writes.length} file(s)\n`);
      } catch (e: any) {
        appendLog("\n[nexus] sync error: " + (e?.message || String(e)) + "\n");
      }
    }, 450);

    return () => {
      if (syncTimer.current) clearTimeout(syncTimer.current);
    };
  }, [files, wc, phase, appendLog]);

  if (!isNextProject) {
    return (
      <div className="h-full grid place-items-center text-zinc-500 px-6 text-center">
        WebContainer preview expects a full Node project (e.g. Next.js) with a <code>package.json</code>.
      </div>
    );
  }

  if (!canRun) {
    return (
      <div className="h-full grid place-items-center px-6 text-center">
        <div>
          <div className="text-zinc-200 font-semibold">WebContainer preview needs cross-origin isolation.</div>
          <div className="text-zinc-500 mt-2 text-sm">
            Your browser reports <code>crossOriginIsolated</code> is <b>false</b>.
          </div>
          <div className="text-zinc-500 mt-2 text-sm">
            Fix: serve this app with headers COOP/COEP (see <code>apps/web/next.config.mjs</code>).
          </div>
        </div>
      </div>
    );
  }

  const portList = Object.values(ports).sort((a, b) => a.port - b.port);
  const currentUrl = activePort ? ports[activePort]?.url : "";

  return (
    <div className="h-full">
      <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-950/40 text-xs text-zinc-300 flex items-center gap-2">
        <span>WebContainer (Node)</span>
        <span className="text-zinc-500">{phase}</span>

        <div className="ml-auto flex items-center gap-2">
          <span className="text-zinc-500">Port</span>
          <select
            className="bg-zinc-950/40 border border-zinc-800 rounded px-2 py-1 text-xs"
            value={activePort ?? ""}
            onChange={(e) => setActivePort(Number(e.target.value))}
          >
            {portList.map((p) => (
              <option key={p.port} value={p.port}>
                {p.port}
              </option>
            ))}
          </select>
          <span className="text-zinc-500 truncate max-w-[240px]" title={currentUrl || ""}>
            {currentUrl || "starting…"}
          </span>
        </div>
      </div>

      <div className="h-[calc(100%-33px)]">
        <iframe ref={iframeRef} title="preview" className="w-full h-full" allow="cross-origin-isolated" src={currentUrl || "about:blank"} />
      </div>
    </div>
  );
}
