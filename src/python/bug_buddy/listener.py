"""Listener for Bug Buddy."""

import os
import re
import traceback
from functools import wraps
from logging import Logger
from typing import Any, Optional, Sequence

from attrs import define, field

from bug_buddy._di_container import BugBuddyInjector
from bug_buddy.issue import Issue


@define
class Listener:
    """Listener for Bug Buddy."""

    project_id: field(converter=int, default=None)
    """Remote project ID for Github or Gitlab."""
    gitlab: bool = False
    """Whether to create a GitLab issue if bug detected."""
    github: bool = False
    """Whether to create a GitHub issue if bug detected."""
    container: BugBuddyInjector = BugBuddyInjector()
    """Dependency injection container for BugBuddy."""

    logger: Logger = field()
    """Logger instance."""

    @logger.default
    def _logger_default(self) -> Logger:
        return self.container.logger("DEBUG")

    def __attrs_post_init__(self) -> None:
        if self.project_id and not (self.gitlab or self.github):
            raise ValueError("Must specify gitlab or github if project_id specified.")

    @property
    def mascot(self):
        """Buzzzzz"""
        return "\U0001F41D"

    def filter_tb(self, tb: Sequence[traceback.FrameSummary]) -> list[traceback.FrameSummary]:
        """Filter traceback to remove bug-buddy references.

        Args:
            tb: traceback.

        Returns:
            Filtered traceback.
        """

        filtered_tb = []
        for t in tb[::-1]:
            if os.path.basename(t.filename) == os.path.basename(__file__):
                break
            else:
                filtered_tb.append(t)

        return filtered_tb[::-1]

    def description(self, tb: Sequence[traceback.FrameSummary]) -> str:
        """Format the description of the issue.

        Upload traceback as a table.

        Also upload raw traceback as a collapsible.

        Args:
            tb: traceback.

        Returns:
            Formatted description.
        """

        rows = [
            "### Traceback",
            "| File | Callable | Line | Code |",
            "| --- | --- | --- | --- |",
        ]
        for t in tb:
            esc_callable = re.sub("_", "\_", t.name)
            rows.append(f"| {t.filename} | {esc_callable} | {t.lineno} | {t.line} |")

        # add raw
        rows.append("\n<details><summary>Raw traceback</summary>")
        rows.append(traceback.format_exc())
        rows.append("</details>")

        return "\n".join(rows)

    def record(self, tb: Sequence[traceback.FrameSummary], exception: type) -> Issue:
        """Record the traceback.

        Args:
            tb: traceback.
            exception: exception.

        Returns:
            Issue metadata.
        """

        filtered_tb = self.filter_tb(tb)
        desc = self.description(filtered_tb)

        remoteapi = self.container.remote_api(gitlab=self.gitlab, github=self.github)
        issue = remoteapi.create_issue(
            project_id=self.project_id,
            description=desc,
            labels=[exception.__name__],
        )
        # cache issues to a local archive
        issue.cache()

        return issue


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

            listener = Listener(project_id, gitlab, github)
            listener.logger.info("listening for " + listener.mascot)

            try:
                actual = runner(*args, **kwargs)
                listener.logger.debug("completed without " + listener.mascot)
                return actual

            except Exception as e:
                # filter traceback for all components
                trace: list[traceback.FrameSummary] = traceback.extract_tb(e.__traceback__)

                issue = listener.record(trace, exception=type(e))

                detection = listener.mascot + " cached."
                if project_id:
                    remote = "Gitlab" if listener.gitlab else "Github"
                    detection += f" Tracking at {remote} issue {issue.id}."

                listener.logger.info(detection)

                raise e

        return wrapper

    # in cases where no optional args passed to decorator
    if runner:
        return _bug_buddy(runner)
    return _bug_buddy
