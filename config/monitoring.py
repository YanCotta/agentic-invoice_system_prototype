import time
from config.logging_config import logger
from contextlib import contextmanager

class Monitoring:
    def __init__(self):
        self.timers = {}

    def start_timer(self, module_name: str):
        """Start a timer for a specific module"""
        self.timers[module_name] = time.time()
        logger.debug(f"Started timer for {module_name}")

    def stop_timer(self, module_name: str) -> float:
        """Stop the timer for a module and return the duration"""
        if module_name in self.timers:
            duration = time.time() - self.timers[module_name]
            logger.info(f"{module_name} took {duration:.2f} seconds")
            del self.timers[module_name]
            return duration
        else:
            logger.warning(f"No start time recorded for {module_name}")
            return 0.0

    @contextmanager
    def timer(self, module_name: str):
        """Context manager for timing a block of code"""
        try:
            self.start_timer(module_name)
            yield
        finally:
            duration = self.stop_timer(module_name)
            return duration