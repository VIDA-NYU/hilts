import os

def write_state(project_path: str, state: str):
    """
    Write the current state to the state.txt file in the project directory.

    Args:
        project_path (str): Path to the project directory
        state (str): The state to write
    """
    with open(os.path.join(project_path, "state.txt"), "w") as f:
        f.write(state)
