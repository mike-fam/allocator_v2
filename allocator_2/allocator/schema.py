from dataclasses import dataclass, field
from typing import List, Optional

from allocator.type_hints import (
    IsoDay,
    SessionType,
    WeekId,
)


@dataclass(frozen=True, eq=True)
class Week:
    id: int
    name: str

    def __str__(self):
        return f"Week {self.name}"

    def __repr__(self):
        return str(self)


@dataclass(frozen=True, order=True, eq=True)
class Hour:
    value: float = field(compare=True)

    def in_time_range(self, time_slot: "Timeslot"):
        return time_slot.start_time <= self < time_slot.end_time

    def in_time_ranges(self, *time_slots: "Timeslot"):
        return any(self.in_time_range(time_slot) for time_slot in time_slots)

    def __sub__(self, other):
        return self.value - other.value

    def __str__(self):
        return f"{self.value}h"

    def __repr__(self):
        return str(self)


@dataclass
class Timeslot:
    start_time: Hour
    end_time: Hour

    def duration(self):
        return self.end_time - self.start_time

    def is_contiguous(self, other: "Timeslot"):
        """Returns True if this time slot is contiguous AFTER the other.
        This function is one way"""
        return self.start_time == other.end_time

    def clashes_with(self, other: "Timeslot"):
        """Returns True if this time slot clashes with the other"""
        return (self.start_time <= other.start_time < self.end_time) or (
            other.start_time <= self.start_time < other.end_time
        )

    def __str__(self):
        return f"{self.start_time}-{self.end_time}"

    def __repr__(self):
        return str(self)

    def __post_init__(self):
        self.start_time = Hour(self.start_time)  # type: ignore
        self.end_time = Hour(self.end_time)  # type: ignore


@dataclass
class Staff:
    id: str
    name: str
    new: bool
    availabilities: dict[IsoDay, list["Timeslot"]]
    type_preference: SessionType = None
    max_contiguous_hours: float = 24
    max_weekly_hours: float = 100

    def __str__(self):
        return f"Staff {self.name}"

    def __repr__(self):
        return str(self)

    def is_available(self, session_stream: "SessionStream"):
        """
        Checks if tutor is available to work on session stream
        Args:
            session_stream: session stream to check if this tutor is available on
        Returns: True if this tutor is available on this stream, False otherwise
        """
        availabilities = self.availabilities.get(session_stream.day)
        if availabilities is None:
            return False
        availabilities = sorted(
            availabilities, key=lambda t: (t.start_time, t.end_time)
        )
        start_check = session_stream.time.start_time
        for time_slot in availabilities:
            if time_slot.start_time > start_check:
                return False
            if time_slot.start_time <= start_check < time_slot.end_time:
                if session_stream.time.end_time <= time_slot.end_time:
                    return True
                start_check = time_slot.end_time
        return False

    def __post_init__(self):
        self.availabilities = {
            day: Timeslot(**timeslot)  # type: ignore
            for day, timeslot in self.availabilities.items()
        }

    @classmethod
    def create_dummy(cls, dummy_id: int) -> "Staff":
        availabilities = {}
        for day in [IsoDay.MON, IsoDay.THU, IsoDay.WED, IsoDay.THU, IsoDay.FRI]:
            availabilities[day] = [Timeslot(Hour(1), Hour(23))]
        instance = cls(str(dummy_id), f"Dummy {dummy_id}", False)
        instance.availabilities = availabilities
        return instance


@dataclass(eq=True)
class SessionStream:
    id: str
    name: str
    type: SessionType  # e.g. 'Practical' or 'Tutorial'
    day: IsoDay
    number_of_tutors: int
    time: Timeslot = None
    weeks: List[WeekId] = field(default_factory=list)

    def __str__(self):
        return f"Session Stream {self.name}"

    def __repr__(self):
        return str(self)

    def __post_init__(self):
        self.timeslot = Timeslot(*self.timeslot)  # type: ignore

    def total_hours(self):
        return self.time.duration() * len(self.weeks)


@dataclass
class InputData:
    timetable_id: str
    weeks: list[Week]
    session_streams: list[SessionStream]
    staff: list["Staff"]
    new_threshold: Optional[float] = None
    timeout: int = 3600

    def __post_init__(self):
        self.weeks = [Week(**week) for week in self.weeks]  # type: ignore
        self.session_streams = [
            SessionStream(**stream)  # type: ignore
            for stream in self.session_streams
        ]
        print(self.staff)
        self.staff = [Staff(**staff) for staff in self.staff]  # type: ignore


@dataclass
class Input:
    request_time: str
    requester: str
    data: InputData

    def __post_init__(self):
        self.data = InputData(**self.data)  # type: ignore
