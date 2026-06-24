from multi_agent_research_lab.agents import AnalystAgent, ResearcherAgent, WriterAgent
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.graph.baseline import SingleAgentBaseline
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


def _mock_llm() -> LLMClient:
    return LLMClient(api_key="unused", force_mock=True)


class _FailingSearch(SearchClient):
    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        raise RuntimeError("search unavailable")


def test_multi_agent_workflow_runs_end_to_end() -> None:
    llm = _mock_llm()
    workflow = MultiAgentWorkflow(
        researcher=ResearcherAgent(llm, SearchClient(api_key="")),
        analyst=AnalystAgent(llm),
        writer=WriterAgent(llm),
    )
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))

    result = workflow.run(state)

    assert result.final_answer
    assert "## Sources" in result.final_answer
    assert result.route_history == ["researcher", "analyst", "writer", "done"]
    assert len(result.agent_results) == 3
    assert not result.errors


def test_baseline_and_metrics_include_citations() -> None:
    baseline = SingleAgentBaseline(_mock_llm(), SearchClient(api_key=""))
    state, metrics = run_benchmark("baseline", "Explain GraphRAG", baseline.run)

    assert state.final_answer
    assert metrics.citation_coverage == 1.0
    assert metrics.quality_score == 10.0
    assert metrics.failure_rate == 0.0


def test_worker_failure_is_recorded_and_falls_back() -> None:
    llm = _mock_llm()
    workflow = MultiAgentWorkflow(
        researcher=ResearcherAgent(llm, _FailingSearch(api_key="")),
        analyst=AnalystAgent(llm),
        writer=WriterAgent(llm),
    )
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))

    result = workflow.run(state)

    assert result.final_answer
    assert result.errors
    assert "researcher failed after 2 attempts" in result.errors[0]
    assert any(event.get("name") == "agent_error" for event in result.trace)
