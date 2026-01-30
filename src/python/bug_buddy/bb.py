import inspect
import traceback
from functools import wraps
from typing import Any, Optional

from bug_buddy._di_container import BugBuddyInjector
from bug_buddy.integration import Integration


def bug_buddy(
    runner: Optional[callable] = None,
    integration: Optional[Integration] = None,
) -> Any:
    """Decorator for bug_buddy.

    Tag a main/runner function with this decorator to enable bug_buddy.

    Args:
        runner: main/runner function.
        integration: Issue tracker integration configuration (GitlabIntegration,
            GithubIntegration, or LinearIntegration).

    Returns:
        Decorated function's return value.
    """

    def _bug_buddy(runner: callable) -> callable:
        @wraps(runner)
        def wrapper(*args, **kwargs) -> any:
            """Main/runner executed here."""

            # init dependency injection container
            di = BugBuddyInjector()
            # inject dependencies
            config = di.config()
            logger = di.logger(config.log_level)
            listener = di.listener(integration=integration, logger=logger)

            logger.info("listening for " + listener.mascot)

            try:
                actual = runner(*args, **kwargs)
                logger.debug("completed without " + listener.mascot)
                return actual

            except Exception as e:
                # filter traceback for all components
                trace: list[traceback.FrameSummary] = traceback.extract_tb(e.__traceback__)

                # get source code of decorated function
                try:
                    func_source = inspect.getsource(runner)
                except (OSError, TypeError):
                    func_source = None

                issue = listener.record(
                    trace,
                    exception=type(e),
                    func_name=runner.__name__,
                    func_source=func_source,
                )

                detection = listener.mascot + " cached."
                if integration:
                    detection += f" Tracking at {integration.name} issue {issue.id}."

                logger.info(detection)

                raise e

        return wrapper

    # in cases where no optional args passed to decorator
    if runner:
        return _bug_buddy(runner)
    return _bug_buddy
