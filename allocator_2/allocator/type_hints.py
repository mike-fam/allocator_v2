from enum import Enum, IntEnum
from dataclasses import dataclass, field


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


@dataclass
class Output:
    status: str
    type: str
    detail: str
    runtime: int
    allocations: Allocation = field(default_factory=dict)
