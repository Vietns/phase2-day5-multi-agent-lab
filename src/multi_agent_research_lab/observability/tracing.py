"""Local JSON tracing with optional LangSmith export."""

import logging
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager, nullcontext
from functools import lru_cache
from importlib import import_module
from time import perf_counter
from typing import Any, cast

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=2)
def _langsmith_client(api_key: str) -> Any:
    module = import_module("langsmith")
    return module.Client(api_key=api_key, timeout_ms=10_000)


def _remote_context(name: str, attributes: dict[str, Any]) -> AbstractContextManager[Any | None]:
    settings = get_settings()
    if not settings.langsmith_api_key:
        return nullcontext(None)
    try:
        module = import_module("langsmith")
        return cast(
            AbstractContextManager[Any | None],
            module.trace(
                name,
                run_type="chain",
                inputs=attributes,
                project_name=settings.langsmith_project,
                client=_langsmith_client(settings.langsmith_api_key),
                tags=["multi-agent-research-lab"],
            ),
        )
    except Exception as exc:
        logger.warning("Could not initialize LangSmith trace: %s", exc)
        return nullcontext(None)


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Capture a local span and mirror it to LangSmith when configured."""

    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
        "provider": "local_json",
    }
    with _remote_context(name, span["attributes"]) as remote_run:
        if remote_run is not None:
            span["provider"] = "langsmith"
            span["run_id"] = str(remote_run.id)
            try:
                span["url"] = remote_run.get_url()
            except Exception as exc:
                logger.debug("Could not create LangSmith run URL: %s", exc)
        try:
            yield span
        except Exception as exc:
            span["status"] = "error"
            span["error"] = str(exc)
            raise
        finally:
            span.setdefault("status", "ok")
            span["duration_seconds"] = perf_counter() - started
            if remote_run is not None:
                remote_run.end(
                    outputs=span.get("outputs") or {"status": span["status"]},
                    error=span.get("error"),
                    metadata={"duration_seconds": span["duration_seconds"]},
                )


def flush_traces(timeout_seconds: float = 10.0) -> None:
    """Flush buffered LangSmith runs without making tracing a workflow dependency."""

    settings = get_settings()
    if not settings.langsmith_api_key:
        return
    try:
        _langsmith_client(settings.langsmith_api_key).flush(timeout=timeout_seconds)
    except Exception as exc:
        logger.warning("Could not flush LangSmith traces: %s", exc)
