from agentdojo.task_suite.load_suites import get_suite

AGENTDOJO_SUITES = ["slack", "banking", "travel", "workspace"]
AGENTDYN_SUITES = ["shopping", "github", "dailylife"]


def _task_ids(tasks: dict, prefix: str) -> list[int]:
    return sorted(int(task_id.removeprefix(prefix)) for task_id in tasks)


def initialize_dataset(suite_name, benign=False, benchmark_version="v1.2"):
    """Enumerate task ids straight from the suite registry.

    Returns user-task ids for benign runs, else the full cross product of
    (user_task_id, injection_task_id) pairs. Deriving the ids from the loaded
    suite keeps this correct across benchmark versions and for the AgentDyn
    suites (shopping/github/dailylife), whose id ranges differ per suite.
    """
    suite = get_suite(benchmark_version, suite_name)
    user_ids = _task_ids(suite.user_tasks, "user_task_")
    if benign:
        return user_ids
    injection_ids = _task_ids(suite.injection_tasks, "injection_task_")
    return [(u, i) for u in user_ids for i in injection_ids]
