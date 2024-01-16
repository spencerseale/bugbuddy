"""Dependency injection container for BugBuddy."""

import sys
from importlib.metadata import version
from logging import Formatter, Logger, StreamHandler, getLogger
from typing import Optional

from attrs import define

from bug_buddy.issue import GitlabIssuesApi


@define
class BugBuddyInjector:
    """Dependency injection container for BugBuddy."""

    def logger(self, log_level: str) -> Logger:
        """Logger"""

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

    def runner(self):
        """Runner"""

        pass

    def config(self):
        """Config"""

        pass

    def remote_api(self, gitlab: bool = False, github: bool = False) -> Optional[GitlabIssuesApi]:
        """Git remote issue tracker API."""

        logger = self.logger("DEBUG")

        if gitlab:
            return GitlabIssuesApi()
        elif github:
            logger.warning("Github not yet supported.")
            return None

        else:
            logger.warning("No remote issue tracker specified.")
            return None
