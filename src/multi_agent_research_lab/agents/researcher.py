"""Researcher agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collect sources and create concise research notes."""

    name = "researcher"

    def __init__(
        self,
        llm: LLMClient | None = None,
        search: SearchClient | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.search = search or SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        with trace_span(self.name, {"query": state.request.query}) as span:
            state.sources = self.search.search(state.request.query, state.request.max_sources)
            if not state.sources:
                raise ValidationError("Researcher returned no sources")
            source_text = "\n".join(
                f"[{index}] {item.title}: {item.snippet} ({item.url or 'no URL'})"
                for index, item in enumerate(state.sources, start=1)
            )
            response = self.llm.complete(
                "You are the researcher. Summarize only supplied evidence and preserve citations.",
                f"Query: {state.request.query}\n\nSources:\n{source_text}",
            )
            if not response.content.strip():
                raise ValidationError("Researcher returned empty notes")
            state.research_notes = response.content
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=response.content,
                    metadata={
                        "source_count": len(state.sources),
                        "provider": self.llm.provider,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )
        state.trace.append(span)
        return state
