import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from allocator.allocation import Allocator
from allocator.types import InputData, IsoDay, SessionType


@csrf_exempt
@require_POST
def index(request):
    data = json.loads(request.body)["data"]
    allocator: Allocator = Allocator.from_input(data)
    return JsonResponse(allocator.run_allocation())
