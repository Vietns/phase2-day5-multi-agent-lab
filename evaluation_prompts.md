# Multi-Agent LLM Research Evaluation Prompts

This README contains four distinct prompts/tasks for students or LLM systems. Each
prompt is enclosed in a copy-pasteable code block so that it can be copied into an LLM
interface or used as a benchmark query.

## Prompt 1: ResearchAgentBench Benchmark Design

```text
You are part of a university lab designing a benchmark to evaluate AI systems that
assist students with research tasks.

Your task is to design a benchmark called ResearchAgentBench.

The benchmark should evaluate whether an AI system can actually help a graduate
student complete research work, not just produce fluent text.

You must produce a full benchmark design document that includes:
1. Benchmark goal
2. Core assumptions
3. Task categories
4. At least 12 example tasks across different categories
5. A scoring rubric
6. Baselines to compare against
7. Likely failure modes and gaming risks
8. Human evaluation protocol
9. Limitations of the benchmark
10. Recommendations for version 2 of the benchmark

Constraints:
- The benchmark must be realistic for a small academic lab
- It must not depend on expensive annotation
- It must distinguish between usefulness, correctness, and research judgment
- It must include at least one adversarial or stress-test component
- It must explicitly discuss how systems might game the evaluation

Output format:
Write this as a mini design document suitable for discussion in a research lab meeting.
```

## Prompt 2: Evidence-Grounded Literature Review Protocol

```text
You are a research methods specialist helping a university lab evaluate whether an AI
assistant can produce a trustworthy literature review rather than a polished but
unsupported summary.

Your task is to design an evaluation protocol called EvidenceReviewEval.

The protocol should test an AI system's ability to discover relevant literature,
separate primary from secondary evidence, compare conflicting findings, preserve
citations, and communicate uncertainty to a graduate student.

You must produce a complete protocol that includes:
1. Evaluation goal and target users
2. Definition of an evidence-grounded literature review
3. Inclusion and exclusion criteria for sources
4. A taxonomy of research claims
5. At least 10 example review tasks from different academic domains
6. Claim-level citation scoring
7. A method for checking whether citations actually support claims
8. Human reviewer instructions and disagreement resolution
9. Baselines and ablation studies
10. Common failure modes, including fabricated or misleading citations
11. An adversarial task containing irrelevant, duplicated, or contradictory sources
12. A reporting template for final scores

Constraints:
- The protocol must be runnable by a small lab with no more than two reviewers per task
- It must avoid requiring access to expensive proprietary databases
- It must score coverage, correctness, source quality, and uncertainty separately
- It must penalize citation laundering and confident claims based on weak evidence
- It must explain how retrieval quality can be separated from writing quality

Output format:
Write a structured evaluation protocol with tables for the task set and scoring rubric.
Include enough operational detail that another lab could reproduce the evaluation.
```

## Prompt 3: Research Reproducibility Assistant Evaluation

```text
You are evaluating AI assistants that help graduate students reproduce results from
published machine learning papers.

Your task is to design a benchmark called ReproResearchEval.

The benchmark should measure whether an AI system can turn a paper, repository, and
partial experiment log into a realistic reproduction plan and diagnose why observed
results differ from the paper.

You must produce a full benchmark proposal that includes:
1. Benchmark motivation and scope
2. Definition of successful reproduction assistance
3. Required task inputs and expected outputs
4. At least 12 example tasks covering setup, data, code, metrics, and debugging
5. Difficulty levels and task selection criteria
6. Scoring dimensions for correctness, usefulness, reproducibility, and safety
7. Baselines, including a single-agent and a multi-agent system
8. A controlled environment for executing suggested commands
9. Human evaluation protocol for graduate-student reviewers
10. Failure modes such as invented dependencies, data leakage, and unsafe commands
11. A stress test with incomplete documentation and conflicting version information
12. Cost, latency, and token reporting requirements

Constraints:
- The benchmark must not require expensive GPU training for every task
- Most tasks should finish in under 30 minutes using small datasets or mocked execution
- The evaluator must distinguish a good plan from an actually successful reproduction
- Systems must not receive credit for fabricating experiment results
- Unsafe or destructive instructions must receive an explicit penalty

Output format:
Write a mini benchmark paper with sections for methodology, task construction, metrics,
baselines, risks, limitations, and expected findings.
```

## Prompt 4: Multi-Agent Research Failure Audit

```text
You are part of an internal review team auditing a multi-agent research assistant used
by graduate students.

The system contains a Supervisor, Researcher, Analyst, and Writer. In a recent run, the
Researcher retrieved weak sources, the Analyst converted uncertain statements into
facts, the Writer cited sources that did not support the claims, and the Supervisor
allowed repeated retries that increased cost without improving the answer.

Your task is to produce a complete failure audit and redesign proposal.

You must include:
1. A concise incident summary
2. A timeline reconstructed from the agent sequence
3. Root causes separated into model, retrieval, orchestration, and evaluation issues
4. The shared-state fields needed to diagnose each failure
5. Validation gates between Researcher, Analyst, and Writer
6. Retry, timeout, fallback, and stop policies
7. A claim-to-source verification method
8. At least eight regression tests derived from the incident
9. Metrics for detecting recurrence in production
10. A comparison between fixing the multi-agent system and replacing it with a
    single-agent baseline
11. Adversarial tests for prompt injection, source poisoning, and citation manipulation
12. A phased remediation plan for one week, one month, and one semester

Constraints:
- The redesign must be feasible for a small university lab
- It must preserve useful partial results when safe to do so
- It must identify which failures should stop the workflow immediately
- It must discuss the latency and token cost introduced by new guardrails
- It must not assume that adding another agent automatically improves reliability

Output format:
Write an incident review document with an executive summary, root-cause table,
corrective-action plan, regression-test matrix, and final architecture recommendation.
```

## Suggested usage

Run each prompt through both the single-agent baseline and multi-agent workflow. Compare
the results using usefulness, correctness, research judgment, citation quality, latency,
token usage, and failure rate. Keep the full output and trace for peer review instead of
relying only on the automatic heuristic score.
