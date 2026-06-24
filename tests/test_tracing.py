from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from multi_agent_research_lab.observability import tracing


class _FakeRun:
    id = "run-123"

    def __init__(self) -> None:
        self.ended: dict[str, Any] | None = None

    def get_url(self) -> str:
        return "https://smith.langchain.com/o/example/projects/p/example/r/run-123"

    def end(self, **kwargs: Any) -> None:
        self.ended = kwargs


def test_trace_span_exports_provider_metadata(monkeypatch: Any) -> None:
    run = _FakeRun()

    @contextmanager
    def fake_remote_context(name: str, attributes: dict[str, Any]) -> Iterator[_FakeRun]:
        assert name == "worker"
        assert attributes == {"agent": "researcher"}
        yield run

    monkeypatch.setattr(tracing, "_remote_context", fake_remote_context)

    with tracing.trace_span("worker", {"agent": "researcher"}) as span:
        span["outputs"] = {"source_count": 3}

    assert span["provider"] == "langsmith"
    assert span["run_id"] == "run-123"
    assert span["url"].startswith("https://smith.langchain.com/")
    assert span["status"] == "ok"
    assert run.ended is not None
    assert run.ended["outputs"] == {"source_count": 3}
