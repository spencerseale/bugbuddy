"""Integration configurations for Bug Buddy."""

from abc import ABC, abstractmethod
from logging import Logger
from typing import Union

from pydantic.dataclasses import dataclass as pydantic_dataclass

from bug_buddy.issue import GitlabIssuesClient, Issue, LinearIssuesClient


@pydantic_dataclass
class Integration(ABC):
    """Base class for issue tracker integrations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the integration."""
        ...

    @abstractmethod
    def get_client(self, logger: Logger) -> Union[GitlabIssuesClient, LinearIssuesClient]:
        """Get the API client for this integration.

        Args:
            logger: Logger instance.

        Returns:
            API client instance.
        """
        ...

    @abstractmethod
    def create_issue(
        self,
        client: Union[GitlabIssuesClient, LinearIssuesClient],
        description: str,
        labels: list[str],
        func_name: str,
    ) -> Issue:
        """Create an issue using the integration's client.

        Args:
            client: API client instance.
            description: Issue description.
            labels: Issue labels.
            func_name: Name of the decorated function.

        Returns:
            Created issue.
        """
        ...


@pydantic_dataclass
class GitlabIntegration(Integration):
    """GitLab integration configuration."""

    project_id: int
    """GitLab project ID."""

    @property
    def name(self) -> str:
        """Name of the integration."""
        return "GitLab"

    def get_client(self, logger: Logger) -> GitlabIssuesClient:
        """Get the GitLab API client.

        Args:
            logger: Logger instance.

        Returns:
            GitLab API client instance.
        """
        return GitlabIssuesClient(logger=logger)

    def create_issue(
        self,
        client: GitlabIssuesClient,
        description: str,
        labels: list[str],
        func_name: str,
    ) -> Issue:
        """Create a GitLab issue.

        Args:
            client: GitLab API client instance.
            description: Issue description.
            labels: Issue labels.
            func_name: Name of the decorated function.

        Returns:
            Created issue.
        """
        return client.create_issue(
            project_id=self.project_id,
            description=description,
            labels=labels,
            func_name=func_name,
        )


@pydantic_dataclass
class GithubIntegration(Integration):
    """GitHub integration configuration."""

    repo: str
    """GitHub repository in 'owner/repo' format."""

    @property
    def name(self) -> str:
        """Name of the integration."""
        return "GitHub"

    def get_client(self, logger: Logger) -> None:
        """Get the GitHub API client.

        Args:
            logger: Logger instance.

        Returns:
            GitHub API client instance.
        """
        logger.warning("GitHub integration not yet implemented.")
        return None

    def create_issue(
        self,
        client,
        description: str,
        labels: list[str],
        func_name: str,
    ) -> Issue:
        """Create a GitHub issue.

        Args:
            client: GitHub API client instance.
            description: Issue description.
            labels: Issue labels.
            func_name: Name of the decorated function.

        Returns:
            Created issue.
        """
        raise NotImplementedError("GitHub integration not yet implemented.")


@pydantic_dataclass
class LinearIntegration(Integration):
    """Linear integration configuration."""

    team_id: str
    """Linear team ID."""

    project_id: str | None = None
    """Linear project ID (optional)."""

    @property
    def name(self) -> str:
        """Name of the integration."""
        return "Linear"

    def get_client(self, logger: Logger) -> LinearIssuesClient:
        """Get the Linear API client.

        Args:
            logger: Logger instance.

        Returns:
            Linear API client instance.
        """
        return LinearIssuesClient(logger=logger)

    def create_issue(
        self,
        client: LinearIssuesClient,
        description: str,
        labels: list[str],
        func_name: str,
    ) -> Issue:
        """Create a Linear issue.

        Args:
            client: Linear API client instance.
            description: Issue description.
            labels: Issue labels (ignored, uses "Bug" label from Linear).
            func_name: Name of the decorated function.

        Returns:
            Created issue.
        """
        # Linear uses the "Bug" label by default (looked up by name)
        # The labels param from caller contains exception names which aren't useful here
        return client.create_issue(
            team_id=self.team_id,
            description=description,
            func_name=func_name,
            project_id=self.project_id,
        )
