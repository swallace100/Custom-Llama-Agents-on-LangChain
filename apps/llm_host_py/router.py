def pick_adapter(task: str) -> str:
    t = task.lower()
    if "calendar" in t:
        return "agent_a"
    if "web" in t or "search" in t:
        return "agent_b"
    return "agent_c"
