{{
  config(
    materialized='view',
    tags=['staging', 'transactions']
  )
}}

-- Staging model for transaction data from Dune queries
-- Parses JSON data and extracts transaction metrics

with parsed_data as (
    select
        id,
        query_name,
        query_id,
        fetched_at,
        json_extract(raw_json_data, '$') as json_array
    from {{ ref('stg_dune_queries') }}
    where query_name in ('num transactions', 'num transactions percent')
),

expanded as (
    select
        id,
        query_name,
        query_id,
        fetched_at,
        json_extract(value, '$.period') as period,
        json_extract(value, '$.project') as project,
        json_extract(value, '$.txs') as transaction_count,
        json_extract(value, '$.percent') as transaction_percent
    from parsed_data,
    json_each(json_array) as value
)

select
    id,
    query_name,
    query_id,
    fetched_at,
    cast(period as text) as period,
    cast(project as text) as project,
    cast(transaction_count as integer) as transaction_count,
    cast(transaction_percent as real) as transaction_percent
from expanded
where period is not null

