from memory.state import ProjectState

state = ProjectState()

state.project_name = "ResearchForge"

state.topic = "Agentic AI"

state.current_agent = "Planning Agent"

state.status = "planning"

state.keywords.append("LangGraph")

print(state.model_dump())