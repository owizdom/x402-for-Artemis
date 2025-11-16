{{
  config(
    materialized='view',
    tags=['staging', 'dune']
  )
}}

-- Staging model for raw Dune query results
-- This model reads from the SQLite database and prepares data for transformation

select
    id,
    logical_name as query_name,
    query_id,
    data as raw_json_data,
    timestamp as fetched_at,
    row_count,
    created_at
from {{ source('raw', 'query_results') }}

