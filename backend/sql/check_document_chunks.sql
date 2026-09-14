select
    column_name,
    data_type
from information_schema.columns
where table_name = 'document_chunks'
order by ordinal_position;