from django.db import models


class AllocationState(models.Model):
    timetable_id = models.UUIDField(primary_key=True)
    data_hash = models.BinaryField()
    pid = models.IntegerField()
    request_time = models.DateTimeField()
    runtime = models.IntegerField(null=True)
    result = models.JSONField(null=True)
    status = models.TextField(default="Requested")
    type = models.TextField(null=True)
    message = models.TextField(null=True)
