"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { authedFetch } from "@/lib/api";
import { AuthGate } from "@/components/AuthGate";
import type { Project } from "@/lib/types";

export default function ProjectPage({ params }: { params: { id: string } }) {
  const [project, setProject] = useState<Project | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(async ({ data }) => {
      const token = data.session?.access_token;
      if (!token) return;

      const resp = await authedFetch(`/projects/${params.id}`, token);
      const json = await resp.json();
      setProject(json.project || null);
    });
  }, [params.id]);

  return (
    <AuthGate>
      <main className="grid gap-4">
        <div className="text-3xl font-bold">Project</div>

        {project ? (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
            <div className="flex items-center justify-between">
              <div className="text-xl font-semibold">{project.title}</div>
              <div className="text-sm text-zinc-400">{project.status}</div>
            </div>

            <div className="mt-3 text-sm text-zinc-300 whitespace-pre-wrap">
              <span className="text-zinc-400">Prompt:</span> {project.prompt}
            </div>

            <div className="mt-4">
              <div className="text-sm font-semibold">Swarm State</div>
              <pre className="mt-2 rounded-lg bg-zinc-950 border border-zinc-800 p-3 text-xs overflow-auto">
                {JSON.stringify(project.swarm_state || {}, null, 2)}
              </pre>
            </div>
          </div>
        ) : (
          <div className="text-zinc-500">Loading…</div>
        )}
      </main>
    </AuthGate>
  );
}
