from langgraph.graph import (
    StateGraph,
    START,
    END
)

from memory.state import ProjectState

from workflow.router import WorkflowRouter

from workflow.nodes import (
    planning_node,
    literature_node,
    synthesis_node,
    manuscript_node,
    citation_node,
    reviewer_node
)


router = WorkflowRouter()

builder = StateGraph(
    ProjectState
)


# -------------------------------------------------
# Nodes
# -------------------------------------------------

builder.add_node(
    "planning",
    planning_node
)

builder.add_node(
    "literature",
    literature_node
)

builder.add_node(
    "synthesis",
    synthesis_node
)

builder.add_node(
    "manuscript",
    manuscript_node
)

builder.add_node(
    "citation",
    citation_node
)

builder.add_node(
    "reviewer",
    reviewer_node
)


# -------------------------------------------------
# Router
# -------------------------------------------------

def route(
    state: ProjectState
):

    action = router.route(
        state.user_input
    )

    return action.agent


# -------------------------------------------------
# Conditional Routing
# -------------------------------------------------

builder.add_conditional_edges(

    START,

    route,

    {

        "planning": "planning",

        "literature": "literature",

        "synthesis": "synthesis",

        "manuscript": "manuscript",

        "citation": "citation",

        "reviewer": "reviewer"

    }

)


# -------------------------------------------------
# End Nodes
# -------------------------------------------------

builder.add_edge(
    "planning",
    END
)

builder.add_edge(
    "literature",
    END
)

builder.add_edge(
    "synthesis",
    END
)

builder.add_edge(
    "manuscript",
    END
)

builder.add_edge(
    "citation",
    END
)

builder.add_edge(
    "reviewer",
    END
)


# -------------------------------------------------
# Compile Graph
# -------------------------------------------------

graph = builder.compile()