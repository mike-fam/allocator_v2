import json
import time
import argparse
from datetime import datetime
from typing import Optional

from .type_hints import InputData
from .schema import Staff, SessionStream, Week
from .solver import Solver

from gurobipy.gurobipy import GRB

INFEASIBLE_MESSAGE = "Model infeasible.\n" \
                     "This is likely because there is no allocation that can " \
                     "satisfy the current availability, preference and session settings.\n" \
                     "The best way to fix this is to either ask staff members " \
                     "to loosen their preferences, \n" \
                     "Or you can change the 'default_preference_threshold' and " \
                     "'default_new_threshold' attributes."

STATUSES = {
    GRB.OPTIMAL: ("Optimal solution found", "success",
                  "Allocation successfully generated at {time}."),
    GRB.INFEASIBLE: ("Infeasible model", "failed", INFEASIBLE_MESSAGE),
    GRB.TIME_LIMIT: ("Time limit reached", "success",
                     "Allocation runs too long and was stopped")
}


class Allocator:
    def __init__(self):
        self._staff = []
        self._session_streams = []
        self._weeks = []
        self._new_threshold: Optional[float] = None
        self._allocation = {}
        self._timeout = 3600

    @classmethod
    def from_input(cls, json_input: InputData, timeout: int):
        instance = cls()
        instance._weeks = [Week.from_input(week_input)
                           for week_input in json_input["weeks"]]
        instance._staff = [Staff.from_input(staff_input)
                           for staff_input in json_input["staff"]]
        instance._session_streams = [SessionStream.from_input(stream_input)
                                     for stream_input in
                                     json_input["session_streams"]]
        instance._timeout = timeout
        return instance

    def run_allocation(self):
        start_time = time.time()
        solver = Solver(self._staff,
                        self._session_streams,
                        self._weeks)
        status = solver.solve()
        response_status, type_, message = STATUSES[status]
        allocations = {}
        if status == GRB.OPTIMAL:
            allocations = solver.get_results()
            message = message.format(time=datetime.now().strftime("%I:%M %p on %d %b %Y"))
        # Write to file
        return {
            "status": response_status,
            "type": type_,
            "detail": message,
            "allocations": allocations,
            "runtime": round(time.time() - start_time, 2)
        }


def setup_parser():
    parser = argparse.ArgumentParser(prog="allocator",
                                     description="Generate tutor allocations")
    parser.add_argument('json_input', type=str, help="JSON file containing model input")

    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()

    allocator = Allocator.from_input(json.loads(args.json_input))
    allocator.run_allocation()


if __name__ == '__main__':
    main()
