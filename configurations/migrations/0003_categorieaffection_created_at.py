# Generated by Django 4.2.19 on 2025-03-21 19:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "configurations",
            "0002_alter_ordonnance_options_codeaffection_updated_at_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="categorieaffection",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, help_text="Date de création", null=True
            ),
        ),
    ]
