"""
Progress tracking utilities for CLI operations.
"""
import time

class ProgressTracker:
    """Simple progress tracking for CLI operations."""
    def __init__(self, total: int = 0, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.last_update = self.start_time
        self.finished = False

    def update(self, n: int = 1, message: str = None):
        """Update progress and optionally display it."""
        self.current += n
        self.last_update = time.time()
        self._display_progress(message)

    def _display_progress(self, message: str = None):
        """Display current progress."""
        if self.total > 0:
            percentage = 100 * self.current / self.total
            elapsed = time.time() - self.start_time
            eta = (elapsed / self.current) * (self.total - self.current) if self.current else 0
            eta_str = f"ETA: {int(eta)}s" if self.current else ""
            progress_bar = self._create_progress_bar(percentage)
            status = f"{self.description}: {progress_bar} {percentage:.1f}% ({self.current}/{self.total}) {eta_str}"
        else:
            # Indeterminate progress
            status = f"{self.description}: {self.current} completed"
        if message:
            status += f" | {message}"
        print(status, end="\r", flush=True)

    def _create_progress_bar(self, percentage: float, width: int = 20) -> str:
        """Create a simple text progress bar."""
        filled = int(width * percentage // 100)
        return f"[{'=' * filled}{' ' * (width - filled)}]"

    def finish(self, message: str = None):
        """Finish progress tracking."""
        self.finished = True
        self._display_progress(message)
        print()

def create_progress_tracker(total: int = 0, description: str = "Processing") -> ProgressTracker:
    """Create a progress tracker instance."""
    return ProgressTracker(total, description) 