from memory.state import ProjectState

from storage.project_storage import ProjectStorage


storage = ProjectStorage()


state = ProjectState()

state.project_name = "ResearchForge"

state.topic = "Fetal ECG"

state.description = "Testing Storage"


storage.save(
    state,
    "demo_project"
)


loaded = storage.load(
    "demo_project"
)


print()

print(loaded.project_name)

print(loaded.topic)

print(loaded.description)

print()

print(storage.list_projects())