"""Dependency injection container for BugBuddy."""

import sys
from importlib.metadata import version
from logging import Formatter, Logger, StreamHandler, getLogger
from typing import Optional

from attrs import define

from bug_buddy._config import BugBuddyConfig
from bug_buddy.integration import Integration
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

    def config(self) -> BugBuddyConfig:
        """Config injection.

        Returns:
            Config instance.
        """

        return BugBuddyConfig()

    def listener(
        self,
        integration: Optional[Integration] = None,
        logger: Optional[Logger] = None,
    ) -> Listener:
        """Listener injection.

        Args:
            integration: Issue tracker integration configuration.
            logger: logger instance.

        Returns:
            Listener instance.
        """

        if not logger:
            config = self.config()
            logger = self.logger(config.log_level)

        return Listener(
            integration=integration,
            logger=logger,
        )
