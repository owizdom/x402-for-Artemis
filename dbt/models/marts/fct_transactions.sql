{{
  config(
    materialized='table',
    tags=['marts', 'fact', 'transactions']
  )
}}

-- Fact table for transaction metrics
-- Aggregates transaction data by period and project

select
    period,
    project,
    sum(transaction_count) as total_transactions,
    avg(transaction_percent) as avg_transaction_percent,
    max(fetched_at) as last_updated,
    count(*) as data_points
from {{ ref('stg_transactions') }}
group by period, project
order by period desc, total_transactions desc

