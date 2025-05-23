# Generated by Django 4.1.7 on 2024-12-20 22:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CentreSante",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=100, unique=True)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("hopital", "Hôpital"),
                            ("clinique", "Clinique"),
                            ("pharmacie", "Pharmacie"),
                            ("laboratoire", "Laboratoire"),
                            ("lunetterie", "Lunetterie"),
                        ],
                        max_length=20,
                    ),
                ),
                ("adresse", models.CharField(max_length=255)),
                ("telephone", models.CharField(max_length=15)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Groupe",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="CentreSantePrestation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tarif_personnalise",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Tarif spécifique pour cette prestation dans ce centre.",
                        max_digits=10,
                        null=True,
                    ),
                ),
                (
                    "disponible",
                    models.BooleanField(
                        default=True,
                        help_text="Indique si la prestation est disponible dans ce centre.",
                    ),
                ),
                (
                    "centre_sante",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prestations",
                        to="centres.centresante",
                    ),
                ),
            ],
            options={
                "verbose_name": "Prestation Centre Santé",
                "verbose_name_plural": "Prestations Centres Santé",
            },
        ),
    ]
