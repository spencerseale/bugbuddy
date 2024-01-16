"""Dependency injection container for BugBuddy."""

import sys
from importlib.metadata import version
from logging import Formatter, Logger, StreamHandler, getLogger
from typing import Optional

from attrs import define

from bug_buddy._config import BugBuddyConfig
from bug_buddy.issue import GitlabIssuesClient
from bug_buddy.listener import Listener


@define
class BugBuddyInjector:
    """Dependency injection container for BugBuddy."""

    def logger(self, log_level: str) -> Logger:
        """Logger injection.

        Args:
            log_level: log level.

        Returns:
            Logger instance.
        """

        logger = getLogger("bug-buddy")
        logger.propagate = False  # don't propagate to root logger
        logger.addHandler(StreamHandler(sys.stdout))

        # init format
        lformat = Formatter(
            fmt="\033[96mbug-buddy\033[0m %(message)s\n",
            datefmt="%d-%b-%y %H:%M:%S",
        )
        # set the format for the logger
        logger.handlers[0].setFormatter(lformat)
        logger.setLevel(log_level.upper())

        logger.debug(
            "\033[93m%s\033[0m logger initialized at level %s."
            % (version("bug-buddy"), log_level.upper())
        )

        return logger

    def runner(self) -> None:
        """Runner injection.

        TODO: implement if CLI is added.
        """

        pass

    def config(self) -> BugBuddyConfig:
        """Config injection.

        Returns:
            Config instance.
        """

        return BugBuddyConfig()

    def remote_client(
        self,
        gitlab: bool = False,
        github: bool = False,
        logger: Optional[Logger] = None,
    ) -> Optional[GitlabIssuesClient]:
        """Git remote issue tracker API injection.

        Args:
            gitlab: whether to use GitLab API.
            github: whether to use GitHub API.
            logger: logger instance.

        Returns:
            Remote API client.
        """

        if not logger:
            config = self.config()
            logger = self.logger(config.log_level)

        if gitlab:
            return GitlabIssuesClient(logger=logger)
        elif github:
            logger.warning("Github not yet supported.")
            return None
        else:
            logger.warning("No remote issue tracker specified.")
            return None

    def listener(
        self,
        project_id: Optional[int] = None,
        gitlab: bool = False,
        github: bool = False,
        logger: Optional[Logger] = None,
    ) -> Listener:
        """Listener injection.

        Args:
            project_id: project ID.
            gitlab: whether to use GitLab API.
            github: whether to use GitHub API.
            logger: logger instance.

        Returns:
            Listener instance.
        """

        if not logger:
            config = self.config()
            logger = self.logger(config.log_level)

        return Listener(
            project_id=project_id,
            gitlab=gitlab,
            github=github,
            logger=logger,
        )
