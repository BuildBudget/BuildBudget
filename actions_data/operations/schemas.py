from enum import Enum


class OperationResult(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    NOOP = "noop"
    IN_PROGRESS = "in_progress"
