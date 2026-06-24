from multi_agent_research_lab.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.openai_model
    assert settings.groq_model
    assert settings.llm_provider in {"auto", "groq", "openai", "mock"}
    assert settings.max_iterations >= 1
