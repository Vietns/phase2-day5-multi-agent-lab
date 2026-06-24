"""Reproducible benchmark helpers for single-agent and multi-agent runs."""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Run once and calculate latency, usage, quality, citations, and failures."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    coverage = _citation_coverage(state)
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=state.estimated_cost_usd,
        quality_score=_quality_score(state, coverage),
        citation_coverage=coverage,
        failure_rate=1.0 if state.errors or not state.final_answer else 0.0,
        input_tokens=state.input_tokens,
        output_tokens=state.output_tokens,
        notes="; ".join(state.errors) if state.errors else "Completed",
    )
    return state, metrics


def _citation_coverage(state: ResearchState) -> float:
    if not state.sources or not state.final_answer:
        return 0.0
    citable = [source for source in state.sources if source.url]
    if not citable:
        return 0.0
    cited = sum(source.url in state.final_answer for source in citable if source.url)
    return cited / len(citable)


def _quality_score(state: ResearchState, citation_coverage: float) -> float:
    answer = state.final_answer or ""
    score = 0.0
    score += 4.0 if len(answer) >= 200 else min(4.0, len(answer) / 50)
    score += 2.0 if "## Sources" in answer else 0.0
    score += 2.0 * citation_coverage
    score += 2.0 if not state.errors else 0.0
    return round(min(10.0, score), 1)
