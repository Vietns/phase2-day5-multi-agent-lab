from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


def test_offline_clients_are_deterministic() -> None:
    llm = LLMClient(api_key="unused", force_mock=True)
    first = llm.complete("You are the analyst", "Analyze evidence")
    second = llm.complete("You are the analyst", "Analyze evidence")
    assert first == second
    assert first.input_tokens

    sources = SearchClient(api_key="").search("Explain GraphRAG", max_results=2)
    assert len(sources) == 2
    assert all(item.metadata["provider"] == "local_mock" for item in sources)


def test_groq_uses_openai_compatible_endpoint() -> None:
    llm = LLMClient(
        api_key="test-key",
        model="test-model",
        provider="groq",
    )

    assert llm.provider == "groq"
    assert llm.base_url == "https://api.groq.com/openai/v1"
    assert llm.model == "test-model"
    assert not llm.is_mock
