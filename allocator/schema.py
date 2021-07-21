from dataclasses import dataclass, field, asdict
from typing import List, Dict

from allocator.type_hints import WeekInput, TimeslotInput, IsoDay, StaffInput, SessionType, SessionStreamInput, WeekId


@dataclass(frozen=True, eq=True)
class Week:
    id: int
    name: str

    @classmethod
    def from_input(cls, week_input: WeekInput) -> 'Week':
        return cls(**week_input)

    def __str__(self):
        return f"Week {self.name}"

    def __repr__(self):
        return str(self)


@dataclass(frozen=True, order=True, eq=True)
class Hour:
    value: float = field(compare=True)

    def in_time_range(self, time_slot: 'Timeslot'):
        return time_slot.start <= self < time_slot.end

    def in_time_ranges(self, *time_slots: 'Timeslot'):
        return any(self.in_time_range(time_slot) for time_slot in time_slots)

    def __sub__(self, other):
        return self.value - other.value

    def __str__(self):
        return f"{self.value}h"

    def __repr__(self):
        return str(self)


@dataclass(frozen=True)
class Timeslot:
    start: Hour
    end: Hour

    def duration(self):
        return self.end - self.start

    def is_contiguous(self, other: 'Timeslot'):
        """Returns True if this time slot is contiguous AFTER the other.
        This function is one way"""
        return self.start == other.end

    def clashes_with(self, other: 'Timeslot'):
        """Returns True if this time slot clashes with the other"""
        return (self.start <= other.start < self.end) or (other.start <= self.start < other.end)

    def __str__(self):
        return f"{self.start}-{self.end}"

    def __repr__(self):
        return str(self)

    @classmethod
    def from_input(cls, timeslot_input: TimeslotInput) -> 'Timeslot':
        return cls(start=Hour(timeslot_input["start_time"]), end=Hour(timeslot_input["end_time"]))


@dataclass
class Staff:
    id: str
    name: str
    new: bool
    type_preference: SessionType = None
    max_contiguous_hours: int = 24
    max_weekly_hours: int = 100
    availabilities: Dict[IsoDay, List['Timeslot']] = field(default_factory=dict,
                                                           init=False)

    def __str__(self):
        return f"Staff {self.name}"

    def __repr__(self):
        return str(self)

    def is_available(self, session_stream: 'SessionStream'):
        """
        Checks if tutor is available to work on session stream
        Args:
            session_stream: session stream to check if this tutor is available on
        Returns: True if this tutor is available on this stream, False otherwise
        """
        availabilities = self.availabilities.get(session_stream.day)
        if availabilities is None:
            return False
        availabilities = sorted(availabilities, key=lambda t: (t.start, t.end))
        start_check = session_stream.time.start
        for time_slot in availabilities:
            if time_slot.start > start_check:
                return False
            if time_slot.start <= start_check < time_slot.end:
                if session_stream.time.end <= time_slot.end:
                    return True
                start_check = time_slot.end
        return False

    @classmethod
    def from_input(cls, staff_input: StaffInput) -> 'Staff':
        instance = cls(**{k: v for k, v in staff_input.items() if k != "availabilities" if v is not None})
        instance.availabilities = {}
        for day, timeslots_input in staff_input["availabilities"].items():
            instance.availabilities[int(day)] = list(map(lambda timeslot_input: Timeslot.from_input(timeslot_input),
                                                         timeslots_input))
        return instance

    @classmethod
    def create_dummy(cls, dummy_id: int) -> 'Staff':
        availabilities = {}
        for day in [IsoDay.MON, IsoDay.THU, IsoDay.WED, IsoDay.THU,
                    IsoDay.FRI]:
            availabilities[day] = [Timeslot(Hour(1), Hour(23))]
        instance = cls(dummy_id, f"Dummy {dummy_id}", False)
        instance.availabilities = availabilities
        return instance


@dataclass(eq=True)
class SessionStream:
    id: str
    name: str
    type: SessionType  # e.g. 'Practical' or 'Tutorial'
    day: IsoDay
    time: Timeslot
    number_of_tutors: int
    weeks: List[WeekId] = field(default_factory=list)

    def __str__(self):
        return f"Session Stream {self.name}"

    def __repr__(self):
        return str(self)

    @classmethod
    def from_input(cls, session_stream_input: SessionStreamInput):
        timeslot = Timeslot(Hour(session_stream_input["start_time"]), Hour(session_stream_input["end_time"]))
        id_ = session_stream_input["id"]
        name = session_stream_input["name"]
        type_ = session_stream_input["type"]
        number_of_tutors = session_stream_input["number_of_tutors"]
        day = session_stream_input["day"]
        weeks = session_stream_input["weeks"]
        return cls(id_, name, type_, day, timeslot, number_of_tutors, weeks)

    def total_hours(self):
        return self.time.duration() * len(self.weeks)