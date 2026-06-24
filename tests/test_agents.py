from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_missing_stages_in_order() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    supervisor = SupervisorAgent(max_iterations=6)

    supervisor.run(state)
    assert state.route_history[-1] == "researcher"

    state.research_notes = "evidence"
    supervisor.run(state)
    assert state.route_history[-1] == "analyst"

    state.analysis_notes = "analysis"
    supervisor.run(state)
    assert state.route_history[-1] == "writer"

    state.final_answer = "answer"
    supervisor.run(state)
    assert state.route_history[-1] == "done"
