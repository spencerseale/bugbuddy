"""Bug Buddy Config"""


from pydantic.dataclasses import dataclass as pydantic_dataclass


@pydantic_dataclass
class BugBuddyConfig:
    """Bug Buddy Config"""

    log_level: str = "INFO"
