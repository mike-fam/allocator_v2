import json
import pprint

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from allocator.allocation import Allocator
from django.views.decorators.http import require_POST, require_GET
import multiprocessing

from .models import Result
from .type_hints import RequestStatus, Input


def run_allocation(allocator: Allocator, token: str):
    result = allocator.run_allocation()
    result_obj = Result(key=token, value=json.dumps(result))
    result_obj.save()


@csrf_exempt
@require_POST
def request_allocation(request):
    data: Input = json.loads(request.body)
    allocator: Allocator = Allocator.from_input(data["data"], data["timeout"])
    new_process = multiprocessing.Process(target=run_allocation,
                                          args=(allocator, data["token"]))
    new_process.start()
    return JsonResponse({"status": RequestStatus.REQUESTED, "allocation": {}})


@csrf_exempt
@require_GET
def get_allocation(request, token):
    try:
        result = Result.objects.get(key=token)
        return JsonResponse({
            "status": RequestStatus.GENERATED,
            "allocation": json.loads(result.value)
        })
    except Result.DoesNotExist:
        return JsonResponse({
            "status": RequestStatus.NOT_READY,
            "allocation": {}
        })
