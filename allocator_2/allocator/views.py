import hashlib
import json
import multiprocessing as mp
import os
import pprint
import sys

import psutil

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
import django

django.setup()
from .allocation import Allocator
from .schema import InputData
from .models import AllocationState


REQUESTED_MESSAGE = "Allocation Successfully Requested"


def _run_allocation(allocator: Allocator, timetable_id: str):
    result = allocator.run_allocation()
    pprint.pprint(result)
    allocation_state = AllocationState.objects.get(timetable_id=timetable_id)
    allocation_state.result = result["allocations"]
    allocation_state.runtime = result["runtime"]
    allocation_state.status = result["status"]
    allocation_state.type = result["type"]
    allocation_state.message = result["message"]
    allocation_state.save()


@csrf_exempt
@require_POST
def request_allocation(request):
    # input_data: InputData = {
    #     "weeks": [{
    #         "id": 1,
    #         "name": "week 1"
    #     },
    #         {
    #             "id": 2,
    #             "name": "week 2"
    #         },
    #
    #         {
    #             "id": 3,
    #             "name": "week 3"
    #         },
    #
    #         {
    #             "id": 3,
    #             "name": "week 3"
    #         },
    #
    #         {
    #             "id": 4,
    #             "name": "week 4"
    #         },
    #
    #         {
    #             "id": 5,
    #             "name": "week 5"
    #         },
    #
    #         {
    #             "id": 6,
    #             "name": "week 6"
    #         },
    #
    #         {
    #             "id": 7,
    #             "name": "week 7"
    #         },
    #
    #     ],
    #     "session_streams": [
    #         {
    #             "id": 1,
    #             "name": "P01",
    #             "start_time": 8,
    #             "end_time": 10,
    #             "type": SessionType.PRACTICAL,
    #             "number_of_tutors": 2,
    #             "day": IsoDay.MON,
    #             "weeks": [1, 2, 3, 4, 5, 6, 7]
    #         },
    #         {
    #             "id": 2,
    #             "name": "T01",
    #             "start_time": 9,
    #             "end_time": 10,
    #             "type": SessionType.TUTORIAL,
    #             "number_of_tutors": 1,
    #             "day": IsoDay.TUE,
    #             "weeks": [1, 2, 3, 4, 5, 6, 7]
    #         }
    #     ],
    #     "staff": [
    #         {
    #             "id": 1,
    #             "name": "Mike",
    #             "new": False,
    #             "type_preference": None,
    #             "max_contiguous_hours": 20,
    #             "max_weekly_hours": 100,
    #             "availabilities": {
    #                 IsoDay.MON: [
    #                     {
    #                         "start_time": 8,
    #                         "end_time": 15
    #                     }
    #                 ],
    #                 IsoDay.TUE: [
    #                     {
    #                         "start_time": 7,
    #                         "end_time": 15
    #                     }
    #                 ]
    #             }
    #         },
    #         {
    #             "id": 2,
    #             "name": "Josh",
    #             "new": False,
    #             "type_preference": None,
    #             "max_contiguous_hours": 20,
    #             "max_weekly_hours": 100,
    #             "availabilities": {
    #                 IsoDay.MON: [
    #                     {
    #                         "start_time": 8,
    #                         "end_time": 15
    #                     }
    #                 ],
    #                 IsoDay.TUE: [
    #                     {
    #                         "start_time": 9,
    #                         "end_time": 10
    #                     }
    #                 ]
    #             }
    #         }
    #     ],
    #     "new_threshold": 0.5,
    # }
    # allocator: Allocator = Allocator.from_input(input_data)
    # TODO when requesting new allocation
    #  if id already requested
    #   if hash matches
    #       if result already exists
    #           return json with allocation
    #       else
    #           reject json with "already requested and timelapse"
    #   if hash doesn't match
    #       kill existing process and
    #       run a new allocation
    #       return json with "requested" status
    #  else: return json with "requested" status
    # TODO: later upgrade to realtime notification using Redis
    json_data = json.loads(request.body)["data"]
    data_hash = hashlib.sha256(
        json.dumps(json_data, separators=(":", ",")).encode()
    ).digest()
    data = InputData(**json_data)
    allocator: Allocator = Allocator.from_input(data)
    timetable_id = data.timetable_id
    try:
        allocation_state = AllocationState.objects.get(
            timetable_id=data.timetable_id
        )
        if data_hash == allocation_state.data_hash:
            if allocation_state.result is not None:
                return JsonResponse(
                    {
                        "type": "GENERATED",
                        "message": "Allocation successfully generated",
                        "title": "Allocation generated",
                        "runtime": allocation_state.runtime,
                    }
                )
            return JsonResponse(
                {
                    "type": "NOT_READY",
                    "message": "Allocation not ready",
                    "title": "Allocation not ready",
                }
            )
        # hash doesn't match
        proc = psutil.Process(pid=allocation_state.pid)
        proc.terminate()
        new_process = mp.Process(
            target=_run_allocation, args=(allocator, timetable_id)
        )
        new_process.start()
        allocation_state.pid = new_process.pid
        allocation_state.save()
        return JsonResponse(
            {
                "type": "REQUESTED",
                "message": REQUESTED_MESSAGE,
                "title": "Hi",
                "runtime": 0
                # TODO
            }
        )
    except AllocationState.DoesNotExist:
        new_process = mp.Process(
            target=_run_allocation, args=(allocator, timetable_id)
        )
        new_process.start()
        allocation_state = AllocationState(
            timetable_id=timetable_id,
            data_hash=data_hash,
            pid=new_process.pid,
            request_time=timezone.now(),
        )
        allocation_state.save()
        return JsonResponse(
            {
                "type": "REQUESTED",
                "message": REQUESTED_MESSAGE,
                "title": "Hi",
                "runtime": 0
                # TODO
            }
        )
        # return JsonResponse(allocator.run_allocation())
        pass
