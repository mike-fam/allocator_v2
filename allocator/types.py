from typing import TypedDict, Dict, List, Optional
from enum import Enum, IntEnum

SessionId = StaffId = WeekId = int

Allocation = Dict[SessionId, List[StaffId]]


class StrEnum(str, Enum):
    pass


class Output(TypedDict):
    status: str
    type: str
    detail: str
    allocations: Allocation
    runtime: int


class SessionType(StrEnum):
    PRACTICAL = "Practical"
    TUTORIAL = "Tutorial"
    SEMINAR = "Seminar"
    LECTURE = "Lecture"
    STUDIO = "Studio"


class IsoDay(IntEnum):
    MON = 1
    TUE = 2
    WED = 3
    THU = 4
    FRI = 5
    SAT = 6
    SUN = 7


class WeekInput(TypedDict):
    id: WeekId
    name: str


class SessionStreamInput(TypedDict):
    id: SessionId
    name: str
    type: SessionType
    start_time: float
    end_time: float
    number_of_tutors: int
    day: IsoDay
    weeks: List[WeekId]


class TimeslotInput(TypedDict):
    start_time: float
    end_time: float


class StaffInput(TypedDict):
    id: StaffId
    name: str
    new: bool
    type_preference: SessionType
    max_contiguous_hours: float
    max_weekly_hours: float
    availabilities: Dict[IsoDay, List[TimeslotInput]]


class InputData(TypedDict):
    weeks: List[WeekInput]
    session_streams: List[SessionStreamInput]
    staff: List[StaffInput]
    new_threshold: Optional[float]


class Input(TypedDict):
    request_time: str
    requester: str
    data: InputData
