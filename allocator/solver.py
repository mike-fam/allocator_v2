import time
from itertools import product

from gurobipy.gurobipy import GRB, quicksum, Model, abs_, max_

from .schema import *

# Used for preference constraint. E.g. 0.8 means, if a tutor's preference is
# practical sessions, they'll get AT LEAST 4 hours of practicals for every hour
# of any other session. Higher values may lead to infeasibility, value must be
# > 1/types_num for preferencing to work, where types_num is the number of
# session types (e.g. 2 if session types include Prac and Tute)
from .types import SessionId, StaffId

DEFAULT_PREFERENCE_THRESHOLD = {
    SessionType.PRACTICAL: 0,
    SessionType.TUTORIAL: 0
}

# Used for seniority constraint. Generally new staff should get fewer hours
# than senior staff. # A value of 0.5 means every new staff should get AROUND
# half the number of hours compared to a senior tutor. Value must be >= 0 and
# <= 1.
DEFAULT_NEW_THRESHOLD = 1


def lazy_constraints(vars_dict, *constraints):
    def callback(model, where):
        if where == GRB.Callback.MIPSOL:
            solution = {k: v for (k, v) in zip(vars_dict.keys(),
                                               model.cbGetSolution(
                                                   list(vars_dict.values())))}
            for constraint in constraints:
                constraint(model, vars_dict, solution)

    return callback


