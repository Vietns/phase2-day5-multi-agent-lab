"""Provider-independent LLM client with Groq, OpenAI, and offline modes."""

from dataclasses import dataclass
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Select Groq/OpenAI from configuration, falling back to a local mock."""

    GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    VALID_PROVIDERS = {"auto", "groq", "openai", "mock"}

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        force_mock: bool = False,
        provider: str | None = None,
    ) -> None:
        settings = get_settings()
        requested = (provider or settings.llm_provider).lower()
        if requested not in self.VALID_PROVIDERS:
            supported = ", ".join(sorted(self.VALID_PROVIDERS))
            raise ValueError(f"Unsupported LLM provider '{requested}'. Choose: {supported}")

        if force_mock or requested == "mock":
            selected = "mock"
        elif requested == "groq" or (requested == "auto" and settings.groq_api_key):
            selected = "groq"
        elif requested == "openai" or (requested == "auto" and settings.openai_api_key) or api_key:
            selected = "openai"
        else:
            selected = "mock"

        self.provider = selected
        self.api_key = api_key or (
            settings.groq_api_key if selected == "groq" else settings.openai_api_key
        )
        self.model = model or (settings.groq_model if selected == "groq" else settings.openai_model)
        self.base_url = self.GROQ_BASE_URL if selected == "groq" else None
        self.timeout_seconds = timeout_seconds or settings.timeout_seconds
        self.is_mock = selected == "mock"

        if not self.is_mock and not self.api_key:
            key_name = "GROQ_API_KEY" if selected == "groq" else "OPENAI_API_KEY"
            raise AgentExecutionError(f"LLM_PROVIDER={selected} requires {key_name}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.25, max=2), reraise=True)
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a completion and provider usage metadata."""

        if self.is_mock:
            content = self._mock_complete(system_prompt, user_prompt)
            return LLMResponse(
                content=content,
                input_tokens=self._estimate_tokens(system_prompt + user_prompt),
                output_tokens=self._estimate_tokens(content),
                cost_usd=0.0,
            )

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise AgentExecutionError(
                'A provider key is set but the SDK is missing; install with pip install -e ".[llm]"'
            ) from exc

        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                max_retries=0,
            )
            if self.provider == "openai" and hasattr(client, "responses"):
                responses_result = client.responses.create(
                    model=self.model,
                    instructions=system_prompt,
                    input=user_prompt,
                )
                usage = getattr(responses_result, "usage", None)
                return LLMResponse(
                    content=responses_result.output_text,
                    input_tokens=self._usage_value(usage, "input_tokens"),
                    output_tokens=self._usage_value(usage, "output_tokens"),
                )

            chat_result = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            usage = chat_result.usage
            return LLMResponse(
                content=chat_result.choices[0].message.content or "",
                input_tokens=getattr(usage, "prompt_tokens", None),
                output_tokens=getattr(usage, "completion_tokens", None),
            )
        except Exception as exc:  # pragma: no cover - requires provider access
            raise AgentExecutionError(f"{self.provider} request failed: {exc}") from exc

    @staticmethod
    def _usage_value(usage: Any, name: str) -> int | None:
        value = getattr(usage, name, None)
        return int(value) if value is not None else None

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    @staticmethod
    def _mock_complete(system_prompt: str, user_prompt: str) -> str:
        role = system_prompt.lower()
        compact = " ".join(user_prompt.split())
        if "researcher" in role:
            return (
                "The sources cover implementation, research, and evaluation perspectives.\n"
                f"- Research task: {compact[:220]}\n"
                "- Prefer primary documentation and papers over unsupported summaries.\n"
                "- State recency and source limitations explicitly."
            )
        if "analyst" in role:
            return (
                "## Main findings\n"
                "1. Specialized stages work when handoffs have a clear schema.\n"
                "2. Multi-agent orchestration improves inspectability but adds latency and cost.\n"
                "3. Claims without captured sources should be marked as uncertain.\n\n"
                "## Risks\nWeak sources, stale evidence, routing loops, and context loss."
            )
        if "writer" in role or "baseline" in role:
            return (
                "## Summary\n\n"
                f"{compact[:650]}\n\n"
                "A robust answer separates sourced findings from interpretation, preserves "
                "citations, and states evidence limitations. Multi-agent designs help most when "
                "the task benefits from specialized stages; simple questions often favor a "
                "single agent because it is faster and cheaper."
            )
        return compact[:1000]
