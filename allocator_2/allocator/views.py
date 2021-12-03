import hashlib
import json
import multiprocessing as mp
from typing import Optional

import psutil

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone

from .constants import (
    REQUESTED_MESSAGE,
    REQUESTED_TITLE,
    NOT_READY_TITLE,
    NOT_READY_MESSAGE,
)
from .type_hints import AllocationStatus
from .allocation import Allocator, _run_allocation
from .schema import InputData
from .models import AllocationState


def _replace_existing_allocation(
    allocation_state: AllocationState,
    allocator: Allocator,
    timetable_id: str,
    new_timeout: Optional[int] = None,
):
    try:
        proc = psutil.Process(pid=allocation_state.pid)
        proc.terminate()
    except psutil.NoSuchProcess:
        pass
    new_process = mp.Process(
        target=_run_allocation, args=(allocator, timetable_id)
    )
    new_process.start()
    allocation_state.pid = new_process.pid
    allocation_state.result = None
    allocation_state.type = AllocationStatus.REQUESTED
    allocation_state.message = REQUESTED_MESSAGE.format(
        eta=allocation_state.timeout
    )
    allocation_state.title = "Allocation Successfully Requested"
    allocation_state.request_time = timezone.now()
    if new_timeout is not None:
        allocation_state.timeout = new_timeout
    allocation_state.save()


@csrf_exempt
@require_POST
def request_allocation(request):
    # TODO: later upgrade to realtime notification using Redis
    json_data = json.loads(request.body)["data"]
    data_hash = hashlib.sha256(
        json.dumps(json_data, separators=(":", ",")).encode()
    ).digest()
    data = InputData(**json_data)
    allocator = Allocator(data)
    timetable_id = data.timetable_id
    try:
        allocation_state = AllocationState.objects.get(
            timetable_id=data.timetable_id
        )
        # Found object, request already made
        # Hash matches, no state change
        if data_hash == allocation_state.data_hash:
            if allocation_state.type in (
                AllocationStatus.REQUESTED,
                AllocationStatus.NOT_READY,
            ):
                # Result not found yet, allocation still running
                if allocation_state.type == AllocationStatus.REQUESTED:
                    allocation_state.type = AllocationStatus.NOT_READY
                    allocation_state.title = NOT_READY_TITLE
                    allocation_state.message = NOT_READY_MESSAGE
                    allocation_state.save()
                eta = int(
                    allocation_state.request_time.timestamp()
                    + allocation_state.timeout
                    - timezone.now().timestamp()
                )
                allocation_state.message = allocation_state.message.format(
                    eta=eta
                )
            elif allocation_state.type == AllocationStatus.ERROR:
                _replace_existing_allocation(
                    allocation_state, allocator, timetable_id
                )
        else:
            # Hash doesn't match, request remade with modified data
            _replace_existing_allocation(
                allocation_state, allocator, timetable_id, data.timeout
            )
    except AllocationState.DoesNotExist:
        # No object found, new request
        new_process = mp.Process(
            target=_run_allocation, args=(allocator, timetable_id)
        )
        new_process.start()
        allocation_state = AllocationState(
            timetable_id=timetable_id,
            data_hash=data_hash,
            pid=new_process.pid,
            request_time=timezone.now(),
            timeout=data.timeout,
            type=AllocationStatus.REQUESTED,
            title=REQUESTED_TITLE,
            message=REQUESTED_MESSAGE,
        )
        allocation_state.save()
        print(allocation_state.message)
        allocation_state.message = allocation_state.message.format(
            eta=data.timeout
        )
    return JsonResponse(
        {
            "type": allocation_state.type,
            "message": allocation_state.message,
            "title": allocation_state.title,
            "result": allocation_state.result,
        }
    )


@require_GET
def check_allocation(request, timetable_id):
    try:
        allocation_state = AllocationState.objects.get(
            timetable_id=timetable_id
        )
        # Request has been made
        if allocation_state.type in (
            AllocationStatus.REQUESTED,
            AllocationStatus.NOT_READY,
        ):
            # Result not found yet, allocation still running
            if allocation_state.type == AllocationStatus.REQUESTED:
                allocation_state.type = AllocationStatus.NOT_READY
                allocation_state.title = NOT_READY_TITLE
                allocation_state.message = NOT_READY_MESSAGE
                allocation_state.save()
            eta = int(
                allocation_state.request_time.timestamp()
                + allocation_state.timeout
                - timezone.now().timestamp()
            )
            allocation_state.message = allocation_state.message.format(eta=eta)
        return JsonResponse(
            {
                "type": allocation_state.type,
                "message": allocation_state.message,
                "title": allocation_state.title,
                "result": allocation_state.result,
            }
        )
    except AllocationState.DoesNotExist:
        # Request has not been made
        return JsonResponse(
            {
                "type": AllocationStatus.NOT_EXIST,
                "message": "No request for an allocation of this timetable "
                "has been made",
                "title": "Allocation not found",
            }
        )
