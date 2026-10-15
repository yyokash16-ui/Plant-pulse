-- PlantPulse starter schema. Review and adapt before production.
create extension if not exists pgcrypto;
create table if not exists public.equipment (
 id uuid primary key default gen_random_uuid(),
 equipment_tag text not null unique,
 equipment_type text not null,
 description text,
 site_name text,
 created_at timestamptz not null default now()
);
create table if not exists public.telemetry (
 id bigint generated always as identity primary key,
 equipment_id uuid not null references public.equipment(id) on delete cascade,
 recorded_at timestamptz not null,
 source text not null default 'demo',
 quality text not null default 'unknown' check (quality in ('good','uncertain','bad','unknown')),
 suction_pressure_bar numeric,
 discharge_pressure_bar numeric,
 flow_m3_h numeric,
 bearing_temperature_c numeric,
 vibration_mm_s numeric,
 motor_current_a numeric,
 created_at timestamptz not null default now()
);
create index if not exists telemetry_equipment_time_idx on public.telemetry(equipment_id, recorded_at desc);
create table if not exists public.alarms (
 id uuid primary key default gen_random_uuid(),
 equipment_id uuid not null references public.equipment(id) on delete cascade,
 alarm_key text not null,
 severity text not null check (severity in ('info','warning','critical')),
 title text not null,
 observed_value numeric,
 unit text,
 status text not null default 'active' check (status in ('active','acknowledged','resolved')),
 triggered_at timestamptz not null default now(),
 acknowledged_at timestamptz,
 acknowledged_by uuid references auth.users(id),
 resolved_at timestamptz,
 metadata jsonb not null default '{}'::jsonb
);
create index if not exists alarms_equipment_time_idx on public.alarms(equipment_id, triggered_at desc);
create table if not exists public.event_log (
 id uuid primary key default gen_random_uuid(),
 equipment_id uuid references public.equipment(id) on delete set null,
 actor_id uuid references auth.users(id),
 event_type text not null,
 title text not null,
 detail text,
 created_at timestamptz not null default now(),
 metadata jsonb not null default '{}'::jsonb
);
alter table public.equipment enable row level security;
alter table public.telemetry enable row level security;
alter table public.alarms enable row level security;
alter table public.event_log enable row level security;
-- No permissive public policies are created. Configure authenticated policies for your site/tenant model.
insert into public.equipment(equipment_tag,equipment_type,description,site_name)
values('P-101','centrifugal_pump','Cooling water circulation pump — demo asset','Demo Plant · Unit 01')
on conflict(equipment_tag) do nothing;
