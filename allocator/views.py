import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from allocator.allocation import Allocator
from allocator.types import InputData, IsoDay, SessionType


@csrf_exempt
@require_POST
def index(request):
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
    allocator: Allocator = Allocator.from_input(json.loads(request.body)["data"])
    return JsonResponse(allocator.run_allocation())
