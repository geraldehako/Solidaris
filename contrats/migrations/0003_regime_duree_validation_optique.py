# Generated by Django 4.1.7 on 2025-02-13 19:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contrats", "0002_regime_duree_validation_consultation"),
    ]

    operations = [
        migrations.AddField(
            model_name="regime",
            name="duree_validation_optique",
            field=models.PositiveIntegerField(
                default=730,
                help_text="Durée de validité en jours pour une prise en charge en optique",
            ),
        ),
    ]
