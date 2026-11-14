"""The read-only product service: one query layer behind REST, MCP and GraphQL."""


class Problem(Exception):
    """An error a client should see, as RFC 9457 problem details."""

    def __init__(self, status, title, detail=None, retry_after=None):
        super().__init__(title)
        self.status, self.title, self.detail = status, title, detail
        self.retry_after = retry_after
