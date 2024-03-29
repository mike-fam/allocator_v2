# Generated by Django 3.2.4 on 2021-11-21 02:59

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AllocationState",
            fields=[
                (
                    "timetable_id",
                    models.UUIDField(primary_key=True, serialize=False),
                ),
                ("data_hash", models.TextField()),
                ("request_time", models.DateTimeField()),
                ("result", models.JSONField(null=True)),
            ],
        ),
    ]
