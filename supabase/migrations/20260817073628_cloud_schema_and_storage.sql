begin;

create table if not exists public.organizations (
  id serial primary key,
  name varchar not null unique
);

create table if not exists public.platform_announcements (
  id serial primary key,
  title varchar not null,
  message text not null,
  severity varchar not null,
  audience varchar not null,
  active boolean not null,
  created_at timestamptz not null
);

create table if not exists public.users (
  id serial primary key,
  name varchar,
  email varchar unique,
  password varchar,
  role varchar,
  organization_id integer references public.organizations(id) on delete set null
);

create table if not exists public.analysis_jobs (
  id varchar(36) primary key,
  user_id integer not null references public.users(id) on delete cascade,
  status varchar(30) not null,
  stage varchar(80) not null,
  progress integer not null,
  image_key varchar not null,
  image_url varchar,
  sensitivity double precision not null,
  label_text text,
  analysis_id varchar,
  error_message text,
  created_at timestamptz not null,
  started_at timestamptz,
  completed_at timestamptz
);

create table if not exists public.analysis_records (
  id serial primary key,
  analysis_id varchar not null unique,
  user_id integer not null references public.users(id) on delete cascade,
  image_url varchar not null,
  model_name varchar not null,
  model_version varchar not null,
  ai_destination varchar,
  ai_confidence double precision,
  manual_review_required boolean not null,
  result_json text not null,
  review_status varchar not null,
  final_destination varchar,
  reviewer_id integer references public.users(id) on delete set null,
  review_reason text,
  reviewed_at timestamptz,
  created_at timestamptz not null
);

create table if not exists public.audit_logs (
  id serial primary key,
  user_id integer references public.users(id) on delete set null,
  action varchar(100) not null,
  entity_type varchar(80) not null,
  entity_id varchar(100),
  details_json text not null,
  request_id varchar(64),
  created_at timestamptz not null
);

create table if not exists public.inventory (
  id serial primary key,
  waste_batch_id varchar unique,
  fabric_type varchar,
  source varchar,
  quantity varchar,
  quantity_kg double precision,
  color varchar,
  condition varchar,
  collection_date varchar,
  status varchar,
  uploaded_by varchar,
  assigned_to varchar,
  image_url varchar,
  analysis_results varchar,
  owner_id integer references public.users(id) on delete set null
);

create table if not exists public.model_versions (
  id serial primary key,
  model_key varchar(100) not null,
  version varchar(120) not null,
  architecture varchar(120) not null,
  dataset varchar(255) not null,
  metrics_json text not null,
  artifact_path varchar not null,
  stage varchar(30) not null,
  approved_by integer references public.users(id) on delete set null,
  approved_at timestamptz,
  active boolean not null,
  created_at timestamptz not null
);

create table if not exists public.notification_receipts (
  id serial primary key,
  user_id integer not null references public.users(id) on delete cascade,
  notification_key varchar(255) not null,
  read_at timestamptz not null,
  constraint uq_notification_receipt unique (user_id, notification_key)
);

create table if not exists public.notifications (
  id serial primary key,
  user_id integer references public.users(id) on delete cascade,
  category varchar(50) not null,
  title varchar(160) not null,
  message text not null,
  severity varchar(20) not null,
  action_url varchar,
  created_at timestamptz not null
);

create table if not exists public.waste_assessments (
  id serial primary key,
  waste_batch_id integer not null unique references public.inventory(id) on delete cascade,
  quantity_kg double precision not null,
  recyclability_score double precision not null,
  condition_score double precision not null,
  reuse_score double precision not null,
  environmental_benefit_score double precision not null,
  processing_feasibility_score double precision not null,
  material_recovery_score double precision not null,
  sustainability_score double precision not null,
  circularity_score double precision not null,
  circularity_category varchar not null,
  co2_saved_kg double precision not null,
  water_saved_litres double precision not null,
  landfill_reduction_kg double precision not null,
  recoverable_material_kg double precision not null,
  recommended_action varchar not null,
  recommended_processing_method varchar not null,
  recommendation_reason text not null,
  audit_log text not null default '[]',
  created_at timestamptz not null,
  updated_at timestamptz not null
);

create index if not exists ix_users_organization_id on public.users(organization_id);
create index if not exists ix_analysis_jobs_created_at on public.analysis_jobs(created_at);
create index if not exists ix_analysis_jobs_user_id on public.analysis_jobs(user_id);
create index if not exists ix_analysis_jobs_status on public.analysis_jobs(status);
create index if not exists ix_analysis_jobs_analysis_id on public.analysis_jobs(analysis_id);
create index if not exists ix_analysis_records_review_status on public.analysis_records(review_status);
create index if not exists ix_analysis_records_manual_review_required on public.analysis_records(manual_review_required);
create index if not exists ix_analysis_records_created_at on public.analysis_records(created_at);
create index if not exists ix_analysis_records_user_id on public.analysis_records(user_id);
create index if not exists ix_analysis_records_final_destination on public.analysis_records(final_destination);
create index if not exists ix_analysis_records_ai_destination on public.analysis_records(ai_destination);
create index if not exists ix_analysis_records_reviewer_id on public.analysis_records(reviewer_id);
create index if not exists ix_audit_logs_action on public.audit_logs(action);
create index if not exists ix_audit_logs_created_at on public.audit_logs(created_at);
create index if not exists ix_audit_logs_request_id on public.audit_logs(request_id);
create index if not exists ix_audit_logs_user_id on public.audit_logs(user_id);
create index if not exists ix_inventory_owner_id on public.inventory(owner_id);
create index if not exists ix_inventory_quantity_kg on public.inventory(quantity_kg);
create index if not exists ix_model_versions_created_at on public.model_versions(created_at);
create index if not exists ix_model_versions_stage on public.model_versions(stage);
create index if not exists ix_model_versions_active on public.model_versions(active);
create index if not exists ix_model_versions_model_key on public.model_versions(model_key);
create index if not exists ix_model_versions_approved_by on public.model_versions(approved_by);
create index if not exists ix_notification_receipts_user_id on public.notification_receipts(user_id);
create index if not exists ix_notifications_user_id on public.notifications(user_id);
create index if not exists ix_notifications_created_at on public.notifications(created_at);
create index if not exists ix_notifications_category on public.notifications(category);
create index if not exists ix_waste_assessments_circularity_category on public.waste_assessments(circularity_category);

alter table public.organizations enable row level security;
alter table public.platform_announcements enable row level security;
alter table public.users enable row level security;
alter table public.analysis_jobs enable row level security;
alter table public.analysis_records enable row level security;
alter table public.audit_logs enable row level security;
alter table public.inventory enable row level security;
alter table public.model_versions enable row level security;
alter table public.notification_receipts enable row level security;
alter table public.notifications enable row level security;
alter table public.waste_assessments enable row level security;

revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;

insert into storage.buckets (id, name, public)
values ('garment-uploads', 'garment-uploads', false)
on conflict (id) do update set public = excluded.public;

commit;
