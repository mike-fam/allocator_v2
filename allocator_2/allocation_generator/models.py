import uuid
from django.db import models


class Result(models.Model):
    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.TextField(null=True)
