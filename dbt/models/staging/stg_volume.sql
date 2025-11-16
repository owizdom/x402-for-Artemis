{{
  config(
    materialized='view',
    tags=['staging', 'volume']
  )
}}

-- Staging model for volume data from Dune queries
-- Handles both EVM and Solana volume data

with parsed_data as (
    select
        id,
        query_name,
        query_id,
        fetched_at,
        json_extract(raw_json_data, '$') as json_array
    from {{ ref('stg_dune_queries') }}
    where query_name in (
        'x402 volume evm',
        'volume by token evm',
        'x402 volume solana',
        'volume by token solana'
    )
),

expanded as (
    select
        id,
        query_name,
        query_id,
        fetched_at,
        json_extract(value, '$.period') as period,
        json_extract(value, '$.chain') as chain,
        json_extract(value, '$.token') as token,
        json_extract(value, '$.volume') as volume,
        json_extract(value, '$.amount') as amount
    from parsed_data,
    json_each(json_array) as value
)

select
    id,
    query_name,
    query_id,
    fetched_at,
    cast(period as text) as period,
    cast(chain as text) as chain,
    cast(token as text) as token,
    cast(coalesce(volume, amount) as real) as volume_amount,
    case 
        when query_name like '%evm%' then 'evm'
        when query_name like '%solana%' then 'solana'
        else 'unknown'
    end as blockchain_type
from expanded
where period is not null

