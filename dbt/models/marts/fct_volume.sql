{{
  config(
    materialized='table',
    tags=['marts', 'fact', 'volume']
  )
}}

-- Fact table for volume metrics
-- Aggregates volume data by period, chain, and token

select
    period,
    chain,
    token,
    blockchain_type,
    sum(volume_amount) as total_volume,
    avg(volume_amount) as avg_volume,
    max(fetched_at) as last_updated,
    count(*) as data_points
from {{ ref('stg_volume') }}
group by period, chain, token, blockchain_type
order by period desc, total_volume desc

