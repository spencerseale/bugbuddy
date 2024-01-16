import traceback
from functools import wraps
from typing import Any, Optional

from bug_buddy._di_container import BugBuddyInjector


def bug_buddy(
    runner: Optional[callable] = None,
    project_id: Optional[int] = None,
    gitlab: bool = False,
    github: bool = False,
) -> Any:
    """Decorator for bug_buddy.

    Tag a main/runner function with this decorator to enable bug_buddy.

    Args:
        runner: main/runner function.
        project_id: Remote project ID for Github or Gitlab.
        gitlab: whether to create a GitLab issue if bug detected.
        github: whether to create a GitHub issue if bug detected.

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
            listener = di.listener(project_id, gitlab, github, logger=logger)

            # listener = Listener(project_id, gitlab, github)
            logger.info("listening for " + listener.mascot)

            try:
                actual = runner(*args, **kwargs)
                logger.debug("completed without " + listener.mascot)
                return actual

            except Exception as e:
                # filter traceback for all components
                trace: list[traceback.FrameSummary] = traceback.extract_tb(e.__traceback__)

                remote = di.remote_client(gitlab, github, logger=logger)
                issue = listener.record(trace, exception=type(e), remote=remote)

                detection = listener.mascot + " cached."
                if project_id:
                    remote = "Gitlab" if listener.gitlab else "Github"
                    detection += f" Tracking at {remote} issue {issue.id}."

                logger.info(detection)

                raise e

        return wrapper

    # in cases where no optional args passed to decorator
    if runner:
        return _bug_buddy(runner)
    return _bug_buddy
