"""Search client with Tavily and local deterministic backends."""

import json
from urllib.request import Request, urlopen

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Search Tavily when configured, otherwise return a small curated corpus."""

    def __init__(self, api_key: str | None = None, timeout_seconds: float | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.tavily_api_key
        self.timeout_seconds = timeout_seconds or settings.timeout_seconds
        self.is_mock = not self.api_key

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Return normalized source documents."""

        if not query.strip():
            raise ValueError("query must not be empty")
        if self.is_mock:
            return self._mock_search(query, max_results)

        payload = json.dumps(
            {"api_key": self.api_key, "query": query, "max_results": max_results}
        ).encode("utf-8")
        request = Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                body = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - requires provider access
            raise AgentExecutionError(f"Search request failed: {exc}") from exc
        return [
            SourceDocument(
                title=item.get("title") or "Untitled source",
                url=item.get("url"),
                snippet=item.get("content") or item.get("snippet") or "",
                metadata={"provider": "tavily", "score": item.get("score")},
            )
            for item in body.get("results", [])[:max_results]
        ]

    @staticmethod
    def _mock_search(query: str, max_results: int) -> list[SourceDocument]:
        graph_sources = [
            SourceDocument(
                title="GraphRAG: Unlocking LLM discovery on narrative private data",
                url="https://www.microsoft.com/en-us/research/project/graphrag/",
                snippet=(
                    "Microsoft Research overview of graph-based retrieval augmented generation."
                ),
            ),
            SourceDocument(
                title="From Local to Global: A Graph RAG Approach",
                url="https://arxiv.org/abs/2404.16130",
                snippet="Paper describing community summaries for global corpus questions.",
            ),
            SourceDocument(
                title="Microsoft GraphRAG repository",
                url="https://github.com/microsoft/graphrag",
                snippet="Reference implementation, indexing pipeline, configuration, and examples.",
            ),
        ]
        agent_sources = [
            SourceDocument(
                title="Building effective agents",
                url="https://www.anthropic.com/engineering/building-effective-agents",
                snippet="Patterns and trade-offs for workflows, routing, and autonomous agents.",
            ),
            SourceDocument(
                title="OpenAI agent orchestration",
                url="https://developers.openai.com/api/docs/guides/agents/orchestration",
                snippet="Guidance for manager-style orchestration and agent handoffs.",
            ),
            SourceDocument(
                title="LangGraph overview",
                url="https://docs.langchain.com/oss/python/langgraph/overview",
                snippet="Graph runtime concepts for durable, stateful agent workflows.",
            ),
        ]
        corpus = graph_sources if "graphrag" in query.lower() else agent_sources
        return [
            item.model_copy(update={"metadata": {"provider": "local_mock"}})
            for item in corpus[:max_results]
        ]
