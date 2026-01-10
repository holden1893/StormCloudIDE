"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useIDEStore } from "@/lib/ideStore";
import { PreviewPanel } from "@/components/PreviewPanel";
import Link from "next/link";

export default function SharePage() {
  const params = useParams<{ id: string }>();
  const shareId = params.id;

  const setFiles = useIDEStore((s) => s.setFiles);
  const [title, setTitle] = useState("Shared Preview");
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    async function load() {
      try {
        const base = process.env.NEXT_PUBLIC_API_BASE_URL!;
        const resp = await fetch(`${base}/shares/${shareId}`);
        if (!resp.ok) throw new Error(await resp.text());
        const json = await resp.json();
        setTitle(json.share?.title || "Shared Preview");
        setFiles(json.files || {});
        setStatus("ready");
      } catch (e) {
        console.error(e);
        setStatus("error");
      }
    }
    load();
  }, [shareId, setFiles]);

  return (
    <div className="h-[calc(100vh-48px)] grid grid-rows-[44px_1fr] gap-2">
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 px-3 flex items-center gap-3">
        <div className="font-bold">🌌 Nexus</div>
        <div className="text-sm text-zinc-300 truncate">{title}</div>
        <div className="ml-auto flex items-center gap-2">
          <Link className="rounded-lg border border-zinc-800 bg-zinc-950/40 px-3 py-2 text-sm" href="/">
            Home
          </Link>
        </div>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-hidden">
        {status !== "ready" ? (
          <div className="h-full grid place-items-center text-zinc-500">{status}…</div>
        ) : (
          <PreviewPanel />
        )}
      </div>
    </div>
  );
}
