{{
  config(
    materialized='view',
    tags=['staging', 'facilitators']
  )
}}

-- Staging model for facilitator data from Dune queries
-- Handles both chain-based and Solana facilitator data

with parsed_data as (
    select
        id,
        query_name,
        query_id,
        fetched_at,
        json_extract(raw_json_data, '$') as json_array
    from {{ ref('stg_dune_queries') }}
    where query_name in (
        'facilitators by chain',
        'facilitators by chain percent',
        'facilitators solana'
    )
),

expanded as (
    select
        id,
        query_name,
        query_id,
        fetched_at,
        json_extract(value, '$.chain') as chain,
        json_extract(value, '$.facilitator') as facilitator,
        json_extract(value, '$.count') as facilitator_count,
        json_extract(value, '$.percent') as facilitator_percent
    from parsed_data,
    json_each(json_array) as value
)

select
    id,
    query_name,
    query_id,
    fetched_at,
    cast(chain as text) as chain,
    cast(facilitator as text) as facilitator,
    cast(facilitator_count as integer) as facilitator_count,
    cast(facilitator_percent as real) as facilitator_percent,
    case 
        when query_name like '%solana%' then 'solana'
        else 'evm'
    end as blockchain_type
from expanded
where chain is not null or facilitator is not null

