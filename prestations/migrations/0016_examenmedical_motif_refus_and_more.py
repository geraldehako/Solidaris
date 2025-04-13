# Generated by Django 4.1.7 on 2025-02-10 18:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("prestations", "0015_medicamentprescris_medicament_substitue"),
    ]

    operations = [
        migrations.AddField(
            model_name="examenmedical",
            name="motif_refus",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="hospitalisation",
            name="motif_refus",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="examenmedical",
            name="statut",
            field=models.CharField(
                choices=[
                    ("en_attente", "En attente"),
                    ("validee", "Validée"),
                    ("refusee", "Refusée"),
                ],
                default="en_attente",
                max_length=20,
            ),
        ),
    ]
