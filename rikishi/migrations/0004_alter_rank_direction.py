# Generated by Django 5.0.3 on 2024-11-12 22:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rikishi", "0003_alter_rikishi_api_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rank",
            name="direction",
            field=models.CharField(
                blank=True,
                choices=[("East", "East"), ("West", "West")],
                editable=False,
                max_length=4,
                null=True,
            ),
        ),
    ]
