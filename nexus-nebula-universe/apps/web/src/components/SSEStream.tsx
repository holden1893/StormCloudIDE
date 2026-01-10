"use client";

import { useRef, useState } from "react";
import { authedFetch } from "@/lib/api";

type SSEEvent =
  | { type: "status"; payload: any }
  | { type: "node"; payload: any }
  | { type: "artifact"; payload: any }
  | { type: "error"; payload: any };

function parseSSE(buffer: string): { events: SSEEvent[]; rest: string } {
  const events: SSEEvent[] = [];
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";

  for (const block of parts) {
    const lines = block.split("\n");
    let eventName = "message";
    let dataLine = "";

    for (const line of lines) {
      if (line.startsWith("event:")) eventName = line.slice(6).trim();
      if (line.startsWith("data:")) dataLine += line.slice(5).trim();
    }

    if (!dataLine) continue;
    let payload: any = dataLine;
    try {
      payload = JSON.parse(dataLine);
    } catch {}

    events.push({ type: eventName as any, payload });
  }

  return { events, rest };
}

export function SSEStream({
  accessToken,
  onNode,
  onArtifact
}: {
  accessToken: string;
  onNode: (node: string | null, notes?: string) => void;
  onArtifact: (artifactId: string, signedUrl: string) => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [kind, setKind] = useState("webapp");
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const restRef = useRef("");

  async function run() {
    setRunning(true);
    setLog([]);
    onNode(null);

    const resp = await authedFetch(
      "/generate",
      accessToken,
      {
        method: "POST",
        body: JSON.stringify({ prompt, kind })
      }
    );

    if (!resp.ok || !resp.body) {
      const t = await resp.text();
      setLog((x) => [...x, `ERROR: ${resp.status} ${t}`]);
      setRunning(false);
      return;
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const combined = restRef.current + chunk;

      const { events, rest } = parseSSE(combined);
      restRef.current = rest;

      for (const ev of events) {
        if (ev.type === "status") {
          setLog((x) => [...x, `STATUS: ${JSON.stringify(ev.payload)}`]);
        } else if (ev.type === "node") {
          const node = ev.payload?.node ?? null;
          const notes = ev.payload?.review;
          setLog((x) => [...x, `NODE: ${ev.payload?.phase} ${node}`]);
          onNode(node, notes);
        } else if (ev.type === "artifact") {
          setLog((x) => [...x, `ARTIFACT: ${JSON.stringify(ev.payload)}`]);
          onArtifact(ev.payload.artifact_id, ev.payload.signed_url);
        } else if (ev.type === "error") {
          setLog((x) => [...x, `ERROR: ${JSON.stringify(ev.payload)}`]);
        } else {
          setLog((x) => [...x, `EVENT: ${JSON.stringify(ev.payload)}`]);
        }
      }
    }

    setRunning(false);
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="font-semibold">Generate</div>

      <div className="mt-3 grid gap-2">
        <textarea
          className="w-full min-h-[120px] rounded-lg bg-zinc-950 border border-zinc-800 p-3 text-sm outline-none"
          placeholder="Describe what you want Nexus to build…"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={running}
        />

        <div className="flex items-center gap-2">
          <select
            className="rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm"
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            disabled={running}
          >
            <option value="webapp">webapp</option>
            <option value="api">api</option>
            <option value="component">component</option>
            <option value="image">image</option>
            <option value="mixed">mixed</option>
          </select>

          <button
            className="ml-auto rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-sm font-semibold disabled:opacity-50"
            onClick={run}
            disabled={running || prompt.trim().length < 5}
          >
            {running ? "Running…" : "Run Swarm"}
          </button>
        </div>

        <div className="rounded-lg bg-zinc-950 border border-zinc-800 p-3 text-xs text-zinc-300 h-44 overflow-auto">
          {log.length ? log.map((l, i) => <div key={i}>{l}</div>) : <div className="text-zinc-500">No output yet.</div>}
        </div>
      </div>
    </div>
  );
}
