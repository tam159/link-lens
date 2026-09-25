# Third-party components

- Agent Inbox: https://github.com/langchain-ai/agent-inbox, commit `cb3af21f9bd3ec04161c0a3202d6eb344371f415`. Built unchanged in the frontend image; upstream MIT licence stays in that image. Its locked dependency tree is installed with `yarn --frozen-lockfile`.
- Open Knowledge Format: https://github.com/GoogleCloudPlatform/open-knowledge-format, commit `ad30107c31c06aec8a7d5636e0d1058118604e6f`, specification v0.2. The minimal parser and standard viewer are vendored in `src/link_lens/_vendor/okf`, with Google copyright headers and Apache-2.0 licence. Only the Python import namespace is adapted, plus escaping embedded JSON against HTML script termination and resolving relative evidence links inside the viewer. This avoids installing Google's unrelated agent and BigQuery dependencies just to generate a viewer.
- Python dependencies and exact resolved versions: `uv.lock`. The LangGraph development runtime is for local development, not an unrestricted production deployment licence.
- Public data retain their source-specific licences. Each immutable snapshot records its licence, resource URL, retrieval time and hash; claims copy the licence. Attribution is generated into OKF source documents. Check the snapshot licence before redistributing raw source files.
- The supplied assignment and ontology belong to their original author. They are inputs, not Link Lens-authored material. No repository has been published.

The viewer references upstream CDN JavaScript libraries. A saved bundle needs no model credentials or database; the HTML viewer currently needs those CDN assets to load. The Markdown and JSON outputs are readable offline.

Agent Server compatibility: `runtime_compat.py` applies a narrow runtime guard for the locked runtime-inmem checkpoint flush registration and normalizes nullable resume `goto`. Remove/retest this guard when upgrading those dependencies.
