"""Multi-agent workflow with optional LangGraph execution."""

from collections.abc import Callable
from time import perf_counter
from typing import Any, TypedDict, cast

from multi_agent_research_lab.agents import (
    AnalystAgent,
    CriticAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState


class WorkflowContext(TypedDict):
    state: ResearchState


class _LocalCompiledGraph:
    """Small compatible fallback used when the optional LangGraph extra is absent."""

    def __init__(self, workflow: "MultiAgentWorkflow") -> None:
        self.workflow = workflow

    def invoke(self, context: WorkflowContext) -> WorkflowContext:
        state = context["state"]
        while True:
            self.workflow._supervise(state)
            route = state.route_history[-1]
            if route == "done":
                return {"state": state}
            self.workflow._run_worker(route, state)


class MultiAgentWorkflow:
    """Build and run the supervisor/worker graph with guardrails."""

    def __init__(
        self,
        supervisor: SupervisorAgent | None = None,
        researcher: ResearcherAgent | None = None,
        analyst: AnalystAgent | None = None,
        writer: WriterAgent | None = None,
        critic: CriticAgent | None = None,
        enable_critic: bool = False,
    ) -> None:
        settings = get_settings()
        self.supervisor = supervisor or SupervisorAgent(settings.max_iterations)
        self.workers: dict[str, BaseAgent] = {
            "researcher": researcher or ResearcherAgent(),
            "analyst": analyst or AnalystAgent(),
            "writer": writer or WriterAgent(),
        }
        self.critic = critic or CriticAgent()
        self.enable_critic = enable_critic
        self.timeout_seconds = settings.timeout_seconds
        self._deadline = float("inf")

    def build(self) -> object:
        """Compile a LangGraph graph, or an API-compatible local fallback."""

        try:
            from langgraph.graph import END, StateGraph
        except ImportError:
            return _LocalCompiledGraph(self)

        graph = StateGraph(WorkflowContext)
        graph.add_node("supervisor", cast(Any, self._supervisor_node))
        for name in self.workers:
            graph.add_node(name, cast(Any, self._worker_node(name)))
            graph.add_edge(name, "supervisor")
        graph.set_entry_point("supervisor")
        graph.add_conditional_edges(
            "supervisor",
            self._route,
            {"researcher": "researcher", "analyst": "analyst", "writer": "writer", "done": END},
        )
        return graph.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and validate its final state."""

        self._deadline = perf_counter() + self.timeout_seconds
        result = self.build().invoke({"state": state})  # type: ignore[attr-defined]
        final_state = cast(ResearchState, result["state"])
        if not final_state.final_answer:
            final_state.final_answer = self._fallback_answer(final_state)
        if self.enable_critic:
            self.critic.run(final_state)
        return final_state

    def _supervisor_node(self, context: WorkflowContext) -> WorkflowContext:
        self._supervise(context["state"])
        return context

    def _worker_node(self, name: str) -> Callable[[WorkflowContext], WorkflowContext]:
        def node(context: WorkflowContext) -> WorkflowContext:
            self._run_worker(name, context["state"])
            return context

        return node

    @staticmethod
    def _route(context: WorkflowContext) -> str:
        return context["state"].route_history[-1]

    def _supervise(self, state: ResearchState) -> None:
        if perf_counter() >= self._deadline:
            state.errors.append(f"Workflow timed out after {self.timeout_seconds} seconds")
            if not state.final_answer:
                state.final_answer = self._fallback_answer(state)
            state.record_route("done")
            state.add_trace_event("timeout", {"timeout_seconds": self.timeout_seconds})
            return
        self.supervisor.run(state)

    def _run_worker(self, route: str, state: ResearchState) -> None:
        worker = self.workers[route]
        last_error: Exception | None = None
        for attempt in range(1, 3):
            try:
                worker.run(state)
                return
            except Exception as exc:  # agent boundary intentionally catches provider errors
                last_error = exc
                state.add_trace_event(
                    "agent_error",
                    {"agent": route, "attempt": attempt, "error": str(exc)},
                )
        message = f"{route} failed after 2 attempts: {last_error}"
        state.errors.append(message)
        self._apply_fallback(route, state, message)

    @staticmethod
    def _apply_fallback(route: str, state: ResearchState, message: str) -> None:
        if route == "researcher":
            state.research_notes = f"Research unavailable. Limitation: {message}"
        elif route == "analyst":
            state.analysis_notes = state.research_notes or f"Analysis unavailable: {message}"
        elif route == "writer":
            state.final_answer = MultiAgentWorkflow._fallback_answer(state)
        else:  # pragma: no cover - route is constrained by the supervisor
            raise AgentExecutionError(f"Unknown route: {route}")

    @staticmethod
    def _fallback_answer(state: ResearchState) -> str:
        details = state.analysis_notes or state.research_notes or "No partial result was produced."
        return (
            "## Partial result\n\n"
            f"{details}\n\n"
            "The workflow encountered an error; verify the provider configuration and trace."
        )
