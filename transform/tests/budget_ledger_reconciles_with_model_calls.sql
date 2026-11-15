-- Attempts, reservations and charges in budget_ledger equal the ledger table.
select ledger.*, stored.attempts as stored_attempts
from (select coalesce(sum(attempts), 0) as attempts,
             coalesce(sum(reservation_usd), 0) as reserved,
             coalesce(sum(charge_usd), 0) as charged
      from {{ ref('budget_ledger') }}) as ledger,
     (select count(*) as attempts,
             coalesce(sum(reservation_usd), 0) as reserved,
             coalesce(sum(charge_usd), 0) as charged
      from {{ source('ops', 'model_call') }}) as stored
where ledger.attempts <> stored.attempts
   or abs(ledger.reserved - stored.reserved) > 1e-9
   or abs(ledger.charged - stored.charged) > 1e-9
