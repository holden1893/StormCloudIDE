"use client";

import { useMemo, useState } from "react";
import { useIDEStore } from "@/lib/ideStore";
import { WebContainerPreview } from "@/components/WebContainerPreview";
import { SandpackProvider, SandpackLayout, SandpackPreview } from "@codesandbox/sandpack-react";

function pickAppFile(files: Record<string, string>) {
  const candidates = ["src/app/page.tsx", "app/page.tsx", "src/App.tsx", "App.tsx"];
  for (const c of candidates) if (files[c]) return c;
  return Object.keys(files).find((p) => p.endsWith(".tsx") || p.endsWith(".jsx")) || null;
}

function SandboxPreview({ files }: { files: Record<string, string> }) {
  const sandpackFiles = useMemo(() => {
    const appPath = pickAppFile(files);
    const appSrc =
      appPath ? files[appPath] : `export default function App(){return <div className="p-6">No previewable UI file found.</div>}`;
    const globals = files["src/app/globals.css"] || files["globals.css"] || "";

    const indexHtml = `<!doctype html><html><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
<script src="https://cdn.tailwindcss.com"></script><style>${globals}</style></head>
<body class="bg-zinc-950 text-zinc-100"><div id="root"></div></body></html>`;

    const indexTsx = `import React from "react"; import { createRoot } from "react-dom/client"; import App from "./App";
createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);`;

    const appTsx = appSrc
      .replace(/from\\s+["']next\\/(.*?)["'];?/g, 'from "react";')
      .replace(/next\\/link/g, "react")
      .replace(/next\\/image/g, "react");

    const extras: Record<string, any> = {};
    for (const [p, c] of Object.entries(files)) {
      if (c.length > 200_000) continue;
      extras[`/${p}`] = { code: c };
    }

    return {
      "/index.html": { code: indexHtml },
      "/index.tsx": { code: indexTsx },
      "/App.tsx": { code: appTsx },
      ...extras,
    };
  }, [files]);

  return (
    <SandpackProvider template="react-ts" files={sandpackFiles}>
      <SandpackLayout style={{ height: "100%" }}>
        <SandpackPreview style={{ height: "100%" }} />
      </SandpackLayout>
    </SandpackProvider>
  );
}

export function PreviewPanel() {
  const files = useIDEStore((s) => s.files);

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

  const [mode, setMode] = useState<"webcontainer" | "sandbox">(isNextProject ? "webcontainer" : "sandbox");

  return (
    <div className="h-full">
      <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-950/40 text-xs text-zinc-300 flex items-center gap-2">
        <span>Live Preview</span>

        <div className="ml-auto flex gap-1">
          <button
            onClick={() => setMode("webcontainer")}
            className={[
              "px-2 py-1 rounded border text-xs",
              mode === "webcontainer" ? "bg-zinc-800 border-zinc-700" : "bg-zinc-950/20 border-zinc-800 hover:bg-zinc-900/40",
            ].join(" ")}
            title="Run the full Node project in-browser (Next.js)"
          >
            WebContainer
          </button>
          <button
            onClick={() => setMode("sandbox")}
            className={[
              "px-2 py-1 rounded border text-xs",
              mode === "sandbox" ? "bg-zinc-800 border-zinc-700" : "bg-zinc-950/20 border-zinc-800 hover:bg-zinc-900/40",
            ].join(" ")}
            title="Fast React sandbox preview (best-effort)"
          >
            Sandbox
          </button>
        </div>
      </div>

      <div className="h-[calc(100%-33px)]">
        {mode === "webcontainer" ? <WebContainerPreview files={files} /> : <SandboxPreview files={files} />}
      </div>
    </div>
  );
}
