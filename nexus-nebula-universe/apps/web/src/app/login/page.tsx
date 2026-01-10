"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function sendLink() {
    setErr(null);
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/dashboard` }
    });
    if (error) setErr(error.message);
    else setSent(true);
  }

  return (
    <main className="min-h-[70vh] grid place-items-center">
      <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-900/40 p-6">
        <div className="text-2xl font-bold">Login</div>
        <p className="mt-2 text-zinc-400 text-sm">Email magic link. No password drama.</p>

        <div className="mt-4 grid gap-2">
          <input
            className="rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm outline-none"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button
            className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-sm font-semibold disabled:opacity-50"
            onClick={sendLink}
            disabled={!email.includes("@")}
          >
            Send magic link
          </button>
          {sent ? <div className="text-sm text-emerald-400">Sent. Check your email.</div> : null}
          {err ? <div className="text-sm text-red-400">{err}</div> : null}
        </div>
      </div>
    </main>
  );
}
