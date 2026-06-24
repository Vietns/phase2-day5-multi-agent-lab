"""Command-line entrypoint for the research lab."""

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.baseline import SingleAgentBaseline
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import flush_traces
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _write_trace(name: str, state: ResearchState) -> str:
    store = LocalArtifactStore()
    path = store.write_text(name, json.dumps(state.trace, indent=2, ensure_ascii=False))
    return str(path)


def _langsmith_links(state: ResearchState) -> list[str]:
    return [str(item["url"]) for item in state.trace if item.get("url")]


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the single-agent comparison baseline."""

    _init()
    state = SingleAgentBaseline().run(query)
    flush_traces()
    trace_path = _write_trace("baseline_trace.json", state)
    console.print(Panel(Markdown(state.final_answer or ""), title="Single-Agent Baseline"))
    console.print(f"Trace: {trace_path}")
    if links := _langsmith_links(state):
        console.print(f"LangSmith: {links[-1]}")


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the supervised multi-agent workflow."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    result = MultiAgentWorkflow().run(state)
    flush_traces()
    trace_path = _write_trace("multi_agent_trace.json", result)
    console.print(Panel(Markdown(result.final_answer or ""), title="Multi-Agent Result"))
    console.print(f"Routes: {' -> '.join(result.route_history)}")
    console.print(f"Trace: {trace_path}")
    if links := _langsmith_links(result):
        console.print(f"LangSmith: {links[-1]}")
    if result.errors:
        console.print(f"Errors: {'; '.join(result.errors)}", style="yellow")


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")] = (
        "Research GraphRAG state-of-the-art and write a 500-word summary"
    ),
) -> None:
    """Compare baseline and multi-agent runs and write a Markdown report."""

    _init()
    baseline_runner = SingleAgentBaseline()
    baseline_state, baseline_metrics = run_benchmark("baseline", query, baseline_runner.run)

    def run_multi(item: str) -> ResearchState:
        return MultiAgentWorkflow().run(ResearchState(request=ResearchQuery(query=item)))

    multi_state, multi_metrics = run_benchmark("multi-agent", query, run_multi)
    flush_traces()
    report = render_markdown_report([baseline_metrics, multi_metrics])
    store = LocalArtifactStore()
    report_path = store.write_text("benchmark_report.md", report)
    store.write_text(
        "benchmark_traces.json",
        json.dumps(
            {"baseline": baseline_state.trace, "multi-agent": multi_state.trace},
            indent=2,
            ensure_ascii=False,
        ),
    )
    console.print(Markdown(report))
    console.print(f"Report: {report_path}")
    links = _langsmith_links(baseline_state) + _langsmith_links(multi_state)
    if links:
        console.print(f"LangSmith traces: {len(links)} (latest: {links[-1]})")


if __name__ == "__main__":
    app()
