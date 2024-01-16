"""Bug Buddy Entrypoint"""


from attrs import define

from bug_buddy._di_container import BugBuddyInjector


@define
class BugBuddyEntrypoint:
    """Bug Buddy Entrypoint"""

    @staticmethod
    def main():
        """Main entrypoint"""

        di = BugBuddyInjector()
        config = di.config()

        di.logger(config.log_level)

        di.runner()
