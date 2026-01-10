import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-[70vh] grid place-items-center">
      <div className="max-w-xl text-center">
        <div className="text-4xl font-bold">🌌 Nexus Nebula Universe</div>
        <p className="mt-3 text-zinc-400">
          A multi-agent swarm that generates artifacts you can sell. Build fast. Ship faster.
        </p>
        <div className="mt-6 flex gap-3 justify-center">
          <Link className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 font-semibold" href="/dashboard">
            Dashboard
          </Link>
          <Link className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-2" href="/marketplace">
            Marketplace
          </Link>
        </div>
      </div>
    </main>
  );
}
