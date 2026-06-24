"""Shared state for the multi-agent workflow.

Students should extend this file when adding new agents, outputs, or evaluation metrics.
"""

from typing import Any

from pydantic import BaseModel, Field

from multi_agent_research_lab.core.schemas import AgentResult, ResearchQuery, SourceDocument


class ResearchState(BaseModel):
    """Single source of truth passed through the workflow."""

    request: ResearchQuery
    iteration: int = 0
    route_history: list[str] = Field(default_factory=list)

    sources: list[SourceDocument] = Field(default_factory=list)
    research_notes: str | None = None
    analysis_notes: str | None = None
    final_answer: str | None = None

    agent_results: list[AgentResult] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @property
    def input_tokens(self) -> int:
        return sum(int(item.metadata.get("input_tokens") or 0) for item in self.agent_results)

    @property
    def output_tokens(self) -> int:
        return sum(int(item.metadata.get("output_tokens") or 0) for item in self.agent_results)

    @property
    def estimated_cost_usd(self) -> float | None:
        costs = [item.metadata.get("cost_usd") for item in self.agent_results]
        known_costs = [float(cost) for cost in costs if cost is not None]
        return sum(known_costs) if known_costs else None

    def record_route(self, route: str) -> None:
        self.route_history.append(route)
        self.iteration += 1

    def add_trace_event(self, name: str, payload: dict[str, Any]) -> None:
        self.trace.append({"name": name, "payload": payload})
