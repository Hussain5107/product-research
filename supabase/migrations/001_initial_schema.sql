create extension if not exists "pgcrypto";

create table if not exists public.products (
  id uuid primary key default gen_random_uuid(),
  marketplace text not null,
  asin text not null,
  name text not null,
  category text,
  product_url text,
  latest_price numeric,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (marketplace, asin)
);

create table if not exists public.product_price_history (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  price numeric not null,
  source text not null,
  verification_status text not null,
  collected_at timestamptz not null default now()
);

create table if not exists public.research_runs (
  id uuid primary key default gen_random_uuid(),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  status text not null,
  products_researched integer not null default 0,
  successful_analyses integer not null default 0,
  errors jsonb not null default '[]'::jsonb,
  api_usage jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.research_results (
  id uuid primary key default gen_random_uuid(),
  research_run_id uuid not null references public.research_runs(id) on delete cascade,
  product_id uuid not null references public.products(id) on delete cascade,
  opportunity_score numeric not null check (opportunity_score >= 0 and opportunity_score <= 10),
  data_confidence text not null check (data_confidence in ('low', 'medium', 'high')),
  status text not null,
  analysis jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.suppliers (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references public.products(id) on delete cascade,
  supplier_name text not null,
  platform text not null,
  product_link text,
  unit_purchase_price numeric,
  minimum_order_quantity integer,
  verification_status text not null,
  notes text,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.profit_calculations (
  id uuid primary key default gen_random_uuid(),
  research_run_id uuid not null references public.research_runs(id) on delete cascade,
  product_id uuid not null references public.products(id) on delete cascade,
  scenarios jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.research_settings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  marketplaces text[] not null default array['amazon.ae'],
  categories text[] not null default array['Outdoor camping','Desert picnic accessories','Car accessories','Home and kitchen','Storage and organization'],
  filters jsonb not null default '{}'::jsonb,
  automation jsonb not null default '{"timezone":"Asia/Dubai","cron_utc":"0 5 * * *","products_per_run":20}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.products enable row level security;
alter table public.product_price_history enable row level security;
alter table public.research_runs enable row level security;
alter table public.research_results enable row level security;
alter table public.suppliers enable row level security;
alter table public.profit_calculations enable row level security;
alter table public.research_settings enable row level security;

create policy "authenticated read products" on public.products for select to authenticated using (true);
create policy "authenticated read price history" on public.product_price_history for select to authenticated using (true);
create policy "authenticated read research runs" on public.research_runs for select to authenticated using (true);
create policy "authenticated read research results" on public.research_results for select to authenticated using (true);
create policy "authenticated read suppliers" on public.suppliers for select to authenticated using (true);
create policy "authenticated read profit calculations" on public.profit_calculations for select to authenticated using (true);

create policy "users manage own settings" on public.research_settings
  for all to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists products_touch_updated_at on public.products;
create trigger products_touch_updated_at
before update on public.products
for each row execute function public.touch_updated_at();

drop trigger if exists research_settings_touch_updated_at on public.research_settings;
create trigger research_settings_touch_updated_at
before update on public.research_settings
for each row execute function public.touch_updated_at();

