"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import type { Listing } from "@/lib/types";

export default function MarketplacePage() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [status, setStatus] = useState<string>("loading");

  async function load() {
    setStatus("loading");
    const { data, error } = await supabase
      .from("nexus_marketplace_listings")
      .select("*")
      .eq("status", "active")
      .order("created_at", { ascending: false });

    if (error) {
      setStatus(error.message);
      return;
    }
    setListings((data as any) || []);
    setStatus("ready");
  }

  useEffect(() => {
    load();

    const channel = supabase
      .channel("nexus_marketplace_listings")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "nexus_marketplace_listings" },
        () => load()
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return (
    <main className="grid gap-6">
      <div>
        <div className="text-3xl font-bold">Marketplace</div>
        <div className="text-sm text-zinc-400">Realtime listings via Supabase.</div>
      </div>

      <div className="grid gap-3">
        {status !== "ready" ? (
          <div className="text-zinc-500">{status}…</div>
        ) : listings.length ? (
          listings.map((l) => (
            <div key={l.id} className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
              <div className="flex items-center justify-between">
                <div className="font-semibold">{l.title}</div>
                <div className="text-sm text-emerald-400">
                  ${(l.price_cents / 100).toFixed(2)} {l.currency.toUpperCase()}
                </div>
              </div>
              <div className="mt-2 text-sm text-zinc-300">{l.description}</div>
              <div className="mt-3 text-xs text-zinc-500">
                artifact_id: {l.artifact_id} • seller: {l.seller_id}
              </div>
              <div className="mt-3 text-xs text-zinc-500">
                Payments: Stripe/PayPal/Cash App hooks are scaffolded server-side (Stripe stub).
              </div>
            </div>
          ))
        ) : (
          <div className="text-zinc-500">No listings yet.</div>
        )}
      </div>
    </main>
  );
}
