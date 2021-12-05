import json
import time
import argparse
import traceback
from django.utils import timezone

from allocator.constants import (
    FAILURE_TITLE,
    FAILURE_MESSAGE,
    GENERATED_MESSAGE,
    GENERATED_TITLE,
)
from .type_hints import AllocationStatus, AllocationOutput
from .schema import InputData
from .solver import Solver

from gurobipy.gurobipy import GRB


class Allocator:
    def __init__(self, input_data: InputData):
        self._input_data = input_data

    def run_allocation(self) -> AllocationOutput:
        start_time = time.time()
        solver = Solver(
            self._input_data.staff,
            self._input_data.session_streams,
            self._input_data.weeks,
            timeout=self._input_data.timeout,
        )
        grb_status = solver.solve()
        runtime = int(time.time() - start_time)
        allocations = {}

        if grb_status == GRB.OPTIMAL or grb_status == GRB.TIME_LIMIT:
            title = GENERATED_TITLE
            allocations = solver.get_results()
            message = GENERATED_MESSAGE.format(
                runtime=runtime
            )
            status = AllocationStatus.GENERATED
        elif grb_status == GRB.INTERRUPTED:
            raise KeyboardInterrupt("Allocation process was interrupted")
        else:
            title = FAILURE_TITLE
            message = FAILURE_MESSAGE
            status = AllocationStatus.ERROR
        # Write to file
        return AllocationOutput(
            title,
            status,
            message,
            runtime,
            result=allocations,
        )


def _run_allocation(allocator: Allocator, timetable_id: str):
    import django

    django.setup()
    from .models import AllocationState

    while True:
        # Wait until allocation state is saved
        try:
            allocation_state = AllocationState.objects.get(
                timetable_id=timetable_id
            )
            break
        except AllocationState.DoesNotExist:
            continue

    try:
        result = allocator.run_allocation()
        allocation_state.result = result.result
        allocation_state.runtime = result.runtime
        allocation_state.title = result.title
        allocation_state.type = result.type
        allocation_state.message = result.message
    except:
        allocation_state.type = AllocationStatus.ERROR
        allocation_state.title = "An Error Occurred"
        allocation_state.message = traceback.format_exc(0)
    allocation_state.save()


def setup_parser():
    parser = argparse.ArgumentParser(
        prog="allocator", description="Generate tutor allocations"
    )
    parser.add_argument(
        "json_input", type=str, help="JSON file containing model input"
    )

    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()

    allocator = Allocator(InputData(**json.loads(args.json_input)))
    allocator.run_allocation()


if __name__ == "__main__":
    main()
