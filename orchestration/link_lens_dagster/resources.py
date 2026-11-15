"""Resources: the library as the orchestrator's database role, and the LangGraph server.

No resource holds a secret. The library reads its connection from the settings,
and `LINK_LENS_DATABASE_ROLE` makes every connection of this process take the
orchestrator's role, which cannot record a human decision.
"""

import dagster as dg
from sqlalchemy import text

ORCHESTRATOR = "linklens_orchestrator"


class Pipeline(dg.ConfigurableResource):
    """The `link_lens` library, checked to be working as the role it should."""

    role: str = ORCHESTRATOR

    def setup_for_execution(self, context):
        actual = self.scalar("SELECT current_user")
        if actual != self.role:
            raise dg.Failure(
                description=(
                    f"Dagster must work on the database as {self.role}, not {actual}. "
                    f"Set LINK_LENS_DATABASE_ROLE={self.role} for the Dagster processes."
                ),
                allow_retries=False,
            )

    @property
    def steps(self):
        """The refresh steps: check, check_drift, extract, request_onboarding, assemble."""
        from link_lens import refresh

        return refresh

    def scalar(self, sql, **parameters):
        from link_lens import store

        with store.engine().connect() as connection:
            return connection.execute(text(sql), parameters).scalar_one()

    def rows(self, sql, **parameters):
        from link_lens import store

        with store.engine().connect() as connection:
            return [
                dict(row)
                for row in connection.execute(text(sql), parameters).mappings()
            ]


class LangGraph(dg.ConfigurableResource):
    """The LangGraph server that runs the onboarding graph and feeds the Agent Inbox."""

    api_url: str = ""

    def client(self):
        from langgraph_sdk import get_sync_client
        from link_lens.settings import settings

        return get_sync_client(url=self.api_url or settings().api_url)
