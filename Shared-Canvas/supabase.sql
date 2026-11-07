-- Run this once in Supabase: Dashboard > SQL Editor > New query > paste > Run.

create table if not exists contributions (
  id uuid primary key,
  created_at timestamptz default now(),
  t bigint not null,            -- when the stroke was painted (ms), used for replay order and wet paint
  name text,
  feeling text,
  author text,
  params jsonb,                 -- the paint the LLM chose
  seed bigint,
  path jsonb                    -- every frame of the hands, face and voice
);

-- Hackathon-level access: anyone with the anon key can add and read strokes.
alter table contributions enable row level security;
create policy "anyone can read strokes" on contributions for select using (true);
create policy "anyone can add strokes" on contributions for insert with check (true);

-- Push new strokes to every open screen.
alter publication supabase_realtime add table contributions;

-- To wipe the painting and start over (e.g. after testing):
--   delete from contributions;