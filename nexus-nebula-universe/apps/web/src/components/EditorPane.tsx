"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import { useIDEStore } from "@/lib/ideStore";

const Monaco = dynamic(() => import("@monaco-editor/react"), { ssr: false });

function languageFromPath(path: string): string {
  const p = path.toLowerCase();
  if (p.endsWith(".ts") || p.endsWith(".tsx")) return "typescript";
  if (p.endsWith(".js") || p.endsWith(".jsx")) return "javascript";
  if (p.endsWith(".json")) return "json";
  if (p.endsWith(".css")) return "css";
  if (p.endsWith(".html")) return "html";
  if (p.endsWith(".md")) return "markdown";
  if (p.endsWith(".py")) return "python";
  return "plaintext";
}

export function EditorPane() {
  const activePath = useIDEStore((s) => s.activePath);
  const files = useIDEStore((s) => s.files);
  const updateFile = useIDEStore((s) => s.updateFile);

  const value = activePath ? files[activePath] ?? "" : "";
  const lang = useMemo(() => (activePath ? languageFromPath(activePath) : "plaintext"), [activePath]);

  if (!activePath) return <div className="h-full grid place-items-center text-zinc-500">No file selected.</div>;

  return (
    <div className="h-full">
      <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-950/40 text-xs text-zinc-300">{activePath}</div>
      <div className="h-[calc(100%-33px)]">
        <Monaco
          height="100%"
          language={lang}
          theme="vs-dark"
          value={value}
          onChange={(v) => updateFile(activePath, v ?? "")}
          options={{ minimap: { enabled: false }, fontSize: 13, wordWrap: "on", scrollBeyondLastLine: false }}
        />
      </div>
    </div>
  );
}
