from django.db import models


class AllocationState(models.Model):
    timetable_id = models.UUIDField(primary_key=True)
    data_hash = models.BinaryField()
    pid = models.IntegerField()
    request_time = models.DateTimeField()
    timeout = models.IntegerField()
    runtime = models.IntegerField(null=True)
    result = models.JSONField(null=True)
    title = models.TextField(default="Allocation Requested")
    type = models.TextField()
    message = models.TextField(null=True)
