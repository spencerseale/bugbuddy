"""Listener for Bug Buddy."""

import os
import platform
import re
import traceback
from datetime import datetime, timezone
from logging import Logger, getLogger
from typing import TYPE_CHECKING, Optional, Sequence

from attrs import define, field

from bug_buddy.issue import Issue

if TYPE_CHECKING:
    from bug_buddy.integration import Integration

# Environment variables to check for CI/execution context
_CI_ENV_VARS = [
    # GitHub Actions
    ("GITHUB_ACTIONS", "GitHub Actions"),
    ("GITHUB_RUN_ID", "Run ID"),
    ("GITHUB_RUN_URL", "Run URL"),
    ("GITHUB_REPOSITORY", "Repository"),
    ("GITHUB_REF_NAME", "Branch/Tag"),
    ("GITHUB_SHA", "Commit SHA"),
    ("GITHUB_ACTOR", "Triggered by"),
    # GitLab CI
    ("GITLAB_CI", "GitLab CI"),
    ("CI_JOB_ID", "Job ID"),
    ("CI_JOB_URL", "Job URL"),
    ("CI_PROJECT_PATH", "Project"),
    ("CI_COMMIT_REF_NAME", "Branch/Tag"),
    ("CI_COMMIT_SHA", "Commit SHA"),
]


@define
class Listener:
    """Listener for Bug Buddy."""

    integration: Optional["Integration"] = None
    """Issue tracker integration configuration."""
    logger: Logger = field()
    """Logger instance."""

    @logger.default
    def _logger_default(self) -> Logger:
        return getLogger(__name__)

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

        # Files that are part of bug_buddy internals
        bug_buddy_files = {"listener.py", "bb.py", "_di_container.py"}

        filtered_tb = []
        for t in tb:
            if os.path.basename(t.filename) not in bug_buddy_files:
                filtered_tb.append(t)

        return filtered_tb

    def _get_execution_context(self) -> list[tuple[str, str]]:
        """Gather execution context information.

        Returns:
            List of (label, value) tuples for context info.
        """
        context = []

        # Timestamp
        context.append(("Timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")))

        # Machine info
        context.append(("Platform", platform.platform()))
        context.append(("Python", platform.python_version()))

        # Working directory
        context.append(("Working Directory", os.getcwd()))

        # User (if available)
        user = os.environ.get("USER") or os.environ.get("USERNAME")
        if user:
            context.append(("User", user))

        # CI/environment context
        ci_context = []
        for env_var, label in _CI_ENV_VARS:
            value = os.environ.get(env_var)
            if value:
                ci_context.append((label, value))

        if ci_context:
            context.extend(ci_context)

        return context

    def description(
        self,
        tb: Sequence[traceback.FrameSummary],
        func_name: str,
        func_source: Optional[str] = None,
    ) -> str:
        """Format the description of the issue.

        Upload traceback as a table.

        Also upload raw traceback as a collapsible.

        Args:
            tb: traceback.
            func_name: name of the decorated function.
            func_source: source code of the decorated function.

        Returns:
            Formatted description.
        """

        rows = []

        # Function source code
        rows.append("### Origin")
        rows.append("```python")
        if func_source:
            rows.append(func_source.rstrip())
        else:
            rows.append(func_name)
        rows.append("```")
        rows.append("")

        # Source/execution context
        rows.append("### Platform")
        rows.append("| Property | Value |")
        rows.append("| --- | --- |")
        for label, value in self._get_execution_context():
            rows.append(f"| {label} | `{value}` |")
        rows.append("")

        # Traceback table
        rows.append("### Traceback")
        rows.append("| File | Callable | Line | Code |")
        rows.append("| --- | --- | --- | --- |")
        for t in tb:
            esc_callable = re.sub("_", r"\_", t.name)
            rows.append(f"| {t.filename} | {esc_callable} | {t.lineno} | {t.line} |")

        # Raw traceback
        rows.append("")
        rows.append("### Raw traceback")
        rows.append("```")
        rows.append(traceback.format_exc())
        rows.append("```")

        return "\n".join(rows)

    def record(
        self,
        tb: Sequence[traceback.FrameSummary],
        exception: type,
        func_name: str,
        func_source: Optional[str] = None,
    ) -> Issue:
        """Record the traceback.

        Args:
            tb: traceback.
            exception: exception type.
            func_name: name of the decorated function.
            func_source: source code of the decorated function.

        Returns:
            Issue metadata.
        """

        # filter and format traceback for issue description
        filtered_tb = self.filter_tb(tb)
        desc = self.description(filtered_tb, func_name, func_source)

        if self.integration:
            client = self.integration.get_client(self.logger)
            issue = self.integration.create_issue(
                client=client,
                description=desc,
                labels=[exception.__name__],
                func_name=func_name,
            )
        else:
            # Create a local-only issue when no integration is configured
            import uuid
            from datetime import datetime

            issue = Issue(
                id=0,
                title=f"BugBuddy-{func_name}-" + str(uuid.uuid4()),
                state="local",
                project_id=0,
                author=("local", "local", "active"),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                description=desc,
                labels=[exception.__name__],
            )

        # cache issues to a local archive
        issue.cache()

        return issue
