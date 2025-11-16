{{
  config(
    materialized='table',
    tags=['marts', 'dimension', 'facilitators']
  )
}}

-- Dimension table for facilitators
-- Provides a clean view of facilitators by chain

select
    chain,
    facilitator,
    blockchain_type,
    sum(facilitator_count) as total_count,
    avg(facilitator_percent) as avg_percent,
    max(fetched_at) as last_updated
from {{ ref('stg_facilitators') }}
where facilitator is not null
group by chain, facilitator, blockchain_type
order by chain, total_count desc

