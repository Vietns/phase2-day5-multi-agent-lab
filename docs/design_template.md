# System Design

## Problem

Build a research assistant that searches a bounded set of sources, analyzes the evidence, and
writes a cited answer. Run the same query through a single-agent baseline and a supervised
multi-agent workflow so quality, latency, cost, citation coverage, and failures can be compared.

## Why multi-agent?

Long research tasks mix evidence collection, critical analysis, and audience-aware writing.
Separating these stages makes handoffs inspectable and enables stage-specific validation. The
trade-off is more model calls, latency, cost, and possible context loss. For simple queries, the
baseline is expected to be preferable.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Select the next stage and stop safely | Shared state | Route | Loop or early stop |
| Researcher | Search and summarize evidence | Query | Sources and notes | Empty/stale sources |
| Analyst | Compare claims and weak evidence | Research notes | Analysis | Unsupported inference |
| Writer | Produce an audience-aware response | Analysis and sources | Cited answer | Missing citations |
| Critic (optional) | Validate answer/source contract | Answer and sources | Findings | False confidence |

## Shared state

- `request`: validated query, audience, and source limit.
- `iteration` and `route_history`: loop guard and routing audit.
- `sources`, `research_notes`, `analysis_notes`, `final_answer`: explicit handoffs.
- `agent_results`: content plus token/cost metadata per agent.
- `trace`: local JSON spans and routing/error events.
- `errors`: provider and validation failures retained for fallback and evaluation.

## Routing policy

```text
START -> supervisor
supervisor -> researcher (research_notes missing)
supervisor -> analyst    (analysis_notes missing)
supervisor -> writer     (final_answer missing)
supervisor -> END        (answer ready or max iterations reached)
worker -> supervisor
```

## Guardrails

- Max iterations: 6 by default, configurable with `MAX_ITERATIONS`.
- Timeout: 60 seconds by default plus provider request timeouts.
- Retry: three LLM request attempts and two workflow-level worker attempts.
- Fallback: preserve partial notes and return a marked partial answer.
- Validation: Pydantic schemas and required output checks at every stage.

## Benchmark plan

Run the configured GraphRAG, support-workflow, and production-guardrail queries through both
architectures. Measure wall-clock latency, provider token/cost metadata, a deterministic 0-10
smoke rubric, citation coverage, and failure rate. Use peer review to validate heuristic quality
scores before drawing a final conclusion.
