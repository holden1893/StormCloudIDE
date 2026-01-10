"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { authedFetch } from "@/lib/api";
import { AuthGate } from "@/components/AuthGate";
import { useIDEStore } from "@/lib/ideStore";
import { FileTree } from "@/components/FileTree";
import { EditorPane } from "@/components/EditorPane";
import { PreviewPanel } from "@/components/PreviewPanel";
import { TerminalPanel } from "@/components/TerminalPanel";
import { PackageManagerPanel } from "@/components/PackageManagerPanel";
import Link from "next/link";

export default function StudioPage({ params }: { params: { id: string } }) {
  const setFiles = useIDEStore((s) => s.setFiles);
  const files = useIDEStore((s) => s.files);

  const [token, setToken] = useState("");
  const [title, setTitle] = useState("Studio");
  const [status, setStatus] = useState("loading");
  const [saving, setSaving] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [shareUrl, setShareUrl] = useState<string>("");
  const [leftTab, setLeftTab] = useState<"files" | "packages">("files");
  const [dockOpen, setDockOpen] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(async ({ data }) => {
      const t = data.session?.access_token || "";
      setToken(t);
      if (!t) return;

      const resp = await authedFetch(`/projects/${params.id}/files`, t);
      const json = await resp.json();

      setTitle(json.project?.title || "Studio");
      setFiles(json.files || {});
      setStatus("ready");
    });
  }, [params.id, setFiles]);

  async function save() {
    if (!token) return;
    setSaving(true);
    try {
      const resp = await authedFetch(`/projects/${params.id}/files`, token, { method: "PUT", body: JSON.stringify({ files }) });
      if (!resp.ok) alert(`Save failed: ${resp.status} ${await resp.text()}`);
    } finally {
      setSaving(false);
    }
  }
  async function share() {
    if (!token) return;
    setSharing(true);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE_URL!;
      const resp = await fetch(`${base}/shares`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ project_id: params.id, title })
      });

      if (!resp.ok) {
        alert(`Share failed: ${resp.status} ${await resp.text()}`);
        return;
      }

      const json = await resp.json();
      const id = json.share?.id;
      const url = `${window.location.origin}/share/${id}`;
      setShareUrl(url);
      await navigator.clipboard.writeText(url);
      alert("Share link copied to clipboard.");
    } finally {
      setSharing(false);
    }
  }


  return (
    <AuthGate>
      <div className="h-[calc(100vh-48px)] grid grid-rows-[44px_1fr_auto] gap-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 px-3 flex items-center gap-3">
          <div className="font-bold">🌌 Nexus</div>
          <div className="text-sm text-zinc-300 truncate">{title}</div>
          <div className="ml-auto flex items-center gap-2">
            <button onClick={save} disabled={saving} className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-sm font-semibold disabled:opacity-50">
              {saving ? "Saving…" : "Save"}
            </button>
            <button onClick={share} disabled={sharing} className="rounded-lg border border-zinc-800 bg-zinc-950/40 hover:bg-zinc-900/40 px-3 py-2 text-sm font-semibold disabled:opacity-50">
              {sharing ? "Sharing…" : "Share Preview"}
            </button>
            <Link className="rounded-lg border border-zinc-800 bg-zinc-950/40 px-3 py-2 text-sm" href="/dashboard">
              Dashboard
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-[56px_260px_1fr_1fr] gap-2 h-full">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-2 flex flex-col gap-2 items-center">
            <div className="w-10 h-10 rounded-lg bg-zinc-950/50 grid place-items-center border border-zinc-800" title="Workspace">🧠</div>
            <div className="w-10 h-10 rounded-lg bg-zinc-950/50 grid place-items-center border border-zinc-800" title="Files">📁</div>
            <div className="w-10 h-10 rounded-lg bg-zinc-950/50 grid place-items-center border border-zinc-800" title="Preview">👁️</div>
            <div className="mt-auto w-10 h-10 rounded-lg bg-zinc-950/50 grid place-items-center border border-zinc-800" title="Settings">⚙️</div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-hidden grid grid-rows-[36px_1fr]">
            <div className="border-b border-zinc-800 bg-zinc-950/30 px-2 py-1 flex gap-1">
              <button onClick={() => setLeftTab("files")} className={["px-2 py-1 rounded border text-xs", leftTab==="files" ? "bg-zinc-800 border-zinc-700" : "bg-zinc-950/20 border-zinc-800 hover:bg-zinc-900/40"].join(" ")}>Files</button>
              <button onClick={() => setLeftTab("packages")} className={["px-2 py-1 rounded border text-xs", leftTab==="packages" ? "bg-zinc-800 border-zinc-700" : "bg-zinc-950/20 border-zinc-800 hover:bg-zinc-900/40"].join(" ")}>Packages</button>
            </div>
            <div className="min-h-0">
              {leftTab === "files" ? <FileTree /> : <PackageManagerPanel />}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-hidden">
            {status !== "ready" ? <div className="h-full grid place-items-center text-zinc-500">{status}…</div> : <EditorPane />}
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-hidden">
            {status !== "ready" ? <div className="h-full grid place-items-center text-zinc-500">{status}…</div> : <PreviewPanel />}
          </div>
        </div>

      {/* Bottom dock (Terminal) */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-hidden">
        <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-950/40 text-xs text-zinc-300 flex items-center">
          <span>Dock</span>
          <button
            onClick={() => setDockOpen(!dockOpen)}
            className="ml-auto px-2 py-1 rounded border border-zinc-800 bg-zinc-950/30 hover:bg-zinc-900/40"
          >
            {dockOpen ? "Hide" : "Show"}
          </button>
        </div>
        {dockOpen ? (
          <div className="h-[320px]">
            <TerminalPanel />
          </div>
        ) : null}
      </div>
      </div>
    </AuthGate>
  );
}
