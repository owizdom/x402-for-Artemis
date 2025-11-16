{{
  config(
    materialized='table',
    tags=['marts', 'artemis', 'export']
  )
}}

-- Mart model optimized for Artemis Analytics export
-- Combines all metrics into a single denormalized table

with transactions as (
    select
        period,
        project as metric_source,
        'transactions' as metric_type,
        total_transactions as metric_value,
        null as chain,
        null as token,
        null as facilitator,
        'evm' as blockchain_type,
        last_updated
    from {{ ref('fct_transactions') }}
),

volume as (
    select
        period,
        chain as metric_source,
        'volume' as metric_type,
        total_volume as metric_value,
        chain,
        token,
        null as facilitator,
        blockchain_type,
        last_updated
    from {{ ref('fct_volume') }}
),

facilitators as (
    select
        null as period,
        chain as metric_source,
        'facilitators' as metric_type,
        total_count as metric_value,
        chain,
        null as token,
        facilitator,
        blockchain_type,
        last_updated
    from {{ ref('dim_facilitators') }}
)

select
    period,
    metric_source,
    metric_type,
    metric_value,
    chain,
    token,
    facilitator,
    blockchain_type,
    last_updated,
    datetime('now') as exported_at
from transactions

union all

select
    period,
    metric_source,
    metric_type,
    metric_value,
    chain,
    token,
    facilitator,
    blockchain_type,
    last_updated,
    datetime('now') as exported_at
from volume

union all

select
    period,
    metric_source,
    metric_type,
    metric_value,
    chain,
    token,
    facilitator,
    blockchain_type,
    last_updated,
    datetime('now') as exported_at
from facilitators

