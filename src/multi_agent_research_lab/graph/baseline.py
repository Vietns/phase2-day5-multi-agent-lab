"""Single-agent comparison baseline."""

from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class SingleAgentBaseline:
    """Perform search, analysis, and writing in one model call."""

    def __init__(
        self,
        llm: LLMClient | None = None,
        search: SearchClient | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.search = search or SearchClient()

    def run(self, query: str) -> ResearchState:
        state = ResearchState(request=ResearchQuery(query=query))
        with trace_span("baseline", {"query": query}) as span:
            state.sources = self.search.search(query, state.request.max_sources)
            source_text = "\n".join(
                f"[{index}] {item.title}: {item.snippet} ({item.url or 'no URL'})"
                for index, item in enumerate(state.sources, start=1)
            )
            response = self.llm.complete(
                (
                    "You are a single-agent research baseline. Research, analyze, and answer "
                    "with citations."
                ),
                f"Query: {query}\nAudience: {state.request.audience}\n\nSources:\n{source_text}",
            )
            if not response.content.strip():
                raise ValidationError("Baseline returned an empty answer")
            references = "\n".join(
                f"{index}. [{item.title}]({item.url})" if item.url else f"{index}. {item.title}"
                for index, item in enumerate(state.sources, start=1)
            )
            state.final_answer = f"{response.content.rstrip()}\n\n## Sources\n\n{references}"
            state.record_route("baseline")
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.BASELINE,
                    content=state.final_answer,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                        "citation_count": len(state.sources),
                    },
                )
            )
        state.trace.append(span)
        return state
