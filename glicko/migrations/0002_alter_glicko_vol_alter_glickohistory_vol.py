# Generated by Django 5.0.3 on 2024-05-25 08:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("glicko", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="glicko",
            name="vol",
            field=models.FloatField(default=0.06, editable=False),
        ),
        migrations.AlterField(
            model_name="glickohistory",
            name="vol",
            field=models.FloatField(default=0.06, editable=False),
        ),
    ]
