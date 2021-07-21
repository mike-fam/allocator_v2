import json
import pprint

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from allocator.allocation import Allocator
from django.views.decorators.http import require_POST
import multiprocessing
import redis


@csrf_exempt
@require_POST
def request_allocation(request):
    def run_allocation(allocator: Allocator, token: str):
        allocator.run_allocation()
        redis_client = redis.Redis()
        redis_client.publish(token, "done")
    data = json.loads(request.body)
    pprint.pprint(data)
    allocator: Allocator = Allocator.from_input(data["data"])
    new_process = multiprocessing.Process(target=run_allocation, args=(allocator, data["token"]))
    new_process.start()
    return JsonResponse({"status": "success"})

@csrf_exempt
def index(request):
    return JsonResponse({"status": "success"})