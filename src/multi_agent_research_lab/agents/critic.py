"""Optional deterministic critic agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Check the minimum answer and citation contract."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        if not state.final_answer:
            raise ValidationError("Critic requires final_answer")
        findings: list[str] = []
        if "## Sources" not in state.final_answer:
            findings.append("Missing Sources section")
        has_captured_url = any(
            source.url in state.final_answer for source in state.sources if source.url
        )
        if state.sources and not has_captured_url:
            findings.append("Captured source URLs are not referenced")
        content = "Passed citation checks" if not findings else "; ".join(findings)
        state.agent_results.append(AgentResult(agent=AgentName.CRITIC, content=content))
        state.add_trace_event("critic", {"passed": not findings, "findings": findings})
        return state
