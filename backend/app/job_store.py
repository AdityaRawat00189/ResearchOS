import threading
from typing import Optional


class JobStore:

    def __init__(self):
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, job_id: str, initial_state: dict) -> None:
        """Register a new job."""
        with self._lock:
            self._store[job_id] = initial_state

    def get(self, job_id: str) -> Optional[dict]:
        """Retrieve the current state of a job."""
        with self._lock:
            return self._store.get(job_id)

    def update(self, job_id: str, updates: dict) -> None:
        """Merge updates into an existing job's state."""
        with self._lock:
            if job_id in self._store:
                self._store[job_id].update(updates)

    def set_status(self, job_id: str, status: str, node: str = "",
                   progress: int = 0, error: str | None = None) -> None:
        """Convenience method to update progress fields."""
        with self._lock:
            if job_id in self._store:
                self._store[job_id]["status"] = status
                if node:
                    self._store[job_id]["current_node"] = node
                self._store[job_id]["progress_pct"] = progress
                if error is not None:
                    self._store[job_id]["error"] = error

    def list_jobs(self) -> list[str]:
        """Return all job IDs."""
        with self._lock:
            return list(self._store.keys())

    def delete(self, job_id: str) -> None:
        """Remove a job."""
        with self._lock:
            self._store.pop(job_id, None)


job_store = JobStore()
