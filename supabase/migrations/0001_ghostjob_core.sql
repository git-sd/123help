-- GhostJob core schema. Apply with: supabase db push
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  role text not null default 'user' check (role in ('user','admin')),
  status text not null default 'active' check (status in ('active','suspended')),
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.investigations (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references public.profiles(id) on delete cascade,
  input_type text not null check (input_type in ('url','text')), job_url text, job_url_hash text,
  job_text text check (char_length(job_text) <= 10000), recruiter_name text, recruiter_email text, recruiter_phone text,
  company_name text, job_title text, status text not null default 'queued' check (status in ('queued','running','partial','completed','failed','cancelled')),
  current_step text, risk_level text check (risk_level in ('low','medium','high')), risk_score integer check (risk_score between 0 and 100),
  fee_detected boolean not null default false, error_code text, attempts integer not null default 0,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), check (job_url is not null or job_text is not null)
);
create table if not exists public.sources (
  id uuid primary key default gen_random_uuid(), investigation_id uuid not null references public.investigations(id) on delete cascade,
  url text, domain text, title text, source_type text not null, excerpt text check (char_length(excerpt) <= 2000), fetched_at timestamptz not null default now()
);
create table if not exists public.findings (
  id uuid primary key default gen_random_uuid(), investigation_id uuid not null references public.investigations(id) on delete cascade,
  category text not null, fee_type text, title text not null, detail text, quote text,
  status text not null check (status in ('verified','warning','unverified','unknown')), severity integer not null default 0 check (severity between 0 and 3), created_at timestamptz not null default now()
);
create table if not exists public.reports (
  investigation_id uuid primary key references public.investigations(id) on delete cascade, summary text not null,
  risk_factors jsonb not null default '[]'::jsonb, next_steps jsonb not null default '[]'::jsonb, disclaimer_version text not null default 'v1', created_at timestamptz not null default now()
);
create table if not exists public.password_reset_otps (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
  otp_hash text not null, expires_at timestamptz not null, consumed_at timestamptz, created_at timestamptz not null default now()
);
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, display_name) values (new.id, new.raw_user_meta_data ->> 'display_name');
  return new;
end;
$$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users for each row execute procedure public.handle_new_user();
create index if not exists investigations_owner_created_idx on public.investigations(user_id, created_at desc);
create index if not exists investigations_queued_idx on public.investigations(created_at) where status = 'queued';
create index if not exists sources_investigation_idx on public.sources(investigation_id);
create index if not exists findings_investigation_idx on public.findings(investigation_id);

alter table public.profiles enable row level security;
alter table public.investigations enable row level security;
alter table public.sources enable row level security;
alter table public.findings enable row level security;
alter table public.reports enable row level security;
alter table public.password_reset_otps enable row level security;
drop policy if exists "profiles_select_own" on public.profiles;
drop policy if exists "investigations_select_own" on public.investigations;
drop policy if exists "investigations_delete_own" on public.investigations;
drop policy if exists "sources_select_own" on public.sources;
drop policy if exists "findings_select_own" on public.findings;
drop policy if exists "reports_select_own" on public.reports;
create policy "profiles_select_own" on public.profiles for select using (auth.uid() = id);
create policy "investigations_select_own" on public.investigations for select using (auth.uid() = user_id);
create policy "investigations_delete_own" on public.investigations for delete using (auth.uid() = user_id);
create policy "sources_select_own" on public.sources for select using (exists (select 1 from public.investigations i where i.id=sources.investigation_id and i.user_id=auth.uid()));
create policy "findings_select_own" on public.findings for select using (exists (select 1 from public.investigations i where i.id=findings.investigation_id and i.user_id=auth.uid()));
create policy "reports_select_own" on public.reports for select using (exists (select 1 from public.investigations i where i.id=reports.investigation_id and i.user_id=auth.uid()));
-- OTP rows have no client policy. Only the backend service role can create, verify, or consume them.
