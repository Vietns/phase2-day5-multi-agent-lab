"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render metrics plus a concise comparison and failure-mode discussion."""

    lines = [
        "# Benchmark Report",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Citations | Failure | Tokens in/out |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in metrics:
        cost = "n/a" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "n/a" if item.quality_score is None else f"{item.quality_score:.1f}"
        coverage = "n/a" if item.citation_coverage is None else f"{item.citation_coverage:.0%}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.3f} | {cost} | {quality} | "
            f"{coverage} | {item.failure_rate:.0%} | {item.input_tokens}/{item.output_tokens} |"
        )

    lines.extend(["", "## Analysis", ""])
    if len(metrics) >= 2:
        fastest = min(metrics, key=lambda item: item.latency_seconds)
        highest = max(metrics, key=lambda item: item.quality_score or 0)
        lines.append(
            f"- **Latency:** {fastest.run_name} was fastest in this sample "
            f"({fastest.latency_seconds:.3f}s)."
        )
        lines.append(
            f"- **Quality:** {highest.run_name} received the highest heuristic score "
            f"({highest.quality_score or 0:.1f}/10)."
        )
    else:
        lines.append("- Add both baseline and multi-agent runs for a direct comparison.")

    lines.extend(
        [
            "",
            "## Failure modes and mitigations",
            "",
            "Search or model providers can time out, return empty output, or produce weak "
            "citations. The workflow limits iterations and request duration, retries each worker "
            "twice, validates stage outputs, records errors in the trace, and returns a partial "
            "fallback answer instead of looping indefinitely.",
            "",
            "## Method note",
            "",
            "Quality is a deterministic smoke-test rubric (answer completeness, source section, "
            "citation coverage, and error-free completion). Replace or supplement it with blinded "
            "peer review for a graded experiment.",
        ]
    )
    return "\n".join(lines) + "\n"
