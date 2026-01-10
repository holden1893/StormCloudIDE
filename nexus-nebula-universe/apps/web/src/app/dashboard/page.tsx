"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { authedFetch } from "@/lib/api";
import { AuthGate } from "@/components/AuthGate";
import { SSEStream } from "@/components/SSEStream";
import { SwarmVisualizer } from "@/components/SwarmVisualizer";
import type { Project } from "@/lib/types";
import Link from "next/link";

export default function DashboardPage() {
  const [accessToken, setAccessToken] = useState<string>("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [reviewNotes, setReviewNotes] = useState<string | undefined>(undefined);
  const [artifactUrl, setArtifactUrl] = useState<string | null>(null);

  async function loadProjects(token: string) {
    const resp = await authedFetch("/projects", token);
    const json = await resp.json();
    setProjects(json.projects || []);
  }

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      const t = data.session?.access_token || "";
      setAccessToken(t);
      if (t) loadProjects(t);
    });
  }, []);

  return (
    <AuthGate>
      <main className="grid gap-6">
        <div className="flex items-center gap-3">
          <div>
            <div className="text-3xl font-bold">Dashboard</div>
            <div className="text-sm text-zinc-400">Run the swarm, get artifacts, list them in the marketplace.</div>
          </div>

          <button
            className="ml-auto rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2 text-sm"
            onClick={async () => {
              await supabase.auth.signOut();
              window.location.href = "/";
            }}
          >
            Sign out
          </button>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <div className="grid gap-4">
            <SwarmVisualizer activeNode={activeNode} notes={reviewNotes} />
            {artifactUrl ? (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
                <div className="font-semibold">Latest Artifact</div>
                <a className="mt-2 inline-block text-emerald-400 underline" href={artifactUrl} target="_blank" rel="noreferrer">
                  Download signed ZIP
                </a>
                <div className="mt-2 text-xs text-zinc-400">Signed links expire. Add a refresh endpoint later.</div>
              </div>
            ) : null}
          </div>

          <SSEStream
            accessToken={accessToken}
            onNode={(node, notes) => {
              setActiveNode(node);
              if (notes) setReviewNotes(notes);
            }}
            onArtifact={(_artifactId, signedUrl) => {
              setArtifactUrl(signedUrl || null);
              loadProjects(accessToken);
            }}
          />
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="flex items-center justify-between">
            <div className="font-semibold">Projects</div>
            <Link className="text-sm text-emerald-400 underline" href="/marketplace">
              Go to marketplace
            </Link>
          </div>

          <div className="mt-3 grid gap-2">
            {projects.length ? (
              projects.map((p) => (
                <Link
                  key={p.id}
                  href={`/studio/${p.id}`}
                  className="rounded-lg border border-zinc-800 bg-zinc-950/40 px-3 py-2 hover:bg-zinc-950"
                >
                  <div className="flex items-center justify-between">
                    <div className="font-medium">{p.title}</div>
                    <div className="text-xs text-zinc-400">{p.status}</div>
                  </div>
                  <div className="text-xs text-zinc-400">
                    {p.kind} • {new Date(p.created_at).toLocaleString()}
                  </div>
                </Link>
              ))
            ) : (
              <div className="text-sm text-zinc-500">No projects yet. Run the swarm above.</div>
            )}
          </div>
        </div>
      </main>
    </AuthGate>
  );
}
