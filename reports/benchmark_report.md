# Benchmark Report

| Run | Latency (s) | Cost (USD) | Quality | Citations | Failure | Tokens in/out |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 5.555 | n/a | 10.0 | 100% | 0% | 175/547 |
| multi-agent | 12.803 | n/a | 10.0 | 100% | 0% | 893/1065 |

## Analysis

- **Latency:** baseline was fastest in this sample (5.555s).
- **Quality:** baseline received the highest heuristic score (10.0/10).

## Failure modes and mitigations

Search or model providers can time out, return empty output, or produce weak citations. The workflow limits iterations and request duration, retries each worker twice, validates stage outputs, records errors in the trace, and returns a partial fallback answer instead of looping indefinitely.

## Method note

Quality is a deterministic smoke-test rubric (answer completeness, source section, citation coverage, and error-free completion). Replace or supplement it with blinded peer review for a graded experiment.
