import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from allocator.allocation import Allocator
from django.views.decorators.http import require_http_methods
import redis


@csrf_exempt
@require_http_methods(["GET", "POST"])
def index(request):
    def run_allocation(allocator: Allocator, token: str):
        allocator.run_allocation()
        redis_client = redis.Redis()
        redis_client.publish(token, "done")

    if request.method == "POST":
        data = json.loads(request.body)["data"]
        allocator: Allocator = Allocator.from_input(data)
        result = allocator.run_allocation()

    else:
        pass
    return JsonResponse(result)
