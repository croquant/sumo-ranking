# Generated by Django 5.0.3 on 2024-04-01 22:09

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("banzuke", "0002_alter_basho_end_date_alter_basho_month_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="basho",
            options={"verbose_name_plural": "Basho"},
        ),
        migrations.AlterModelOptions(
            name="torikumi",
            options={"verbose_name_plural": "Torikumi"},
        ),
    ]
