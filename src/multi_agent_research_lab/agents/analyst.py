"""Analyst agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turn research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        if not state.research_notes:
            raise ValidationError("Analyst requires research_notes")
        with trace_span(self.name) as span:
            response = self.llm.complete(
                "You are the analyst. Compare viewpoints, extract claims, and flag weak evidence.",
                f"Query: {state.request.query}\n\nResearch notes:\n{state.research_notes}",
            )
            if not response.content.strip():
                raise ValidationError("Analyst returned empty notes")
            state.analysis_notes = response.content
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.ANALYST,
                    content=response.content,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )
        state.trace.append(span)
        return state
