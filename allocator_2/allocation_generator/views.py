import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import multiprocessing
import django
django.setup()

from .allocation import Allocator
from .models import Result
from .type_hints import RequestStatus, Input


def run_allocation(allocator: Allocator, token: str):
    result = allocator.run_allocation()
    result_obj = Result.objects.get()
    result_obj.value = json.dumps(result)
    result_obj.save()


@csrf_exempt
@require_POST
def request_allocation(request):
    data: Input = json.loads(request.body)
    allocator: Allocator = Allocator.from_input(data["data"], data["timeout"])
    new_process = multiprocessing.Process(target=run_allocation,
                                          args=(allocator, data["token"]))
    new_process.start()
    result_obj = Result(key=data["token"], value=None)
    result_obj.save()
    return JsonResponse({"status": RequestStatus.REQUESTED, "allocation": {}})


@csrf_exempt
@require_GET
def get_allocation(request, token):
    try:
        result = Result.objects.get(key=token)
        if result.value is None:
            return JsonResponse({
                "status": RequestStatus.NOT_READY,
                "allocations": {}
            })
        else:
            return JsonResponse({
                "status": RequestStatus.GENERATED,
                "allocations": json.loads(result.value)["allocations"]
            })
    except Result.DoesNotExist:
        return JsonResponse({
            "status": RequestStatus.NOT_EXIST,
            "allocations": {}
        })
