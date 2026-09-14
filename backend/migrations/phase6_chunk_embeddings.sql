create table if not exists chunk_embeddings (

    id uuid primary key default gen_random_uuid(),

    chunk_id uuid not null
        references document_chunks(id)
        on delete cascade,

    embedding jsonb not null,

    created_at timestamp default now()

);