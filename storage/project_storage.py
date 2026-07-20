from pathlib import Path

from memory.state import ProjectState


class ProjectStorage:


    def __init__(
        self,
        project_dir: str = "projects"
    ):

        self.project_dir = Path(
            project_dir
        )

        self.project_dir.mkdir(
            exist_ok=True
        )


    def save(
        self,
        state: ProjectState,
        filename: str
    ):

        path = self.project_dir / f"{filename}.json"

        path.write_text(
            state.model_dump_json(
                indent=4
            ),
            encoding="utf-8"
        )


    def load(
        self,
        filename: str
    ) -> ProjectState:

        path = self.project_dir / f"{filename}.json"

        return ProjectState.model_validate_json(
            path.read_text(
                encoding="utf-8"
            )
        )


    def list_projects(
        self
    ):

        return sorted(

            file.stem

            for file in self.project_dir.glob(
                "*.json"
            )

        )


    def delete(
        self,
        filename: str
    ):

        path = self.project_dir / f"{filename}.json"

        if path.exists():

            path.unlink()