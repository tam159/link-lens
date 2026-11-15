"""The operations console: an admin API for the people who run the product, and its pages.

The product owner adds and manages sources, records releases and manages
clients here instead of in a terminal. Every route is a few lines over the
library function the CLI calls, so no rule lives only in the API. Every request
is signed in, every change is checked against the signer's role in the API and
written to the audit log, and the pages hold no database credentials: they
call the API and nothing else.

It is not the product service, which only reads and answers clients, and it
does not replace the Dagster UI (operating), the dashboards (observing) or the
Agent Inbox (reviewing a mapping); it links to them.
"""
