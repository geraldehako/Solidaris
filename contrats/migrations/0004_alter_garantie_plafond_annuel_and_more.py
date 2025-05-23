# Generated by Django 4.1.7 on 2025-02-22 18:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contrats", "0003_regime_duree_validation_optique"),
    ]

    operations = [
        migrations.AlterField(
            model_name="garantie",
            name="plafond_annuel",
            field=models.IntegerField(
                blank=True,
                help_text="Plafond annuel en FCFA (ex: 100000.00 FCFA)",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="regime",
            name="plafond_annuel_couverture",
            field=models.IntegerField(
                blank=True,
                help_text="Plafond annuel de couverture en FCFA (laisser vide pour illimité)",
                null=True,
            ),
        ),
    ]
