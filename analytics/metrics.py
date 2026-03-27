import time
from analytics.logger import log_event


def track_agent_run(agent_name, student_id):
    return AgentMetricTracker(agent_name, student_id)


class AgentMetricTracker:
    def __init__(self, agent_name, student_id):
        self.agent_name = agent_name
        self.student_id = student_id
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        log_event(
            event_type="agent_invocation",
            user_type="system",
            details={
                "agent": self.agent_name,
                "student_id": self.student_id,
                "success": exc_type is None,
                "error": str(exc_val) if exc_val else None,
            },
            duration_ms=duration_ms,
        )
        return False
