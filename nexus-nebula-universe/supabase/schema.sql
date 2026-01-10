-- =========================
-- Nexus Nebula Universe schema (MVP)
-- Tables are prefixed with nexus_ to avoid collisions.
-- =========================

-- Projects: stores swarm state + metadata
create table if not exists public.nexus_projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  title text not null default 'Untitled Project',
  prompt text not null,
  kind text not null default 'webapp',
  status text not null default 'created',
  swarm_state jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists nexus_projects_owner_id_idx on public.nexus_projects(owner_id);

-- Artifacts: zip + media pointers
create table if not exists public.nexus_artifacts (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.nexus_projects(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  kind text not null default 'zip',
  storage_path text not null,
  mime_type text not null default 'application/zip',
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists nexus_artifacts_project_id_idx on public.nexus_artifacts(project_id);
create index if not exists nexus_artifacts_owner_id_idx on public.nexus_artifacts(owner_id);

-- Marketplace listings
create table if not exists public.nexus_marketplace_listings (
  id uuid primary key default gen_random_uuid(),
  artifact_id uuid not null references public.nexus_artifacts(id) on delete cascade,
  seller_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  description text not null default '',
  price_cents int not null default 0,
  currency text not null default 'usd',
  status text not null default 'active', -- active, sold, hidden
  created_at timestamptz not null default now()
);

create index if not exists nexus_marketplace_status_idx on public.nexus_marketplace_listings(status);
create index if not exists nexus_marketplace_seller_id_idx on public.nexus_marketplace_listings(seller_id);

-- updated_at trigger for projects
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_nexus_projects_updated_at on public.nexus_projects;
create trigger trg_nexus_projects_updated_at
before update on public.nexus_projects
for each row execute function public.set_updated_at();

-- =========================
-- RLS
-- =========================
alter table public.nexus_projects enable row level security;
alter table public.nexus_artifacts enable row level security;
alter table public.nexus_marketplace_listings enable row level security;

-- Projects: owners can read/write
drop policy if exists "nexus_projects_select_own" on public.nexus_projects;
create policy "nexus_projects_select_own"
on public.nexus_projects for select
using (auth.uid() = owner_id);

drop policy if exists "nexus_projects_insert_own" on public.nexus_projects;
create policy "nexus_projects_insert_own"
on public.nexus_projects for insert
with check (auth.uid() = owner_id);

drop policy if exists "nexus_projects_update_own" on public.nexus_projects;
create policy "nexus_projects_update_own"
on public.nexus_projects for update
using (auth.uid() = owner_id)
with check (auth.uid() = owner_id);

drop policy if exists "nexus_projects_delete_own" on public.nexus_projects;
create policy "nexus_projects_delete_own"
on public.nexus_projects for delete
using (auth.uid() = owner_id);

-- Artifacts: owners can read/write
drop policy if exists "nexus_artifacts_select_own" on public.nexus_artifacts;
create policy "nexus_artifacts_select_own"
on public.nexus_artifacts for select
using (auth.uid() = owner_id);

drop policy if exists "nexus_artifacts_insert_own" on public.nexus_artifacts;
create policy "nexus_artifacts_insert_own"
on public.nexus_artifacts for insert
with check (auth.uid() = owner_id);

drop policy if exists "nexus_artifacts_delete_own" on public.nexus_artifacts;
create policy "nexus_artifacts_delete_own"
on public.nexus_artifacts for delete
using (auth.uid() = owner_id);

-- Marketplace: anyone can read active listings; sellers can manage their own
drop policy if exists "nexus_marketplace_select_active" on public.nexus_marketplace_listings;
create policy "nexus_marketplace_select_active"
on public.nexus_marketplace_listings for select
using (status = 'active' OR auth.uid() = seller_id);

drop policy if exists "nexus_marketplace_insert_seller" on public.nexus_marketplace_listings;
create policy "nexus_marketplace_insert_seller"
on public.nexus_marketplace_listings for insert
with check (auth.uid() = seller_id);

drop policy if exists "nexus_marketplace_update_seller" on public.nexus_marketplace_listings;
create policy "nexus_marketplace_update_seller"
on public.nexus_marketplace_listings for update
using (auth.uid() = seller_id)
with check (auth.uid() = seller_id);

drop policy if exists "nexus_marketplace_delete_seller" on public.nexus_marketplace_listings;
create policy "nexus_marketplace_delete_seller"
on public.nexus_marketplace_listings for delete
using (auth.uid() = seller_id);


-- ============================================================
-- Nexus Nebula Universe — Shares (Preview URL Sharing)
-- Public read by share_id (RLS policy permits select).
-- Create requires authenticated owner.
-- ============================================================

create table if not exists public.nexus_shares (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  project_id uuid not null references public.nexus_projects(id) on delete cascade,
  title text,
  files jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  expires_at timestamptz
);

alter table public.nexus_shares enable row level security;

-- Authenticated users can create shares for their own projects
create policy "shares_insert_own"
on public.nexus_shares
for insert
to authenticated
with check (auth.uid() = owner_id);

-- Owners can update/delete their own shares
create policy "shares_update_own"
on public.nexus_shares
for update
to authenticated
using (auth.uid() = owner_id);

create policy "shares_delete_own"
on public.nexus_shares
for delete
to authenticated
using (auth.uid() = owner_id);

-- Anyone can read a share if they have the id (public link)
create policy "shares_select_public"
on public.nexus_shares
for select
to anon, authenticated
using (true);
