# Generated by Django 3.2.4 on 2021-11-21 03:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("allocator", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="allocationstate",
            name="data_hash",
            field=models.BinaryField(),
        ),
    ]