class Solver:
    #  (dis)preferred day
    def __init__(self, tutors: List[Staff],
                 session_streams: List[SessionStream],
                 weeks: List[Week],
                 new_threshold: float = None,
                 preference_threshold=None):

        self._tutors: Dict[str, Staff] = {tutor.id: tutor for tutor in tutors}
        self._session_streams: Dict[str, SessionStream] = {
            session_stream.id: session_stream for
            session_stream in session_streams}
        self._weeks: Dict[int, Week] = {week.id: week for week in weeks}
        self._week_sessions: Dict[int, List[SessionStream]] = {}
        for session_stream in session_streams:
            for week in session_stream.weeks:
                if week not in self._week_sessions:
                    self._week_sessions[week] = []
                self._week_sessions[week].append(session_stream)

        if new_threshold is None:
            new_threshold = DEFAULT_NEW_THRESHOLD
        self._new_threshold = new_threshold

        if preference_threshold is None:
            preference_threshold = DEFAULT_PREFERENCE_THRESHOLD
        self._preference_threshold = preference_threshold

        self._model = Model()
        self._model.setParam("LazyConstraints", 1)
        self._model.setParam("TimeLimit", 1800)  # Run for at most 30 minutes
        self._model.setParam("NonConvex", 2)  # For quadratic variance
        # self._model.Params.LogToConsole = 0

        self._allocation_var = {}
        self._tutor_on_day_var = {}

        self._clashing_session_data = {}

        self._days = [IsoDay.MON, IsoDay.TUE, IsoDay.WED, IsoDay.THU,
                      IsoDay.FRI]
        self._max_weekly_hours_constraint = {}
        self._results: Dict[SessionId, List[StaffId]] = {
            session_stream_id: []
            for session_stream_id in self._session_streams
        }
        print("starting timer")
        self._start_time = time.time()

    def add_tutors(self, *tutors: Staff):
        self._tutors.update((tutor.id, tutor) for tutor in tutors)

    def add_session_streams(self, *session_streams: SessionStream):
        self._session_streams.update((session_stream.id, session_stream)
                                     for session_stream in session_streams)

    def add_weeks(self, *weeks: Week):
        self._weeks.update((week.id, week) for week in weeks)

    def change_new_threshold(self, new_threshold: float):
        self._new_threshold = new_threshold

    def _setup_variables(self):
        self._setup_allocation_var()
        self._setup_tutor_on_day_var()
        print("Finish setting up vars after", time.time() - self._start_time)

    def _setup_data(self):
        self._setup_clashing_session_data()
        print("Finish setting up data after", time.time() - self._start_time)

    def _setup_constraints(self):
        self._setup_allocation_collision_constraint()
        self._setup_number_of_tutors_constraint()
        self._setup_tutor_on_day_constraint()
        self._setup_tutor_availability_constraint()
        # self._setup_seniority_for_session_constraint()
        self._setup_maximum_weekly_hours_constraint()
        self._setup_preference_hour_constraint()

    def _setup_allocation_var(self):
        self._allocation_var = {
            (tutor_id, session_stream_id): self._model.addVar(vtype=GRB.BINARY)
            for tutor_id in self._tutors
            for session_stream_id in self._session_streams
        }

    def _setup_tutor_on_day_var(self):
        self._tutor_on_day_var = {
            (tutor_id, day_id, week): self._model.addVar(vtype=GRB.BINARY)
            for tutor_id in self._tutors
            for day_id in self._days
            for week in self._weeks
        }

    def _setup_clashing_session_data(self):
        """Set up session data dictionary, 1 if session runs at a time,
        0 otherwise"""
        self._clashing_session_data = {
            (stream_a_id, stream_b_id): int(
                stream_a.time.clashes_with(stream_b.time) and
                len(set(stream_a.weeks) & set(stream_b.weeks)) > 0
                and stream_a.day == stream_b.day
            )
            for (stream_a_id, stream_a), (stream_b_id, stream_b)
            in product(self._session_streams.items(), repeat=2)
        }

    def _setup_tutor_on_day_constraint(self):
        self._model.addConstrs(
            self._tutor_on_day_var[tutor_id,
                                   self._session_streams[stream_id].day,
                                   week]
            >= self._allocation_var[tutor_id, stream_id]
            * int(week in self._session_streams[stream_id].weeks)
            for stream_id in self._session_streams
            for tutor_id in self._tutors
            for week in self._weeks)

    def _setup_seniority_for_session_constraint(self):
        """Each session has to have a least 1 senior tutor if possible"""
        for session_stream_id, session_stream in self._session_streams.items():
            self._model.addConstr(
                (session_stream.number_of_tutors - 1)
                * quicksum(self._allocation_var[tutor_id, session_stream_id]
                           * (1 - int(tutor.new))
                           for tutor_id, tutor in self._tutors.items())
                >= quicksum(
                    self._allocation_var[tutor_id, session_stream_id]
                    * int(tutor.new)
                    for tutor_id, tutor in self._tutors.items())
            )

    def _setup_tutor_availability_constraint(self):
        """staff can only work when they're available"""
        for tutor_id, tutor in self._tutors.items():
            for stream_id, session_stream in self._session_streams.items():
                self._model.addConstr(
                    self._allocation_var[tutor_id, stream_id] <=
                    int(tutor.is_available(session_stream))
                )

    def _setup_allocation_collision_constraint(self):
        """tutor must work on at most one session per time slot,
        i.e. no collision"""
        for (stream_a_id, stream_a), (stream_b_id, stream_b) in product(
                self._session_streams.items(), repeat=2):
            if stream_a == stream_b or \
                    self._clashing_session_data[stream_a_id, stream_b_id] == 0:
                continue
            for tutor_id in self._tutors:
                self._model.addConstr(
                    self._allocation_var[tutor_id, stream_a_id] +
                    self._allocation_var[tutor_id, stream_b_id] <= 1
                )

    def _setup_number_of_tutors_constraint(self):
        """
        Each session stream should be allocated exactly the number of staff that
        stream requires.
        """
        for session_stream_id, session_stream in self._session_streams.items():
            self._model.addConstr(
                quicksum(self._allocation_var[tutor_id, session_stream_id]
                         for tutor_id in self._tutors)
                <= session_stream.number_of_tutors
            )

    def _setup_preference_hour_constraint(self):
        """Tutors should work more in their preferred session type"""
        # sum preference hours >= self._preference_threshold * sum all hours
        for tutor_id, tutor in self._tutors.items():
            if tutor.type_preference is None:
                continue
            self._model.addConstr(
                quicksum(self._allocation_var[tutor_id, session_stream_id]
                         for session_stream_id, session_stream in
                         self._session_streams.items()
                         if tutor.type_preference == session_stream.type) >=
                self._preference_threshold[tutor.type_preference] *
                quicksum(self._allocation_var[tutor_id, session_stream_id]
                         for session_stream_id in self._session_streams)
            )

    def _setup_contiguous_hours_constraint(self, model, allocation_vars,
                                           allocation_solution):
        """Staff must not work consecutively longer than their maximum
        contiguous hours constraint"""
        for tutor_id, tutor in self._tutors.items():
            allocated_streams = [stream_id
                                 for (tutor_id_, stream_id), value in
                                 allocation_solution.items()
                                 if tutor_id == tutor_id_ and value > 0.99]
            allocated_streams.sort(
                key=lambda stream_id: (
                    self._session_streams[stream_id].time.start,
                    self._session_streams[stream_id].time.end)
            )
            if len(allocated_streams) == 0:
                continue
            streams_to_check = [(0, allocated_streams[0])]
            while len(streams_to_check) != 0:
                first_stream_index, first_stream_id = streams_to_check.pop(0)
                first_stream = self._session_streams[first_stream_id]
                current_contiguous_hours = first_stream.time.duration()

                if current_contiguous_hours > tutor.max_contiguous_hours:
                    model.cbLazy(
                        allocation_vars[tutor_id, first_stream_id] == 0)

                violation_found = False

                # All ids of currently found contiguous sessions
                contiguous_ids = [self._session_streams[first_stream_id].id]

                for stream_index, stream_id in enumerate(
                        allocated_streams[first_stream_index + 1:],
                        start=first_stream_index + 1):

                    stream = self._session_streams[stream_id]
                    current_stream = self._session_streams[contiguous_ids[-1]]

                    # Immediately move on if there's a gap
                    # Not really needed for logic, but for optimisation
                    if stream.time.start > current_stream.time.end:
                        streams_to_check.append((stream_index, stream_id))
                        break

                    # Found contiguous stream
                    if stream.time.is_contiguous(current_stream.time) and \
                            len(set(stream.weeks) & set(
                                current_stream.weeks)) > 0 and \
                            stream.day == current_stream.day:
                        contiguous_ids.append(stream.id)
                        current_contiguous_hours += stream.time.duration()

                        if current_contiguous_hours > tutor.max_contiguous_hours:
                            violation_found = True
                            break

                    # stream not contiguous
                    else:
                        streams_to_check.append((stream_index, stream_id))

                if violation_found:
                    model.cbLazy(quicksum(
                        allocation_vars[tutor_id, stream_id] for stream_id in
                        contiguous_ids) <= len(contiguous_ids) - 1)

    def _setup_maximum_weekly_hours_constraint(self):
        """Staff must not work more than their maximum weekly hours per week"""
        for tutor_id, tutor in self._tutors.items():
            for week, streams in self._week_sessions.items():
                self._model.addConstr(
                    quicksum(self._allocation_var[tutor_id, stream.id]
                             * stream.time.duration()
                             for stream in streams)
                    <= tutor.max_weekly_hours
                )
            # self._model.addConstr(
            #     quicksum(self._allocation_var[tutor_id, session_stream_id] *
            #              session_stream.time.duration()
            #              for session_stream_id, session_stream in
            #              self._session_streams.items()) <=
            #     tutor.max_weekly_hours
            # )

    def _setup_objective(self):
        """
        We want to minimize the variance, so people will have maximum spread.
        Weights for new staff will be accounted here.
        """
        # dict containing total number of allocated hours of every tutor
        total_hours = {
            tutor_id:
                quicksum(
                    self._allocation_var[tutor_id, session_stream_id] *
                    session_stream.time.duration() *
                    len(session_stream.weeks)
                    / (self._new_threshold if tutor.new else 1)
                    # account for seniority
                    for session_stream_id, session_stream in
                    self._session_streams.items()
                )
            for tutor_id, tutor in self._tutors.items()
        }
        # mean of number of allocated hours for every tutor
        mean_hours = sum(
            session_stream.time.duration() *
            session_stream.number_of_tutors *
            len(session_stream.weeks)
            for session_stream in self._session_streams.values()
        ) / len(self._tutors)

        # Difference between allocated hours and mean hours for every tutor
        differences = {tutor_id: self._model.addVar(lb=-GRB.INFINITY) for
                       tutor_id in self._tutors}

        # Absolute variance between allocated hours and mean hours
        variance = {tutor_id: self._model.addVar() for tutor_id in
                    self._tutors}

        # Link difference and absolute variances
        for tutor_id in self._tutors:
            self._model.addConstr(
                total_hours[tutor_id] - differences[tutor_id] == mean_hours)
            self._model.addConstr(
                variance[tutor_id] == differences[tutor_id] * differences[tutor_id])

        self._model.ModelSense = GRB.MINIMIZE

        # minimize amount of unallocated hours
        unallocated_hours = quicksum(
            stream.number_of_tutors * stream.total_hours() -
            quicksum(self._allocation_var[tutor_id, stream.id]
                     for tutor_id in self._tutors) * stream.total_hours()
            for stream in self._session_streams.values()
        )
        self._model.setObjectiveN(unallocated_hours, 0, priority=2, weight=2)

        # Minimize absolute variances between tutors
        spread = quicksum(
            variance[tutor_id] for tutor_id in self._tutors)
        self._model.setObjectiveN(spread, 1, priority=1)

        # Minimize number of days tutors have to go to work
        self._model.setObjectiveN(
            quicksum(self._tutor_on_day_var[tutor_id, day_id, week]
                     for tutor_id in self._tutors
                     for day_id in self._days
                     for week in self._weeks),
            2, priority=0)

    def solve(self, output_log_file=""):
        self._setup_data()
        self._setup_variables()
        self._setup_objective()
        self._setup_constraints()
        # self._model.Params.LogFile = output_log_file
        self._model.optimize(
            lazy_constraints(self._allocation_var,
                             self._setup_contiguous_hours_constraint)
        )
        if self._model.Status not in (GRB.OPTIMAL, GRB.TIME_LIMIT):
            return self._model.Status
        self._populate_allocation()
        return GRB.OPTIMAL

    def _populate_allocation(self):
        for tutor_id in self._tutors:
            for session_stream_id in self._session_streams:
                if self._allocation_var[tutor_id, session_stream_id].x > 0.99:
                    print(
                        f"Tutor {self._tutors[tutor_id]} works on {self._session_streams[session_stream_id]}")
                    self._results[session_stream_id].append(tutor_id)

    def get_results(self):
        return self._results
