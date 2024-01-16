"""Listener for Bug Buddy."""

import os
import re
import traceback
from logging import Logger, getLogger
from typing import Sequence

from attrs import define, field

from bug_buddy.issue import GitlabIssuesClient, Issue


@define
class Listener:
    """Listener for Bug Buddy."""

    project_id: field(converter=int, default=None)
    """Remote project ID for Github or Gitlab."""
    gitlab: bool = False
    """Whether to create a GitLab issue if bug detected."""
    github: bool = False
    """Whether to create a GitHub issue if bug detected."""
    logger: Logger = field()
    """Logger instance."""

    @logger.default
    def _logger_default(self) -> Logger:
        return getLogger(__name__)

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

    def record(
        self, tb: Sequence[traceback.FrameSummary], exception: type, remote: GitlabIssuesClient
    ) -> Issue:
        """Record the traceback.

        Args:
            tb: traceback.
            exception: exception.
            remote: remote issue tracker API client.

        Returns:
            Issue metadata.
        """

        # filter and format traceback for issue description
        filtered_tb = self.filter_tb(tb)
        desc = self.description(filtered_tb)

        issue = remote.create_issue(
            project_id=self.project_id,
            description=desc,
            labels=[exception.__name__],
        )
        # cache issues to a local archive
        issue.cache()

        return issue
