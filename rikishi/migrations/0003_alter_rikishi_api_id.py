# Generated by Django 5.0.3 on 2024-11-04 12:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rikishi", "0002_alter_division_name_alter_rank_title"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rikishi",
            name="api_id",
            field=models.PositiveSmallIntegerField(
                db_index=True, editable=False, unique=True
            ),
        ),
    ]
