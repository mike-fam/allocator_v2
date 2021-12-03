from dataclasses import dataclass, field
from enum import Enum, IntEnum


SessionId = StaffId = str

WeekId = int

Allocation = dict[SessionId, list[StaffId]]


class StrEnum(str, Enum):
    pass


class SessionType(StrEnum):
    PRACTICAL = "Practical"
    TUTORIAL = "Tutorial"
    SEMINAR = "Seminar"
    LECTURE = "Lecture"
    STUDIO = "Studio"
    CONTACT = "Contact"
    WORKSHOP = "Workshop"


class IsoDay(IntEnum):
    MON = 1
    TUE = 2
    WED = 3
    THU = 4
    FRI = 5
    SAT = 6
    SUN = 7


class AllocationStatus(StrEnum):
    REQUESTED = "REQUESTED"
    NOT_READY = "NOT_READY"
    NOT_EXIST = "NOT_EXIST"
    ERROR = "ERROR"
    GENERATED = "GENERATED"
    FAILED = "FAILED"


@dataclass
class AllocationOutput:
    title: str
    type: AllocationStatus
    message: str
    runtime: int
    result: dict = field(default_factory=dict)
