"""Dependency injection container for BugBuddy."""

import sys
from logging import Formatter, Logger, StreamHandler

from attrs import define


@define
class BugBuddyInjector:
    def logger(self, log_level: str) -> Logger:
        """Logger"""

        logger = Logger()
        logger.propagate = False  # don't propagate to root logger
        logger.addHandler(StreamHandler(sys.stdout))

        # init format
        lformat = Formatter(
            fmt="%(asctime)s -- %(message)s\n",
            datefmt="%d-%b-%y %H:%M:%S",
        )
        # set the format for the logger
        logger.handlers[0].setFormatter(lformat)
        logger.setLevel(log_level.upper())

        logger.debug("Logger initialized at level %s.", log_level.upper())

        return logger

    def runner(self):
        """Runner"""

        pass
        # return BugBuddyRunner()

    def config(self):
        """Config"""

        pass
        # return BugBuddyConfig()
